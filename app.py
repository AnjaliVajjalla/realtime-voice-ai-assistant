import json
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify
from flask_sock import Sock
from dotenv import load_dotenv

load_dotenv()  # before importing src modules, same reason as pipeline.py

from src.pipeline import run_turn
from src.naming import generate_chat_name

app = Flask(__name__)
sock = Sock(app)

CHATS_DIR = Path("data/chats")
CHATS_DIR.mkdir(parents=True, exist_ok=True)

# This app is single-user and single-session (just you, one browser tab),
# so plain module-level variables are enough to hold state between
# requests. A real multi-user product would need per-user sessions
# instead, not needed for this project's scope.
conversation_history = []

# Only one turn (record -> transcribe -> respond -> speak) can run at a
# time, there's one microphone. This lock enforces that: a second
# WebSocket connection trying to start a turn while one is already
# running gets rejected immediately instead of the two colliding.
turn_lock = threading.Lock()


def _new_chat_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


# The chat currently being talked to. "id" is a timestamp (used as the
# filename, always unique and sortable). "name" is the fun random label
# (e.g. "Silly Raccoon") shown to the user, purely cosmetic. "turns" is
# the plain display data (transcript/reply/timings) already shown on
# screen, no Claude SDK objects, so it's safe to write straight to JSON.
current_chat = {
    "id": _new_chat_id(),
    "name": generate_chat_name(),
    "turns": [],
}


def _save_current_chat():
    """Write the current chat to disk, but only if it actually has any
    turns in it (no point saving an empty chat someone never used)."""
    if not current_chat["turns"]:
        return
    path = CHATS_DIR / f"{current_chat['id']}.json"
    with open(path, "w") as f:
        json.dump(current_chat, f, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@sock.route("/ws/turn")
def ws_turn(ws):
    """One WebSocket connection = one full turn. The browser opens this
    connection when the user clicks "Start turn"; the server pushes each
    progress event (recording, transcribing, thinking, speaking) over it
    the instant that stage happens, instead of the browser polling for
    status. The browser can send {"type": "stop"} over this same
    connection at any time to interrupt recording early."""
    if not turn_lock.acquire(blocking=False):
        ws.send(json.dumps({"type": "error", "error": "A turn is already in progress"}))
        return

    stop_event = threading.Event()

    def listen_for_stop():
        # Runs on its own thread so it can wait for an incoming message
        # (ws.receive() blocks) at the same time the main thread below is
        # busy running the turn and pushing outgoing events.
        while True:
            try:
                message = ws.receive()
            except Exception:
                break
            if message is None:  # connection closed
                break
            try:
                data = json.loads(message)
            except ValueError:
                continue
            if data.get("type") == "stop":
                stop_event.set()
                break

    listener = threading.Thread(target=listen_for_stop, daemon=True)
    listener.start()

    def on_event(event_type, **data):
        try:
            ws.send(json.dumps({"type": event_type, **data}))
        except Exception:
            pass  # browser may have already disconnected
        if event_type in ("respond_fallback", "speak_fallback", "record_failure", "transcribe_failure"):
            print(f"[{event_type}] {data.get('error')}")

    try:
        global conversation_history
        result = run_turn(
            on_event=on_event,
            history=conversation_history,
            stop_event=stop_event,
            assistant_name=current_chat["name"],
        )
        conversation_history = result["history"]

        # history holds raw Claude SDK objects (not JSON-serializable),
        # and only this server needs it, not the browser.
        response_data = {k: v for k, v in result.items() if k != "history"}

        if response_data.get("transcript"):
            current_chat["turns"].append({
                "transcript": response_data.get("transcript"),
                "reply": response_data.get("reply"),
                "timings": response_data.get("timings"),
            })
            _save_current_chat()

        ws.send(json.dumps({"type": "final_result", "result": response_data}))
    finally:
        turn_lock.release()


@app.route("/api/current_chat")
def api_current_chat():
    return jsonify({"id": current_chat["id"], "name": current_chat["name"]})


@app.route("/api/new_chat", methods=["POST"])
def api_new_chat():
    global conversation_history, current_chat
    _save_current_chat()
    conversation_history = []
    current_chat = {
        "id": _new_chat_id(),
        "name": generate_chat_name(),
        "turns": [],
    }
    return jsonify({"id": current_chat["id"], "name": current_chat["name"]})


@app.route("/api/chats")
def api_list_chats():
    chats = []
    for path in sorted(CHATS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        with open(path) as f:
            data = json.load(f)
        chats.append({
            "id": data["id"],
            "name": data["name"],
            "turn_count": len(data["turns"]),
        })
    return jsonify({"chats": chats})


@app.route("/api/chats/<chat_id>")
def api_get_chat(chat_id):
    path = CHATS_DIR / f"{chat_id}.json"
    if not path.exists():
        return jsonify({"error": "Chat not found"}), 404
    with open(path) as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/api/chats/<chat_id>", methods=["DELETE"])
def api_delete_chat(chat_id):
    path = CHATS_DIR / f"{chat_id}.json"
    if not path.exists():
        return jsonify({"error": "Chat not found"}), 404
    path.unlink()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5050, threaded=True)
