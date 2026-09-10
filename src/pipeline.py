import time

from dotenv import load_dotenv

load_dotenv()  # must run before importing modules that read env vars at import time

from src.capture import record_audio, MAX_DURATION
from src.transcribe import transcribe
from src.respond import get_response
from src.speak import speak
from src.trace import time_stage

STOP_PHRASES = ("goodbye", "stop listening", "that's all", "exit", "quit")


def run_turn(max_duration: float = MAX_DURATION, on_event=None, history: list | None = None, stop_event=None, assistant_name: str | None = None) -> dict:
    """Run one full voice interaction: record -> transcribe -> respond -> speak.

    `history` is the conversation so far (see src/respond.py), passed in
    from the caller and returned (possibly updated) in the result dict so
    the caller can carry it into the next turn. Pass None to start a
    fresh conversation.

    `stop_event` (an optional threading.Event) is passed straight through
    to record_audio(), letting some outside caller (e.g. a web request
    handling a "Stop Recording" click) end recording early.

    Calls on_event(event_type, **data) at each stage transition (used by
    the CLI to print progress, and by the web UI to report progress) and
    returns a structured result dict describing what happened. This is
    the shared core logic behind both run_pipeline() (CLI) and the web
    app's endpoints, so both display the same real behavior instead of
    duplicating it.
    """
    def emit(event_type, **data):
        if on_event:
            on_event(event_type, **data)

    timings = {}
    pipeline_start = time.perf_counter()
    result = {
        "stopped": False,
        "transcript": None,
        "reply": None,
        "error": None,
        "respond_fallback": False,
        "speak_fallback": False,
        "timings": {},
        "history": history or [],
    }

    emit("recording")
    try:
        with time_stage("record", timings):
            audio = record_audio(max_duration, stop_event=stop_event)
    except Exception as e:
        result["error"] = f"Could not record audio: {e}"
        emit("record_failure", error=str(e))
        return result

    emit("transcribing")
    try:
        with time_stage("transcribe", timings):
            transcript = transcribe(audio)
        result["transcript"] = transcript
        emit("transcript", text=transcript)
    except Exception as e:
        result["error"] = f"Could not transcribe audio: {e}"
        emit("transcribe_failure", error=str(e))
        return result

    if any(phrase in transcript.lower() for phrase in STOP_PHRASES):
        result["stopped"] = True
        emit("stopped")
        return result

    emit("thinking")
    try:
        with time_stage("respond", timings):
            reply, updated_history = get_response(transcript, history, assistant_name=assistant_name)
        result["history"] = updated_history
    except Exception as e:
        result["respond_fallback"] = True
        emit("respond_fallback", error=str(e))
        reply = "Sorry, I'm having trouble thinking right now. Please try again in a moment."
        # get_response never ran, so history is unchanged; result["history"]
        # already holds the pre-failure history set above.
    result["reply"] = reply
    emit("response", text=reply)

    emit("speaking")
    try:
        with time_stage("speak", timings):
            speak(reply)
    except Exception as e:
        result["speak_fallback"] = True
        emit("speak_fallback", error=str(e))

    timings["total"] = round(time.perf_counter() - pipeline_start, 3)
    result["timings"] = timings
    emit("done", timings=timings)
    return result


def run_pipeline(max_duration: float = MAX_DURATION, history: list | None = None) -> tuple[bool, list]:
    """CLI wrapper around run_turn(): prints progress to the terminal and
    returns (keep_going, updated_history)."""

    def on_event(event_type, **data):
        if event_type == "recording":
            print("[recording] Listening...")
        elif event_type == "record_failure":
            print(f"[failure] Could not record audio: {data['error']}")
        elif event_type == "transcribing":
            print("[processing] Transcribing...")
        elif event_type == "transcribe_failure":
            print(f"[failure] Could not transcribe audio: {data['error']}")
        elif event_type == "transcript":
            print(f"  You said: {data['text']}")
        elif event_type == "stopped":
            print("[success] Goodbye!")
        elif event_type == "thinking":
            print("[processing] Thinking...")
        elif event_type == "respond_fallback":
            print(f"  [fallback] Claude didn't respond in time ({data['error']}), using a fallback reply.")
        elif event_type == "response":
            print(f"  Claude says: {data['text']}")
        elif event_type == "speaking":
            print("[processing] Speaking response...")
        elif event_type == "speak_fallback":
            print(f"  [fallback] Couldn't speak the response ({data['error']}). Showing text only:")
        elif event_type == "done":
            print(f"[success] Done. Latency (seconds): {data['timings']}\n")

    result = run_turn(max_duration, on_event=on_event, history=history)

    if result["speak_fallback"]:
        print(f"  >>> {result['reply']}")

    if result["error"]:
        return True, result["history"]  # try again next turn rather than ending the conversation

    return not result["stopped"], result["history"]


def run_conversation(max_duration: float = MAX_DURATION) -> None:
    """Keep running voice interactions until the user says a stop phrase
    (or presses Ctrl+C to force-stop immediately)."""
    print("=" * 50)
    print("Voice Assistant")
    print("=" * 50)
    print("Just start talking after each 'Recording...' prompt.")
    print("Recording stops automatically when you pause.")
    print("Try asking about the weather, or ask anything else.")
    print("Say 'goodbye' anytime to stop, or press Ctrl+C.")
    print("=" * 50 + "\n")
    history = []
    try:
        while True:
            keep_going, history = run_pipeline(max_duration, history)
            if not keep_going:
                break
    except KeyboardInterrupt:
        print("\n[success] Stopped.")


if __name__ == "__main__":
    run_conversation()
