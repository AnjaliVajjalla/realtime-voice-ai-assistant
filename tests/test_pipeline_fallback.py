from unittest.mock import patch
import numpy as np
from src.pipeline import run_pipeline


def test_respond_failure_falls_back_to_canned_reply(capsys):
    fake_audio = np.zeros(1000, dtype=np.float32)

    with patch("src.pipeline.record_audio", return_value=fake_audio), \
         patch("src.pipeline.transcribe", return_value="What's the weather?"), \
         patch("src.pipeline.get_response", side_effect=Exception("simulated API failure")), \
         patch("src.pipeline.speak"):
        run_pipeline()

    output = capsys.readouterr().out
    assert "[fallback]" in output
    assert "Sorry, I'm having trouble thinking" in output


def test_speak_failure_falls_back_to_printing_text(capsys):
    fake_audio = np.zeros(1000, dtype=np.float32)

    with patch("src.pipeline.record_audio", return_value=fake_audio), \
         patch("src.pipeline.transcribe", return_value="Hello"), \
         patch("src.pipeline.get_response", return_value=("Hi there!", [])), \
         patch("src.pipeline.speak", side_effect=Exception("simulated TTS failure")):
        run_pipeline()

    output = capsys.readouterr().out
    assert "[fallback]" in output
    assert "Hi there!" in output  # text still shown even though speech failed
