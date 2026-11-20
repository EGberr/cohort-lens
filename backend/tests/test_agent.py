"""Exercises the Claude tool loop against a scripted fake client (no network)."""

from types import SimpleNamespace as NS

from app.agent import ClaudeAnalyst


class FakeStream:
    def __init__(self, events, final):
        self._events, self._final = events, final

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        async def gen():
            for e in self._events:
                yield e

        return gen()

    async def get_final_message(self):
        return self._final


class FakeClient:
    def __init__(self, turns):
        self.turns, self.calls = list(turns), []
        self.beta = NS(messages=NS(stream=self._stream))

    def _stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeStream(*self.turns.pop(0))


def usage():
    return NS(input_tokens=100, output_tokens=20, cache_read_input_tokens=0, cache_creation_input_tokens=0)


async def test_tool_loop_runs_tools_and_streams_answer(toolbox):
    tool_block = NS(
        type="tool_use", id="tu_1", name="query_survey", input={"metric": "penetration", "categories": ["skincare"]}
    )
    turn1 = (
        [NS(type="content_block_start", content_block=NS(type="tool_use", name="query_survey"))],
        NS(stop_reason="tool_use", content=[tool_block], usage=usage(), model="claude-opus-5-5"),
    )
    turn2 = (
        [NS(type="text", text="78% bought skincare [D1].")],
        NS(
            stop_reason="end_turn",
            content=[NS(type="text", text="78% bought skincare [D1].")],
            usage=usage(),
            model="claude-opus-5-5",
        ),
    )
    client = FakeClient([turn1, turn2])
    events = [
        e
        async for e in ClaudeAnalyst(toolbox, client=client).run([{"role": "user", "content": "Skincare penetration?"}])
    ]
    types = [e["type"] for e in events]
    assert "dataset" in types and "tool_call" in types and types[-1] == "done"
    assert events[-1]["usage"]["input_tokens"] == 200
    # Second request carries the assistant tool_use turn and the matching tool_result.
    second = client.calls[1]["messages"]
    assert second[-1]["content"][0]["tool_use_id"] == "tu_1"
    assert client.calls[0]["fallbacks"] == "default"
    assert client.calls[0]["thinking"] == {"type": "adaptive"}


async def test_invalid_tool_input_is_returned_as_error(toolbox):
    bad = NS(type="tool_use", id="tu_x", name="query_survey", input={"metric": "penetration", "categories": []})
    turn1 = ([], NS(stop_reason="tool_use", content=[bad], usage=usage(), model="m"))
    turn2 = ([NS(type="text", text="Sorry.")], NS(stop_reason="end_turn", content=[], usage=usage(), model="m"))
    client = FakeClient([turn1, turn2])
    events = [e async for e in ClaudeAnalyst(toolbox, client=client).run([{"role": "user", "content": "x"}])]
    call = next(e for e in events if e["type"] == "tool_call")
    assert call["is_error"] is True
    assert client.calls[1]["messages"][-1]["content"][0]["is_error"] is True
