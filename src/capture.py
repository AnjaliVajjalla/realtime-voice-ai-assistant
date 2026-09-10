import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000  # 16kHz, standard for speech-to-text APIs
CHUNK_SECONDS = 0.1        # how often we check the volume
SILENCE_THRESHOLD = 0.02   # volume below this counts as "quiet"
SILENCE_DURATION = 1.2     # seconds of quiet after speech before we stop
MAX_DURATION = 30          # safety cap, in case something goes wrong


def record_audio(max_duration: float = MAX_DURATION, stop_event=None) -> np.ndarray:
    """Record from the default microphone until the user stops talking.

    Starts recording immediately. Stops on whichever comes first:
    SILENCE_DURATION seconds of quiet following speech, max_duration
    seconds no matter what (a safety cap), or stop_event being set
    (an optional threading.Event some caller can set from outside, e.g.
    a "Stop Recording" button). Pass no stop_event and behavior is
    unchanged, silence/timeout only.
    """
    chunk_samples = int(CHUNK_SECONDS * SAMPLE_RATE)
    chunks = []
    speech_started = False
    silent_chunks_in_a_row = 0
    silence_chunks_needed = int(SILENCE_DURATION / CHUNK_SECONDS)
    max_chunks = int(max_duration / CHUNK_SECONDS)

    print("Recording... speak now, it'll stop automatically when you pause.")
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    with stream:
        for _ in range(max_chunks):
            if stop_event is not None and stop_event.is_set():
                break

            chunk, _ = stream.read(chunk_samples)
            chunk = chunk.flatten()
            chunks.append(chunk)

            volume = np.sqrt(np.mean(chunk ** 2))  # RMS: a simple loudness measure

            if volume > SILENCE_THRESHOLD:
                speech_started = True
                silent_chunks_in_a_row = 0
            else:
                silent_chunks_in_a_row += 1

            if speech_started and silent_chunks_in_a_row >= silence_chunks_needed:
                break

    print("Done recording.")
    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate(chunks)
