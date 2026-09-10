import io
import numpy as np
import soundfile as sf
import sounddevice as sd
from openai import OpenAI

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY from your .env, only when first needed
    return _client


def text_to_speech(text: str) -> bytes:
    """Send text to OpenAI's TTS API and return MP3 audio bytes."""
    response = _get_client().audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        timeout=20,
    )
    return response.content


def play_audio(mp3_bytes: bytes) -> None:
    """Decode MP3 bytes and play them through the default speakers."""
    audio_array, sample_rate = sf.read(io.BytesIO(mp3_bytes))
    sd.play(audio_array, sample_rate)
    sd.wait()  # blocks until playback finishes


def speak(text: str) -> None:
    """Convert text to speech and play it immediately."""
    mp3_bytes = text_to_speech(text)
    play_audio(mp3_bytes)
