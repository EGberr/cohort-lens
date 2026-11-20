"""Deterministic offline analyst, used when no Anthropic credentials are configured.

It follows the same tool path as the Claude agent (search + survey + chart) with rule-based
planning, and emits the same event stream, so the whole product can be demoed and tested
without an API key. It is intentionally simple and labelled as such in the UI.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import AsyncIterator
from typing import Any

from app.corpus.spec import BY_SLUG, CATEGORIES, GROUPS
from app.tools import SourceRegistry, Toolbox

Event = dict[str, Any]

METRIC_RULES: list[tuple[str, str]] = [
    (r"\b(dupe|dupes|lookalike|copy|copies|knock-?off)", "dupe_rate"),
    (r"\b(sustainab|eco|green|ethical|environment)", "sustainable_premium_rate"),
    (r"\b(loyal|loyalty|switch|repurchase|same brand)", "brand_loyalty_rate"),
    (r"\b(discover|discovery|find out|hear about|awareness|inspiration)", "discovery_mix"),
    (r"\b(channel|where do|where does|buy from|shop on|purchase on|checkout|tiktok shop|online or)", "channel_mix"),
    (r"\b(why|driver|drivers|motivat|reason|choose|criteria)", "driver_mix"),
    (r"\b(per year|annual|wallet|share of wallet)", "annual_spend_per_capita"),
    (r"\b(spend|spending|how much|budget|basket|€|eur)", "avg_monthly_spend"),
    (r"\b(price.sensitiv|cheap|price matter|price-driven|deal)", "price_decisive_rate"),
]
BREAKDOWN_RULES: list[tuple[str, str]] = [
    (r"\b(men|women|male|female|gender|girls|boys|non-binary)\b", "gender"),
    (r"\b(age|older|younger|teen|teens|16-19|20-24|25-29|students?)\b", "age_band"),
    (
        r"\b(countr|market|france|french|uk|britain|british|germany|german|spain|spanish|italy|italian|us|usa|america)",
        "country",
    ),
    (r"\b(income|affluent|wealthy|low-income|rich)\b", "income_band"),
    (r"\b(urban|rural|city|cities)\b", "urban"),
]
GROUP_WORDS = {
    "beauty": "beauty",
    "fashion": "fashion",
    "food": "food",
    "drinks": "food",
    "beverage": "food",
    "tech": "tech",
    "electronics": "tech",
    "entertainment": "entertainment",
    "media": "entertainment",
    "wellness": "wellness",
    "health": "wellness",
    "home": "home",
    "travel": "mobility",
    "mobility": "mobility",
    "finance": "services",
    "money": "services",
    "services": "services",
}


def _alias_index() -> list[tuple[str, str]]:
    pairs = []
    for c in CATEGORIES:
        names = {c.name.lower(), c.slug.replace("-", " "), *[a.lower() for a in c.aliases]}
        for n in names:
            pairs.append((n, c.slug))
    return sorted(pairs, key=lambda p: -len(p[0]))


ALIASES = _alias_index()


def detect_categories(text: str) -> list[str]:
    t = " " + text.lower() + " "
    found: list[str] = []
    for alias, slug in ALIASES:
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?:s|es)?(?![a-z])", t) and slug not in found:
            found.append(slug)
            t = t.replace(alias, " ")
    if not found:
        for word, group in GROUP_WORDS.items():
            if re.search(rf"\b{word}\b", t):
                found += [c.slug for c in CATEGORIES if c.group == group and c.slug not in found]
    return found[:12]


def detect(rules: list[tuple[str, str]], text: str, default: str | None) -> str | None:
    t = text.lower()
    for pattern, value in rules:
        if re.search(pattern, t):
            return value
    return default


def _fmt(v: float, unit: str) -> str:
    if unit.startswith("EUR"):
        return f"€{v:,.0f}"
    return f"{v:.0f}%"


SEGMENT_LABELS = {
    "FR": "France",
    "UK": "UK",
    "DE": "Germany",
    "ES": "Spain",
    "IT": "Italy",
    "US": "US",
    True: "Urban",
    False: "Non-urban",
}


class OfflineAnalyst:
    def __init__(self, toolbox: Toolbox) -> None:
        self.toolbox = toolbox

    async def run(self, history: list[dict[str, str]]) -> AsyncIterator[Event]:
        question = next((m["content"] for m in reversed(history) if m.get("role") == "user"), "").strip()
        if not question:
            yield {"type": "error", "message": "Ask a question to get started."}
            return
        t0 = time.perf_counter()
        reg = SourceRegistry()
        yield {"type": "status", "text": "Planning the analysis (offline analyst)"}

        cats = detect_categories(question)
        metric = detect(METRIC_RULES, question, "penetration")
        breakdown = detect(BREAKDOWN_RULES, question, None)

        # 1. research search (always)
        yield {"type": "status", "text": "Searching the research library"}
        search_in = {"query": question, "k": 5, **({"categories": cats} if cats else {})}
        res, events = self.toolbox.run("search_research", search_in, reg)
        async for e in self._tool_events("search_research", search_in, events):
            yield e
        passages = res["passages"]
        if not cats and passages:
            top = self.toolbox.retriever.chunk_by_id[next(iter(reg.passages))].categories
            cats = top[:1]
        if not cats:
            async for e in self._stream(
                "I could not map this question to one of the 50 categories. "
                "Try naming a category, e.g. *skincare*, *sneakers* or *energy drinks*."
            ):
                yield e
            yield {
                "type": "done",
                "mode": "offline",
                "model": "offline-analyst",
                "usage": {},
                "latency_ms": int((time.perf_counter() - t0) * 1000),
            }
            return

        # 2. survey query
        yield {"type": "status", "text": "Querying the survey panel"}
        if len(cats) > 1 and breakdown and metric.endswith("_mix"):
            breakdown = None  # keep mixes readable when comparing several categories
        survey_in = {"metric": metric, "categories": cats, **({"breakdown": breakdown} if breakdown else {})}
        data, events = self.toolbox.run("query_survey", survey_in, reg)
        async for e in self._tool_events("query_survey", survey_in, events):
            yield e

        # 3. recommendation passage for the lead category
        lead = cats[0]
        rec_in = {
            "query": f"implications for marketers {BY_SLUG[lead].name}",
            "categories": [lead],
            "k": 1,
            "doc_types": ["category_report"],
        }
        rec, events = self.toolbox.run("search_research", rec_in, reg)
        async for e in self._tool_events("search_research", rec_in, events):
            yield e

        # 4. chart
        chart_in = self._chart_input(data)
        if chart_in:
            _, events = self.toolbox.run("create_chart", chart_in, reg)
            async for e in self._tool_events("create_chart", chart_in, events):
                yield e

        yield {"type": "status", "text": "Writing the answer"}
        async for e in self._stream(self._compose(data, passages, rec["passages"], cats)):
            yield e
        yield {
            "type": "done",
            "mode": "offline",
            "model": "offline-analyst",
            "usage": {},
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }

    # ── helpers ──────────────────────────────────────────────────────────────
    async def _tool_events(self, name, inp, events) -> AsyncIterator[Event]:
        await asyncio.sleep(0.05)
        summary = next((e["summary"] for e in events if e["type"] == "tool_summary"), "")
        yield {
            "type": "tool_call",
            "id": f"off_{name}_{id(inp)}",
            "name": name,
            "input": inp,
            "is_error": False,
            "summary": summary,
        }
        for e in events:
            if e["type"] != "tool_summary":
                yield e

    async def _stream(self, text: str) -> AsyncIterator[Event]:
        for piece in re.findall(r"\S+\s*|\n", text):
            yield {"type": "text", "delta": piece}
            await asyncio.sleep(0.006)

    @staticmethod
    def _label(row: dict) -> str:
        if "segment" in row:
            return str(SEGMENT_LABELS.get(row["segment"], row["segment"]))
        if "option" in row:
            return row["option"]
        return BY_SLUG[row["category"]].name

    def _chart_input(self, data: dict) -> dict | None:
        rows = data["rows"]
        cats = list(data["category_names"])
        if data["metric"].endswith("_mix") and data["breakdown"]:
            rows = [r for r in rows if r["category"] == cats[0]]
            overall = {}
            for r in rows:
                overall[r["option_key"]] = overall.get(r["option_key"], 0) + r["value"] * r["n"]
            key = max(overall, key=overall.get)
            sel = [r for r in rows if r["option_key"] == key]
            points = [{"label": self._label(r), "value": r["value"]} for r in sel]
            ctype = "bar"
            title = f"{data['category_names'][cats[0]]}: share citing {sel[0]['option']}, by {data['breakdown'].replace('_', ' ')}"
        elif data["metric"].endswith("_mix"):
            rows = [r for r in rows if r["category"] == cats[0]][:6]
            points = [{"label": r["option"], "value": r["value"]} for r in rows]
            ctype = "donut" if data["metric"] != "driver_mix" else "horizontal_bar"
            title = f"{data['category_names'][cats[0]]}: {data['description'].lower()}"
        elif data["breakdown"] and len(cats) > 1:
            points = [
                {"label": self._label(r), "value": r["value"], "series": BY_SLUG[r["category"]].name} for r in rows
            ]
            ctype, title = "grouped_bar", data["description"]
        else:
            ordered = rows if data["breakdown"] else sorted(rows, key=lambda r: -r["value"])
            points = [{"label": self._label(r), "value": r["value"]} for r in ordered]
            ctype = "bar" if len(points) <= 6 else "horizontal_bar"
            title = data["description"]
        if len(points) < 2:
            return None
        return {
            "title": title[:120],
            "chart_type": ctype,
            "unit": data["unit"],
            "data": points,
            "source_ids": [data["id"]],
        }

    def _compose(self, data: dict, passages: list[dict], rec: list[dict], cats: list[str]) -> str:
        d, unit, rows = data["id"], data["unit"], data["rows"]
        names = data["category_names"]
        lead = names[cats[0]]
        desc = data["description"][0].lower() + data["description"][1:]
        lines: list[str] = []
        if data["metric"].endswith("_mix"):
            top = [r for r in rows if r["category"] == cats[0]]
            seg = f" ({self._label(top[0])})" if "segment" in top[0] else ""
            if "segment" in top[0]:
                firsts = {}
                for r in top:
                    firsts.setdefault(r["segment"], r)
                lines.append(f"**For {lead}, top answer by segment** — {desc} [{d}]:")
                lines += [
                    f"- {self._label(r)}: {r['option']} ({_fmt(r['value'], unit)}, n={r['n']:,})"
                    for r in firsts.values()
                ]
            else:
                lines.append(
                    f"**{top[0]['option']} leads for {lead}{seg}**, cited by {_fmt(top[0]['value'], unit)} "
                    f"of buyers [{d}]."
                )
                lines += [f"- {r['option']}: {_fmt(r['value'], unit)}" for r in top[:5]]
        elif data["breakdown"]:
            by_cat: dict[str, list[dict]] = {}
            for r in rows:
                by_cat.setdefault(r["category"], []).append(r)
            for cat, rs in by_cat.items():
                hi, lo = max(rs, key=lambda r: r["value"]), min(rs, key=lambda r: r["value"])
                lines.append(
                    f"**{names[cat]}: highest among {self._label(hi)} ({_fmt(hi['value'], unit)}), "
                    f"lowest among {self._label(lo)} ({_fmt(lo['value'], unit)})** [{d}]."
                )
                lines += [f"- {self._label(r)}: {_fmt(r['value'], unit)} (n={r['n']:,})" for r in rs]
        elif len(rows) == 1:
            lines.append(f"**{lead}: {_fmt(rows[0]['value'], unit)}** — {desc} [{d}].")
        else:
            ranked = sorted(rows, key=lambda r: -r["value"])
            lines.append(
                f"**{names[ranked[0]['category']]} ranks first at {_fmt(ranked[0]['value'], unit)}** — {desc} [{d}]."
            )
            lines += [f"{i}. {names[r['category']]}: {_fmt(r['value'], unit)}" for i, r in enumerate(ranked, 1)]
        if data["notes"]:
            lines.append(f"*Note: {' '.join(data['notes'])}*")

        if passages:
            lines.append("\n### What the research says")
            prose = [p for p in passages if not p["text"].lstrip().startswith(("-", "*", "1."))]
            for p in prose[:3]:
                text = re.sub(r"\*Also covers:.*?\*\s*", "", p["text"]).replace("\n", " ")
                first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=2)
                lines.append(f"- {' '.join(first[:2]).strip()} [{p['id']}]")
        if rec:
            text = rec[0]["text"].split("\n")[0]
            lines.append("\n### So what for marketers")
            lines.append(f"{text} [{rec[0]['id']}]")
        lines.append(
            "\n*Offline analyst mode: answer assembled by rules from retrieved evidence. "
            "Configure `ANTHROPIC_API_KEY` for the full Claude agent.*"
        )
        return "\n".join(lines)


__all__ = ["OfflineAnalyst", "detect_categories", "GROUPS"]
