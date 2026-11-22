"""Zentrend evaluation harness.

1. Retrieval: ~200 generated queries with gold documents/sections, written with category
   *aliases* and trend names rather than category names, so lexical overlap is limited.
   Compares BM25, dense, hybrid (RRF) and hybrid + cross-encoder rerank on Hit@1, Hit@5,
   MRR@10, section Hit@5 and latency.
2. Answers: questions whose gold number is computed from the panel. An answer passes when
   it states the gold value (±1 point / €1) and cites a dataset ID. Runs the Claude agent
   when credentials are configured, else the offline analyst.

Run: `uv run python -m eval.run_eval [--answers 40] [--skip-answers]`
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import statistics
import time
from datetime import UTC, datetime

from app.agent import ClaudeAnalyst
from app.config import settings
from app.corpus.spec import CATEGORIES, DRIVERS
from app.offline import OfflineAnalyst
from app.retrieval.index import Retriever
from app.survey import SurveyStore
from app.tools import Toolbox

SEED = 7


# ── retrieval set ────────────────────────────────────────────────────────────
def retrieval_queries() -> list[dict]:
    rng = random.Random(SEED)
    qs = []
    for c in CATEGORIES:
        alias = rng.choice(c.aliases)
        doc = f"cat-{c.slug}"
        qs += [
            {
                "query": f"Where do young consumers usually buy {alias}?",
                "doc": doc,
                "section": "path-to-purchase",
                "kind": "channel",
            },
            {
                "query": f"What motivates Gen Z to purchase {alias} and what holds them back?",
                "doc": doc,
                "section": "purchase-drivers-and-barriers",
                "kind": "drivers",
            },
            {"query": f"Emerging trends: {c.trends[0]}", "doc": doc, "section": "trends-to-watch", "kind": "trend"},
            {
                "query": f"How should brands selling {rng.choice(c.aliases)} adapt their marketing for Gen Z?",
                "doc": doc,
                "section": "implications-for-marketers",
                "kind": "implications",
            },
        ]
    return qs


def evaluate_retrieval(retriever: Retriever) -> dict:
    queries = retrieval_queries()
    results = {}
    for mode in retriever.available_modes():
        hit1 = hit5 = sec5 = 0
        rr, lat = [], []
        by_kind: dict[str, list[int]] = {}
        for q in queries:
            t0 = time.perf_counter()
            hits = retriever.search(q["query"], k=10, mode=mode)
            lat.append((time.perf_counter() - t0) * 1000)
            docs = [h.chunk.doc_id for h in hits]
            secs = [h.chunk.chunk_id for h in hits[:5]]
            rank = next((i + 1 for i, d in enumerate(docs) if d == q["doc"]), None)
            hit1 += rank == 1
            hit5 += bool(rank and rank <= 5)
            sec5 += any(s.startswith(f"{q['doc']}#{q['section']}") for s in secs)
            rr.append(1 / rank if rank else 0.0)
            by_kind.setdefault(q["kind"], []).append(int(bool(rank and rank <= 5)))
        n = len(queries)
        results[mode] = {
            "hit@1": round(hit1 / n, 3),
            "hit@5": round(hit5 / n, 3),
            "mrr@10": round(sum(rr) / n, 3),
            "section_hit@5": round(sec5 / n, 3),
            "latency_p50_ms": round(statistics.median(lat), 1),
            "latency_p95_ms": round(sorted(lat)[int(0.95 * n) - 1], 1),
            "hit@5_by_kind": {k: round(sum(v) / len(v), 3) for k, v in by_kind.items()},
        }
    return {"n_queries": len(queries), "modes": results, "examples": [q["query"] for q in queries[:8]]}


# ── answer set ───────────────────────────────────────────────────────────────
def answer_questions(store: SurveyStore, n: int) -> list[dict]:
    rng = random.Random(SEED)
    cats = rng.sample(CATEGORIES, k=min(n, len(CATEGORIES)))
    out = []
    for i, c in enumerate(cats):
        kind = i % 4
        if kind == 0:
            v = store.query("penetration", [c.slug]).rows[0]["value"]
            q = f"What share of Gen Z bought {c.name.lower()} in the last 12 months?"
            out.append({"question": q, "gold": v, "unit": "%", "category": c.slug})
        elif kind == 1:
            v = store.query("avg_monthly_spend", [c.slug]).rows[0]["value"]
            q = f"How much do Gen Z buyers spend per month on {c.name.lower()}?"
            out.append({"question": q, "gold": v, "unit": "EUR", "category": c.slug})
        elif kind == 2:
            rows = store.query("penetration", [c.slug], breakdown="gender").rows
            v = next(r["value"] for r in rows if r["segment"] == "female")
            q = f"What percentage of Gen Z women bought {c.name.lower()} last year?"
            out.append({"question": q, "gold": v, "unit": "%", "category": c.slug})
        else:
            top = store.query("channel_mix", [c.slug]).rows[0]
            q = f"What is the main purchase channel for {c.name.lower()} among Gen Z, and what share does it take?"
            out.append(
                {"question": q, "gold": top["value"], "unit": "%", "category": c.slug, "gold_label": top["option"]}
            )
    return out


NUM = re.compile(r"€?\s?(\d+(?:[.,]\d+)?)\s?%?")


def grade(answer: str, item: dict) -> dict:
    nums = [float(m.replace(",", ".")) for m in NUM.findall(answer)]
    tol = 1.0 if item["unit"] == "%" else 1.0
    correct = any(abs(x - item["gold"]) <= tol for x in nums)
    cited_data = bool(re.search(r"\[D\d+\]", answer))
    cited_any = bool(re.search(r"\[[SD]\d+\]", answer))
    label_ok = item.get("gold_label") is None or item["gold_label"].split(" (")[0].lower() in answer.lower()
    return {"correct": correct and label_ok, "cited_dataset": cited_data, "cited_any": cited_any}


async def evaluate_answers(toolbox: Toolbox, store: SurveyStore, n: int) -> dict:
    use_claude = settings.llm_enabled
    analyst = ClaudeAnalyst(toolbox) if use_claude else OfflineAnalyst(toolbox)
    items = answer_questions(store, n)
    rows, lat, tokens = [], [], {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
    for item in items:
        t0 = time.perf_counter()
        text, tools_used, error = "", [], None
        async for ev in analyst.run([{"role": "user", "content": item["question"]}]):
            if ev["type"] == "text":
                text += ev["delta"]
            elif ev["type"] == "tool_call":
                tools_used.append(ev["name"])
            elif ev["type"] == "error":
                error = ev["message"]
            elif ev["type"] == "done":
                for k in tokens:
                    tokens[k] += ev.get("usage", {}).get(k, 0)
        lat.append(time.perf_counter() - t0)
        g = grade(text, item)
        rows.append({**item, **g, "tools": tools_used, "error": error, "answer": text[:1200]})
    n_items = len(rows)
    return {
        "analyst": "claude" if use_claude else "offline",
        "model": settings.model if use_claude else "offline-analyst",
        "n_questions": n_items,
        "numeric_accuracy": round(sum(r["correct"] for r in rows) / n_items, 3),
        "dataset_citation_rate": round(sum(r["cited_dataset"] for r in rows) / n_items, 3),
        "citation_rate": round(sum(r["cited_any"] for r in rows) / n_items, 3),
        "error_rate": round(sum(bool(r["error"]) for r in rows) / n_items, 3),
        "latency_p50_s": round(statistics.median(lat), 2),
        "tokens": tokens,
        "items": rows,
    }


def to_markdown(report: dict) -> str:
    lines = [
        f"# Zentrend evaluation — {report['generated_at'][:10]}",
        "",
        f"Corpus: {report['corpus']['documents']} documents, {report['corpus']['chunks']} chunks.",
        "",
        f"## Retrieval ({report['retrieval']['n_queries']} queries)",
        "",
        "| Mode | Hit@1 | Hit@5 | MRR@10 | Section Hit@5 | p50 latency |",
        "|---|---|---|---|---|---|",
    ]
    for mode, m in report["retrieval"]["modes"].items():
        lines.append(
            f"| {mode} | {m['hit@1']:.1%} | {m['hit@5']:.1%} | {m['mrr@10']:.3f} | "
            f"{m['section_hit@5']:.1%} | {m['latency_p50_ms']} ms |"
        )
    a = report.get("answers")
    if a:
        lines += [
            "",
            f"## Answers ({a['n_questions']} questions, {a['analyst']} / {a['model']})",
            "",
            f"- Numeric accuracy: {a['numeric_accuracy']:.1%}",
            f"- Answers citing a survey dataset: {a['dataset_citation_rate']:.1%}",
            f"- Error rate: {a['error_rate']:.1%}",
            f"- Median latency: {a['latency_p50_s']} s",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", type=int, default=40)
    ap.add_argument("--skip-answers", action="store_true")
    args = ap.parse_args()

    store, retriever = SurveyStore(), Retriever()
    report = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "corpus": {"documents": len(retriever.docs), "chunks": len(retriever.chunks)},
        "retrieval": evaluate_retrieval(retriever),
    }
    if not args.skip_answers:
        report["answers"] = asyncio.run(evaluate_answers(Toolbox(retriever, store), store, args.answers))
    out = settings.data_dir / "eval"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (out / "report.md").write_text(to_markdown(report))
    print(to_markdown(report))
    print(f"Detailed DRIVERS vocabulary size: {len(DRIVERS)}")


if __name__ == "__main__":
    main()
