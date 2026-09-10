from anthropic import Anthropic
from src.tools import get_weather

_client = None


def _build_system_prompt(assistant_name: str | None) -> str:
    """Builds the system prompt, optionally giving Claude a name to
    identify itself as (e.g. this chat's random generated name)."""
    identity = f"You are {assistant_name}, a voice assistant." if assistant_name else "You are a voice assistant."
    return (
        f"{identity} The user is speaking to you, and your reply "
        "will be read aloud by text-to-speech. Keep answers short and "
        "conversational: 1-2 sentences, ideally under 40 words, even for broad "
        "or open-ended questions. Pick the single most important point rather "
        "than trying to be comprehensive. Avoid lists, bullet points, or "
        "markdown formatting since none of that survives being spoken aloud."
    )


# The schema Claude sees: a description of what the tool does and what
# input it needs. Claude decides on its own when a question calls for it.
WEATHER_TOOL = {
    "name": "get_weather",
    "description": "Get the current weather for a specific location.",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and state/country, e.g. 'Edison, New Jersey'",
            }
        },
        "required": ["location"],
    },
}


def _get_client():
    global _client
    if _client is None:
        _client = Anthropic()  # reads ANTHROPIC_API_KEY from your .env, only when first needed
    return _client


def get_response(transcript: str, history: list | None = None, assistant_name: str | None = None) -> tuple[str, list]:
    """Send a transcribed question to Claude, streaming the text response
    as it's generated, using the weather tool if needed.

    `history` is the conversation so far (a list of message dicts). Pass
    None (or omit it) to start a fresh conversation. `assistant_name`
    (optional) lets Claude introduce itself with a specific name, e.g.
    this chat's randomly generated name. Returns (reply_text,
    updated_history) so the caller can hold onto the updated history and
    pass it into the next turn.
    """
    client = _get_client()
    system_prompt = _build_system_prompt(assistant_name)
    messages = list(history) if history else []
    messages.append({"role": "user", "content": transcript})

    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=system_prompt,
        tools=[WEATHER_TOOL],
        messages=messages,
        timeout=15,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)  # show each piece as it arrives
        response = stream.get_final_message()
    print()  # newline once streaming for this turn is done

    if response.stop_reason != "tool_use":
        # Claude answered directly, no tool needed
        messages.append({"role": "assistant", "content": response.content})
        return response.content[0].text, messages

    # Claude wants to call a tool, possibly more than once in the same
    # turn (e.g. asking for weather in three towns at once becomes three
    # separate tool_use blocks). Run all of them and send back a
    # tool_result for each, the API requires exactly one tool_result per
    # tool_use block, or the next call is rejected outright.
    tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
    tool_results = []
    for block in tool_use_blocks:
        result = get_weather(block.input["location"])
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": result,
        })

    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})

    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=system_prompt,
        tools=[WEATHER_TOOL],
        messages=messages,
        timeout=15,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        final_response = stream.get_final_message()
    print()

    messages.append({"role": "assistant", "content": final_response.content})
    return final_response.content[0].text, messages
