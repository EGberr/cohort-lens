"""The Claude agent loop (Messages API, manual tool loop, streamed to the UI as events).

Why a hand-written loop rather than a hosted agent: the tools are local (DuckDB + an
in-process index), every step is streamed to the UI as it happens, and the loop is
short-lived and request-scoped, so owning it keeps latency low and the trace inspectable.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import anthropic

from app.config import settings
from app.corpus.spec import BY_SLUG
from app.prompts import SYSTEM_PROMPT
from app.tools import TOOLS, SourceRegistry, Toolbox, ToolError

log = logging.getLogger(__name__)
FALLBACK_BETA = "server-side-fallback-2026-07-01"
TOOL_LABELS = {
    "search_research": "Searching the research library",
    "query_survey": "Querying the survey panel",
    "list_categories": "Mapping categories",
    "create_chart": "Building a chart",
}

Event = dict[str, Any]


def _history_to_messages(history: list[dict[str, str]]) -> list[dict[str, Any]]:
    msgs: list[dict[str, Any]] = []
    for m in history:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n\n" + content
        else:
            msgs.append({"role": role, "content": content})
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    return msgs


class ClaudeAnalyst:
    def __init__(self, toolbox: Toolbox, client: anthropic.AsyncAnthropic | None = None) -> None:
        self.toolbox = toolbox
        self.client = client or anthropic.AsyncAnthropic()
        self.use_fallbacks = True

    def _request(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": settings.model,
            "max_tokens": 16000,
            "system": SYSTEM_PROMPT,
            "tools": TOOLS,
            "messages": messages,
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": settings.effort},
            "cache_control": {"type": "ephemeral"},
        }
        if self.use_fallbacks:
            # Server-side refusal fallback: the API re-runs a declined turn on a fallback model.
            kwargs |= {"betas": [FALLBACK_BETA], "fallbacks": "default"}
        return kwargs

    async def run(
        self, history: list[dict[str, str]], scope: str | None = None, lang: str = "en"
    ) -> AsyncIterator[Event]:
        messages = _history_to_messages(history)
        if messages and messages[-1]["role"] == "user":
            notes = []
            if scope:
                notes.append(
                    f"I am browsing the {BY_SLUG[scope].name} category (slug `{scope}`); "
                    "focus on it unless my question clearly asks about something else."
                )
            if lang == "fr":
                notes.append("My interface is in French: answer in French.")
            if notes:
                messages[-1]["content"] += "\n\n(Context: " + " ".join(notes) + ")"
        if not messages or messages[-1]["role"] != "user":
            yield {"type": "error", "message": "The last message must come from the user."}
            return
        reg = SourceRegistry()
        usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        t0 = time.perf_counter()
        yield {"type": "status", "text": "Planning the analysis"}

        for turn in range(settings.max_agent_turns):
            try:
                async with self.client.beta.messages.stream(**self._request(messages)) as stream:
                    async for event in stream:
                        if event.type == "text":
                            yield {"type": "text", "delta": event.text}
                        elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                            name = event.content_block.name
                            yield {"type": "status", "text": TOOL_LABELS.get(name, name)}
                    response = await stream.get_final_message()
            except ValueError:
                # Tool-input JSON the SDK could not parse: re-issue the turn once.
                if turn + 1 < settings.max_agent_turns:
                    continue
                raise
            except anthropic.BadRequestError as exc:
                # Older deployments may not accept server-side fallbacks: retry without them once.
                if self.use_fallbacks and "fallback" in str(exc).lower():
                    log.warning("Server-side fallbacks rejected; retrying without them.")
                    self.use_fallbacks = False
                    continue
                log.error("Claude API rejected the request: %s", exc)
                yield {"type": "error", "message": "Claude API rejected the request (400)."}
                return
            except anthropic.RateLimitError:
                yield {"type": "error", "message": "Rate limited by the Claude API. Please retry shortly."}
                return
            except anthropic.AuthenticationError:
                yield {"type": "error", "message": "Invalid Anthropic credentials on the server."}
                return
            except anthropic.APIStatusError as exc:
                yield {"type": "error", "message": f"Claude API error ({exc.status_code})."}
                return
            except anthropic.APIConnectionError:
                yield {"type": "error", "message": "Could not reach the Claude API."}
                return

            u = response.usage
            for key in usage:
                usage[key] += getattr(u, key, 0) or 0

            if response.stop_reason == "refusal":
                yield {"type": "error", "message": "The model declined this request."}
                return
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue
            if not tool_uses:
                break
            if response.stop_reason == "max_tokens":
                yield {"type": "error", "message": "The answer was cut off (max tokens)."}
                return

            messages.append({"role": "assistant", "content": response.content})
            # Tools are fast and local; run them in order so citation IDs are deterministic.
            results = [await self._exec(b, reg) for b in tool_uses]
            tool_results = []
            for block, (result, events, is_error) in zip(tool_uses, results, strict=True):
                yield {
                    "type": "tool_call",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                    "is_error": is_error,
                    "summary": next((e["summary"] for e in events if e["type"] == "tool_summary"), ""),
                }
                for e in events:
                    if e["type"] != "tool_summary":
                        yield e
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "is_error": is_error,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            yield {"type": "status", "text": "Writing the answer"}
        else:
            yield {"type": "error", "message": "Stopped after the maximum number of agent steps."}

        yield {
            "type": "done",
            "mode": "claude",
            "model": response.model,
            "usage": usage,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }

    async def _exec(self, block, reg: SourceRegistry) -> tuple[dict, list[Event], bool]:
        if not isinstance(block.input, dict):
            return (
                {"error": "INVALID_JSON: tool input must be an object"},
                [{"type": "tool_summary", "summary": "invalid input"}],
                True,
            )
        try:
            result, events = await asyncio.to_thread(self.toolbox.run, block.name, block.input, reg)
            return result, events, False
        except ToolError as exc:
            return {"error": str(exc)}, [{"type": "tool_summary", "summary": f"error: {exc}"[:160]}], True
