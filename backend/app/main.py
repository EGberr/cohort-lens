"""Cohort Lens HTTP API (FastAPI). Run: `uv run uvicorn app.main:app --reload --port 8000`."""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent import ClaudeAnalyst
from app.config import settings
from app.corpus.spec import BY_SLUG, CHANNELS, DISCOVERY, DRIVERS, GROUPS
from app.offline import OfflineAnalyst
from app.retrieval.index import get_retriever
from app.survey import DIMENSIONS, METRICS, get_store
from app.tools import Toolbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cohort_lens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.perf_counter()
    store, retriever = get_store(), get_retriever()
    app.state.toolbox = Toolbox(retriever, store)
    app.state.analyst = ClaudeAnalyst(app.state.toolbox) if settings.llm_enabled else OfflineAnalyst(app.state.toolbox)
    log.info(
        "Ready in %.1fs: %d docs, %d chunks, modes=%s, analyst=%s",
        time.perf_counter() - t0,
        len(retriever.docs),
        len(retriever.chunks),
        retriever.available_modes(),
        type(app.state.analyst).__name__,
    )
    yield


app = FastAPI(title="Cohort Lens API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])


# ── models ───────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=20_000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=400)
    k: int = Field(default=8, ge=1, le=20)
    mode: Literal["bm25", "dense", "hybrid", "hybrid_rerank"] | None = None
    categories: list[str] | None = None


class SurveyRequest(BaseModel):
    metric: str
    categories: list[str]
    breakdown: str | None = None
    filters: dict[str, Any] | None = None


# ── routes ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health() -> dict[str, Any]:
    r = get_retriever()
    return {
        "status": "ok",
        "analyst": "claude" if settings.llm_enabled else "offline",
        "model": settings.model if settings.llm_enabled else "offline-analyst",
        "retrieval_modes": r.available_modes(),
        "documents": len(r.docs),
        "chunks": len(r.chunks),
        "respondents": get_store().n_respondents,
    }


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "groups": GROUPS,
        "metrics": METRICS,
        "dimensions": list(DIMENSIONS),
        "channels": CHANNELS,
        "discovery": DISCOVERY,
        "drivers": DRIVERS,
    }


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    store = get_store()
    kpis = store.category_kpis()
    groups = []
    for g, name in GROUPS.items():
        ks = [k for k in kpis if k["group"] == g]
        groups.append(
            {
                "group": g,
                "name": name,
                "categories": len(ks),
                "avg_penetration": round(sum(k["penetration"] for k in ks) / len(ks), 1),
                "annual_spend_per_capita": round(sum(k["annual_spend_per_capita"] for k in ks), 1),
                "avg_growth": round(sum(k["yoy_growth"] for k in ks) / len(ks), 1),
            }
        )
    return {
        "respondents": store.n_respondents,
        "categories": kpis,
        "groups": groups,
        "demographics": store.demographics(),
    }


@app.get("/api/categories/{slug}")
def category(slug: str) -> dict[str, Any]:
    if slug not in BY_SLUG:
        raise HTTPException(404, "Unknown category")
    store, spec = get_store(), BY_SLUG[slug]
    kpi = next(k for k in store.category_kpis() if k["slug"] == slug)

    def q(metric, breakdown=None):
        return store.query(metric, [slug], breakdown=breakdown).rows

    r = get_retriever()
    docs = [
        {"doc_id": d.doc_id, "title": d.title, "type": d.doc_type}
        for d in r.docs
        if slug in d.categories or d.doc_type == "thematic_report"
    ]
    return {
        "kpi": kpi,
        "aliases": list(spec.aliases),
        "insight": spec.insight,
        "recommendation": spec.recommendation,
        "trends": list(spec.trends),
        "barriers": list(spec.barriers),
        "channel_mix": q("channel_mix"),
        "discovery_mix": q("discovery_mix"),
        "driver_mix": q("driver_mix"),
        "penetration_by": {d: q("penetration", d) for d in ("gender", "age_band", "country", "income_band")},
        "spend_by_country": q("avg_monthly_spend", "country"),
        "discovery_by_age": q("discovery_mix", "age_band"),
        "documents": docs,
    }


@app.get("/api/documents/{doc_id}")
def document(doc_id: str) -> dict[str, Any]:
    r = get_retriever()
    doc = r.doc_by_id.get(doc_id)
    if not doc:
        raise HTTPException(404, "Unknown document")
    return {
        "doc_id": doc.doc_id,
        "title": doc.title,
        "type": doc.doc_type,
        "meta": doc.meta,
        "body": doc.body,
        "chunks": [c.chunk_id for c in r.chunks if c.doc_id == doc_id],
    }


@app.get("/api/documents")
def documents() -> list[dict[str, Any]]:
    r = get_retriever()
    return [
        {
            "doc_id": d.doc_id,
            "title": d.title,
            "type": d.doc_type,
            "categories": d.categories,
            "group": d.meta.get("group"),
        }
        for d in r.docs
    ]


@app.post("/api/search")
def search(req: SearchRequest) -> dict[str, Any]:
    r = get_retriever()
    t0 = time.perf_counter()
    hits = r.search(req.query, k=req.k, mode=req.mode, categories=req.categories)
    return {
        "mode": req.mode or r.default_mode(),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "hits": [h.to_dict() for h in hits],
    }


@app.post("/api/survey")
def survey(req: SurveyRequest) -> dict[str, Any]:
    from app.survey import SurveyQueryError

    try:
        return get_store().query(req.metric, req.categories, req.breakdown, req.filters).to_dict()
    except SurveyQueryError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/eval")
def eval_report() -> dict[str, Any]:
    path = settings.data_dir / "eval" / "report.json"
    if not path.exists():
        raise HTTPException(404, "No evaluation report yet. Run `make eval`.")
    return json.loads(path.read_text())


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    analyst = request.app.state.analyst
    history = [m.model_dump() for m in req.messages]

    async def gen():
        try:
            async for event in analyst.run(history):
                if await request.is_disconnected():
                    break
                yield {"data": json.dumps(event, ensure_ascii=False, default=str)}
        except Exception:  # never leak a stack trace into the stream
            log.exception("chat failed")
            yield {"data": json.dumps({"type": "error", "message": "Internal error while answering."})}

    return EventSourceResponse(gen(), ping=15)
