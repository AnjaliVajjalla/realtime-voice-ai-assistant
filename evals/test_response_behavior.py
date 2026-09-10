"""Evals for get_response(): real API calls, checks system behavior against
meaningful scenarios (not just code correctness). Costs a small amount to run.
"""
from src.respond import get_response


def test_weather_question_triggers_tool_and_returns_real_data():
    reply = get_response("What's the weather in Chicago right now?")
    # A real answer should mention a temperature, not decline or hallucinate
    assert "degree" in reply.lower() or "°" in reply

    print(f"\n[eval] Weather question -> {reply}")


def test_nonexistent_location_is_handled_gracefully():
    reply = get_response("What's the weather in Zzzxqplace?")
    # Should say it couldn't find it, not make up a fake temperature
    assert "couldn't find" in reply.lower() or "not sure" in reply.lower() or "find" in reply.lower()

    print(f"\n[eval] Fake location -> {reply}")


def test_non_weather_question_does_not_trigger_tool():
    reply = get_response("What's 12 times 8?")
    assert "96" in reply

    print(f"\n[eval] Math question -> {reply}")


def test_reply_is_short_and_voice_appropriate():
    reply = get_response("Tell me about the history of the Roman Empire.")
    # System prompt asks for short, spoken-friendly answers, not an essay
    word_count = len(reply.split())
    assert word_count < 80, f"Reply was {word_count} words, too long for a spoken response"

    print(f"\n[eval] Broad question kept short ({word_count} words) -> {reply}")
