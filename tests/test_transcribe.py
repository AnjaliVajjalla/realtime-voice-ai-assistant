import wave
import io
import numpy as np
from src.transcribe import audio_to_wav_bytes


def test_wav_bytes_are_valid_wav_format():
    audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    wav_bytes = audio_to_wav_bytes(audio, sample_rate=16000)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2  # 16-bit
        assert wav_file.getframerate() == 16000


def test_wav_bytes_match_input_length():
    audio = np.zeros(8000, dtype=np.float32)  # 0.5 seconds at 16kHz
    wav_bytes = audio_to_wav_bytes(audio, sample_rate=16000)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnframes() == 8000


def test_full_scale_audio_does_not_overflow():
    # audio values right at the edges (-1.0 and 1.0) should convert cleanly,
    # not wrap around into garbage due to integer overflow
    audio = np.array([1.0, -1.0, 0.0], dtype=np.float32)
    wav_bytes = audio_to_wav_bytes(audio, sample_rate=16000)

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frames = wav_file.readframes(3)
        samples = np.frombuffer(frames, dtype=np.int16)
        assert samples[0] > 0   # 1.0 became a large positive number
        assert samples[1] < 0   # -1.0 became a large negative number
        assert samples[2] == 0  # 0.0 stayed 0
