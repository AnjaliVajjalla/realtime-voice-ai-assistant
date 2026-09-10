import io
import wave
import numpy as np
from openai import OpenAI

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY from your .env, only when first needed
    return _client


def audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """Convert a numpy float32 audio array into in-memory WAV file bytes."""
    # Whisper expects 16-bit integer samples, not float32, so we convert.
    int_samples = (audio * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 2 bytes = 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_samples.tobytes())
    return buffer.getvalue()


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """Send recorded audio to Whisper and return the transcribed text."""
    wav_bytes = audio_to_wav_bytes(audio, sample_rate)
    wav_bytes_file = io.BytesIO(wav_bytes)
    wav_bytes_file.name = "audio.wav"  # Whisper's API needs a filename hint

    response = _get_client().audio.transcriptions.create(
        model="whisper-1",
        file=wav_bytes_file,
    )
    return response.text
