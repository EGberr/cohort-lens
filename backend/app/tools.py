"""Agent tools: definitions (JSON Schema for Claude), validation, and execution.

Each tool returns (result_for_model, events_for_ui). Sources get stable per-conversation
IDs (S1, S2... for passages, D1, D2... for survey datasets) that the model cites inline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.corpus.spec import BY_SLUG, CATEGORIES, GROUPS
from app.retrieval.index import Retriever
from app.survey import DIMENSIONS, METRICS, SurveyQueryError, SurveyStore

CATEGORY_SLUGS = [c.slug for c in CATEGORIES]
DOC_TYPES = ["category_report", "sector_report", "thematic_report", "methodology", "external"]


# ── input models (validation of tool inputs) ─────────────────────────────────
class SearchInput(BaseModel):
    query: str = Field(min_length=2, max_length=400)
    categories: list[str] | None = None
    doc_types: list[str] | None = None
    k: int = Field(default=6, ge=1, le=10)

    @field_validator("categories")
    @classmethod
    def _cats(cls, v):
        if v:
            bad = [c for c in v if c not in BY_SLUG]
            if bad:
                raise ValueError(f"unknown category slugs {bad}")
        return v


class SurveyInput(BaseModel):
    metric: Literal[tuple(METRICS)]  # type: ignore[valid-type]
    categories: list[str] = Field(min_length=1, max_length=12)
    breakdown: Literal[tuple(DIMENSIONS)] | None = None  # type: ignore[valid-type]
    filters: dict[str, Any] | None = None


class ListInput(BaseModel):
    group: Literal[tuple(GROUPS)] | None = None  # type: ignore[valid-type]


class ChartPoint(BaseModel):
    label: str
    value: float
    series: str | None = None


class ChartInput(BaseModel):
    title: str = Field(max_length=120)
    chart_type: Literal["bar", "horizontal_bar", "grouped_bar", "donut"]
    unit: str = Field(default="%", max_length=20)
    data: list[ChartPoint] = Field(min_length=1, max_length=60)
    source_ids: list[str] = Field(default_factory=list)


# ── tool definitions for the Messages API ────────────────────────────────────
TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_research",
        "description": (
            "Hybrid semantic + keyword search over the research library: 50 category reports, 9 sector "
            "overviews, thematic reports (social commerce, sustainability, dupes, loyalty, wallet share) "
            "and the panel methodology. Returns passages with citation IDs (S1, S2...). Use it for "
            "qualitative insight, context, trends and recommendations. Write focused queries; run several "
            "searches for multi-part questions rather than one broad search."
        ),
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural-language search query."},
                "categories": {
                    "type": "array",
                    "items": {"type": "string", "enum": CATEGORY_SLUGS},
                    "description": "Optional category slugs to restrict the search (thematic reports are always included).",
                },
                "doc_types": {"type": "array", "items": {"type": "string", "enum": DOC_TYPES}},
                "k": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Passages to return (default 6)."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "query_survey",
        "description": (
            "Run an exact aggregate query on the respondent-level Gen Z panel (6,000 respondents aged 16-29, "
            "FR/UK/DE/ES/IT/US). Returns a dataset with a citation ID (D1, D2...), base sizes (n) and "
            "low-base warnings. Use it for any number: penetration, spend, channel/discovery/driver mixes, "
            "sustainability, dupe, loyalty and price rates, optionally broken down by one demographic "
            "dimension and filtered by others. Metrics: " + "; ".join(f"{k} = {v}" for k, v in METRICS.items())
        ),
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "enum": list(METRICS)},
                "categories": {
                    "type": "array",
                    "items": {"type": "string", "enum": CATEGORY_SLUGS},
                    "minItems": 1,
                    "maxItems": 12,
                },
                "breakdown": {
                    "type": "string",
                    "enum": list(DIMENSIONS),
                    "description": "Optional dimension to split results by.",
                },
                "filters": {
                    "type": "object",
                    "description": 'Optional filters, e.g. {"country": ["FR", "DE"], "age_band": "16-19"}.',
                    "properties": {
                        "country": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["FR", "UK", "DE", "ES", "IT", "US"]},
                        },
                        "gender": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["female", "male", "non-binary"]},
                        },
                        "age_band": {"type": "array", "items": {"type": "string", "enum": ["16-19", "20-24", "25-29"]}},
                        "income_band": {"type": "array", "items": {"type": "string", "enum": ["low", "mid", "high"]}},
                        "urban": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["metric", "categories"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_categories",
        "description": "List the 50 category slugs with names, sectors and headline KPIs. Use it to map the user's wording to slugs.",
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {"group": {"type": "string", "enum": list(GROUPS)}},
            "additionalProperties": False,
        },
    },
    {
        "name": "create_chart",
        "description": (
            "Render a chart for the user from numbers you already retrieved with query_survey. Use at most "
            "one or two charts per answer, only when a comparison is clearer visually. Never invent values."
        ),
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "chart_type": {"type": "string", "enum": ["bar", "horizontal_bar", "grouped_bar", "donut"]},
                "unit": {"type": "string", "description": "e.g. %, EUR / month"},
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "number"},
                            "series": {"type": "string", "description": "Series name for grouped bars."},
                        },
                        "required": ["label", "value"],
                        "additionalProperties": False,
                    },
                },
                "source_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dataset IDs (D1...) the numbers come from.",
                },
            },
            "required": ["title", "chart_type", "data"],
            "additionalProperties": False,
        },
    },
]
TOOLS[-1]["cache_control"] = {"type": "ephemeral"}


@dataclass
class SourceRegistry:
    """Per-conversation registry that assigns citation IDs."""

    passages: dict[str, str] = field(default_factory=dict)  # chunk_id -> S#
    datasets: list[dict[str, Any]] = field(default_factory=list)
    charts: int = 0

    def passage_id(self, chunk_id: str) -> tuple[str, bool]:
        if chunk_id in self.passages:
            return self.passages[chunk_id], False
        sid = f"S{len(self.passages) + 1}"
        self.passages[chunk_id] = sid
        return sid, True

    def dataset_id(self) -> str:
        return f"D{len(self.datasets) + 1}"


class ToolError(Exception):
    pass


class Toolbox:
    def __init__(self, retriever: Retriever, store: SurveyStore) -> None:
        self.retriever = retriever
        self.store = store
        self._kpis = {k["slug"]: k for k in store.category_kpis()}

    def run(self, name: str, raw_input: Any, reg: SourceRegistry) -> tuple[dict[str, Any], list[dict]]:
        try:
            if name == "search_research":
                return self._search(SearchInput.model_validate(raw_input), reg)
            if name == "query_survey":
                return self._survey(SurveyInput.model_validate(raw_input), reg)
            if name == "list_categories":
                return self._list(ListInput.model_validate(raw_input or {}))
            if name == "create_chart":
                return self._chart(ChartInput.model_validate(raw_input), reg)
        except ValidationError as exc:
            raise ToolError(f"Invalid input for {name}: {exc.errors(include_url=False)}") from exc
        except SurveyQueryError as exc:
            raise ToolError(str(exc)) from exc
        raise ToolError(f"Unknown tool {name}")

    # ── implementations ──────────────────────────────────────────────────────
    def _search(self, inp: SearchInput, reg: SourceRegistry):
        hits = self.retriever.search(inp.query, k=inp.k, categories=inp.categories, doc_types=inp.doc_types)
        events, passages = [], []
        for h in hits:
            sid, new = reg.passage_id(h.chunk.chunk_id)
            src = {
                "id": sid,
                "kind": "passage",
                "chunk_id": h.chunk.chunk_id,
                "doc_id": h.chunk.doc_id,
                "title": h.chunk.title,
                "section": h.chunk.section,
                "text": h.chunk.text,
                "doc_type": h.chunk.doc_type,
                "score": round(h.score, 4),
            }
            if new:
                events.append({"type": "source", "source": src})
            passages.append({"id": sid, "document": h.chunk.title, "section": h.chunk.section, "text": h.chunk.text})
        summary = f"{len(passages)} passages" + (f" ({', '.join(p['id'] for p in passages)})" if passages else "")
        return {"passages": passages, "note": None if passages else "No matching passages."}, events + [
            {"type": "tool_summary", "summary": summary}
        ]

    def _survey(self, inp: SurveyInput, reg: SourceRegistry):
        res = self.store.query(inp.metric, inp.categories, inp.breakdown, inp.filters)
        did = reg.dataset_id()
        payload = {"id": did, **res.to_dict(), "category_names": {c: BY_SLUG[c].name for c in inp.categories}}
        reg.datasets.append(payload)
        rows = res.rows
        summary = f"{did}: {inp.metric} · {len(rows)} rows" + (f" by {inp.breakdown}" if inp.breakdown else "")
        return payload, [{"type": "dataset", "dataset": payload}, {"type": "tool_summary", "summary": summary}]

    def _list(self, inp: ListInput):
        cats = [k for k in self._kpis.values() if inp.group is None or k["group"] == inp.group]
        out = [
            {
                "slug": k["slug"],
                "name": k["name"],
                "sector": k["group_name"],
                "aliases": list(BY_SLUG[k["slug"]].aliases),
                "penetration_pct": k["penetration"],
                "yoy_growth_pct": k["yoy_growth"],
            }
            for k in cats
        ]
        return {"categories": out}, [{"type": "tool_summary", "summary": f"{len(out)} categories"}]

    def _chart(self, inp: ChartInput, reg: SourceRegistry):
        known = {d["id"] for d in reg.datasets}
        unknown = [s for s in inp.source_ids if s not in known]
        if unknown:
            raise ToolError(f"Unknown dataset ids {unknown}. Charts must use retrieved datasets.")
        reg.charts += 1
        chart = {"id": f"C{reg.charts}", **inp.model_dump()}
        return {"ok": True, "chart_id": chart["id"]}, [
            {"type": "chart", "chart": chart},
            {"type": "tool_summary", "summary": f"chart {chart['id']}"},
        ]
