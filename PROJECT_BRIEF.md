# Real-Time Voice AI Assistant — Project Brief

## Why
Practical experience with the full realtime voice pipeline: speech recognition, LLM reasoning, text-to-speech, streaming/WebSockets, tool calling, latency measurement, evaluation, and resilient AI application design. Supports entry-level AI analyst / AI solutions / AI operations job targets by showing a user need translated into a measurable, testable AI workflow.

## Product idea
Lets a user ask a focused question aloud and receive a relevant spoken response. The speech, model, and audio stages are all visible, so the system can be understood, evaluated, and improved.

## Core version (build first)
Capture microphone audio, transcribe it, send the transcript to an LLM, display the text response, convert the response to speech, and play the resulting audio. Exposes clear recording, processing, success, and failure states.

## Portfolio version (build after core works)
Adds streaming/realtime interaction, one small and controlled tool, stage-level and end-to-end latency measurement, timeouts, graceful fallbacks, structured evaluation, automated tests for non-audio logic, and a GitHub README with architecture and measured results.

## Out of scope
Phone calls, mobile apps, user accounts, persistent personal profiles, continuous background recording, RAG, autonomous transactions, and a broad multi-tool agent.

## Target user
Someone who wants a hands-free, conversational way to ask a focused information question and hear a brief response. This is a portfolio demonstration for controlled use cases, not a general-purpose personal assistant.

## Boundaries
Educational portfolio application, not an emergency, medical, legal, or financial service. No autonomous purchases, no sending messages, no other consequential external actions. Microphone use is visible and user-initiated. Credentials stay on the server. Sensitive audio/transcript data is not stored unless a later requirement explicitly justifies it.

## Sprint 0 decisions

**Tech choices (starting point, adjustable as sprints progress):**
- STT (speech-to-text): OpenAI Whisper API
- LLM: Anthropic Claude API (already used elsewhere in Anjali's projects)
- TTS (text-to-speech): OpenAI TTS API
- Mic capture / audio playback: `sounddevice` (Python)
- Streaming (portfolio version): WebSockets

**One controlled tool (portfolio version):** TBD — pick something small, safe, and easy to demo (e.g. a weather lookup or a simple calculator). Decide in the sprint that introduces tool calling, not before.

**Success criteria (core version):**
- A user can complete a reliable speech-to-response conversation (mic in, spoken answer out)
- Clear recording / processing / success / failure states are visible
- Text transcript and text response are both shown, not just spoken

**Success criteria (portfolio version):**
- The assistant can safely use one controlled tool
- Output begins incrementally through streaming or realtime communication
- Latency is measured by pipeline stage (STT / LLM / TTS) and end-to-end
- Failures recover or degrade gracefully (timeouts, fallbacks)
- GitHub repo explains architecture, evaluation method, results, limitations, and setup

## Status
- Sprint 0: done (this doc)
- Sprint 1+: not started
