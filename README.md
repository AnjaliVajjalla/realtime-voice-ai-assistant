# Real-Time Voice AI Assistant

An assistant that lets you have a spoken, hands-free conversation, ask a
question, hear an answer, ask a follow-up, with every stage of the
pipeline (speech-in, model, speech-out) visible and measurable, and one
small tool (real-time weather) it can actually use.

## Why this project exists

Built for hands-on practice with the full realtime voice pipeline: speech
recognition, LLM reasoning, tool/function calling, streaming responses,
text-to-speech, latency measurement, evaluation, and resilient AI
application design. See `PROJECT_BRIEF.md` for the original scope and
boundaries.

## Architecture

```
mic audio ──► transcribe (Whisper STT) ──► transcript (shown on screen)
    ▲                                             │
    │                                             ▼
    │                              LLM call (Claude, streamed)
    │                                             │
    │                        ┌────────────────────┴──────────────────┐
    │                        │                                       │
    │                 no tool needed                         needs a tool
    │                        │                                       │
    │                        │                         run get_weather(),
    │                        │                         send result back,
    │                        │                         get final answer
    │                        │                                       │
    │                        └────────────────────┬──────────────────┘
    │                                              ▼
    │                                text response (shown on screen)
    │                                              │
    │                                              ▼
    │                                   speak (TTS) ──► audio playback
    │                                              │
    └──────────────── listen for next question ◄───┘
     (until a stop phrase is heard, or Ctrl+C)
```

Each stage is its own module in `src/`: `capture.py` (mic, voice-activity
detection), `transcribe.py` (Whisper), `respond.py` (Claude, streaming +
tool calling), `tools.py` (the weather tool), `speak.py` (TTS + playback),
`trace.py` (per-stage latency), `pipeline.py` (orchestrates all of it,
states + fallbacks + the conversation loop).

States exposed at every stage: `[recording]` → `[processing]` →
`[success]` / `[failure]` / `[fallback]`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your API keys:
```
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

## Running it

```bash
python3 -m src.pipeline
```

Just start talking after each "Recording..." prompt, it stops
automatically when you pause (voice activity detection, not a fixed
timer). Ask a follow-up, ask about the weather somewhere, ask anything
else, it's a real back-and-forth conversation, not one question and exit.
Say "goodbye" (or "stop listening," "exit," "quit") to end it naturally,
or press Ctrl+C to stop immediately.

## Testing vs. evaluation

- `pytest tests/` — 7 unit tests, free, no real API calls (API-calling
  functions are tested with mocks). Checks the *code* behaves correctly:
  does WAV conversion produce valid audio, does latency tracking record
  correctly even when a stage fails, does the pipeline's fallback logic
  actually trigger when a stage errors out.
- `pytest evals/` — 4 real-API evals against meaningful scenarios. Checks
  the *system* behaves well: does a weather question correctly trigger
  the tool, does a nonexistent location get handled gracefully instead of
  hallucinated, does a non-weather question correctly skip the tool, is a
  broad/open-ended question still kept short enough to be spoken
  naturally. Costs a small amount to run (real Claude + tool calls).

## Evaluation results

All 4 evals pass. One real finding along the way: the first run of
`test_reply_is_short_and_voice_appropriate` failed, "Tell me about the
history of the Roman Empire" got a 93-word answer, too long to be spoken
naturally, even though the system prompt already asked for short replies.
The prompt held up fine for narrow questions but not broad, open-ended
ones. Fixed by explicitly telling the model to stay short "even for broad
or open-ended questions" and to pick the single most important point
rather than being comprehensive. Re-ran the eval: same question, 49 words
instead of 93, still a real, informative answer. Confirms evals catch
quality drift that unit tests can't, the code never crashed, it just
wasn't behaving the way the system was supposed to.

## Latency

Measured live, stage-by-stage, across multiple real runs (not a
controlled benchmark, just honest numbers from actual use):

| stage | typical range | notes |
|---|---|---|
| record | 4-6s | now voice-activity-detected: matches how long you actually talk, not a fixed timer |
| transcribe | 0.75-2.8s | Whisper API |
| respond (no tool) | ~1-2s | one Claude API call |
| respond (tool call) | ~3.2-4.8s | two Claude API calls (ask → tool requested → run it → final answer), roughly 2-3x slower than a direct answer |
| speak | 4-13s | OpenAI TTS + playback; scales with reply length |
| **total per turn** | **~14-22s** | end to end, one full question-to-spoken-answer cycle |

The clearest tradeoff: tool calling roughly doubles `respond` latency
(two API round trips instead of one), a real cost worth knowing when
deciding whether a feature needs a tool or can be answered directly.

## Known limitations

- Tested only on one machine/microphone; `SILENCE_THRESHOLD` in
  `src/capture.py` (the voice-activity-detection cutoff) is a starting
  guess and may need tuning for different mics or noisy rooms.
- Streaming applies to the *text* response only (visible incrementally as
  Claude generates it); audio playback still waits for the full reply
  before speaking. True sentence-by-sentence audio streaming (speak the
  first sentence while later ones are still generating) would need
  sentence-boundary detection and an audio queue, a natural next step,
  not yet built.
- One tool (weather, via the free Open-Meteo API). No broader multi-tool
  agent, by design, per the project brief's scope.
- Terminal-only interface right now; a visual interface is a planned next
  sprint.
- No formal evaluation yet for noisy/accented speech, interruptions, or
  numbers/proper nouns in transcription, the eval suite currently covers
  response behavior (tool use, scope, length), not transcription
  robustness.
- `evals/` costs real money to run (small, but non-zero), so it's run
  deliberately, not on every save, unlike the free `tests/` suite.

## Tech stack

Python, OpenAI Whisper API (STT), Anthropic Claude API (LLM, streaming +
tool calling), OpenAI TTS API (speech), `sounddevice` + `soundfile`
(mic capture with voice activity detection, audio playback), `requests`
(the weather tool, via the free Open-Meteo API), `pytest` (unit tests +
evals).
