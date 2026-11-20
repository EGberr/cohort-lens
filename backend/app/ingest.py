"""Corpus management CLI.

  uv run python -m app.ingest build                 # regenerate demo panel, reports and index
  uv run python -m app.ingest add report.pdf notes.md --category skincare
  uv run python -m app.ingest index                 # (re)build the embedding index only
  uv run python -m app.ingest list

Imported files are converted to Markdown under data/corpus/external/ with front matter, then
picked up by the same section-aware chunker, BM25 index and embedding index as the demo corpus.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from app.config import settings
from app.corpus.spec import BY_SLUG

EXTERNAL = "external"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def pdf_to_markdown(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            # One section per page keeps citations precise ("Page 4").
            parts.append(f"## Page {i}\n\n{re.sub(r'[ \\t]+', ' ', text)}")
    return "\n\n".join(parts)


def html_to_markdown(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|nav|footer).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<h[1-3][^>]*>(.*?)</h[1-3]>", r"\n\n## \1\n\n", raw)
    raw = re.sub(r"(?i)<(p|li|br|div)[^>]*>", "\n", raw)
    text = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()


def add(paths: list[Path], categories: list[str], title: str | None) -> list[Path]:
    unknown = [c for c in categories if c not in BY_SLUG]
    if unknown:
        sys.exit(f"Unknown category slugs: {unknown}")
    out_dir = settings.corpus_dir / EXTERNAL
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            body = pdf_to_markdown(path)
        elif suffix in {".md", ".markdown", ".txt"}:
            body = path.read_text(encoding="utf-8")
            body = re.sub(r"^---\n.*?\n---\n", "", body, flags=re.S)
        elif suffix in {".html", ".htm"}:
            body = html_to_markdown(path.read_text(encoding="utf-8", errors="ignore"))
        else:
            print(f"skip {path} (unsupported type)")
            continue
        if not body.strip():
            print(f"skip {path} (no extractable text)")
            continue
        doc_title = title or path.stem.replace("_", " ").replace("-", " ").title()
        if "## " not in body:
            body = f"## Content\n\n{body}"
        front = ["---", f"id: ext-{_slug(path.stem)}", f"title: {doc_title}", "type: external", f"source: {path.name}"]
        if categories:
            front.append(f"categories: [{', '.join(categories)}]")
        front.append("---")
        target = out_dir / f"{_slug(path.stem)}.md"
        target.write_text("\n".join(front) + f"\n\n# {doc_title}\n\n{body.strip()}\n", encoding="utf-8")
        written.append(target)
        print(f"added {path} -> {target.relative_to(settings.data_dir)}")
    return written


def build_index() -> None:
    from app.retrieval.index import Retriever

    r = Retriever()
    print(f"Indexed {len(r.docs)} documents, {len(r.chunks)} chunks; modes: {r.available_modes()}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m app.ingest")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="Regenerate the synthetic panel, reports and index")
    a = sub.add_parser("add", help="Import PDF / Markdown / text / HTML files")
    a.add_argument("files", nargs="+", type=Path)
    a.add_argument("--category", action="append", default=[], help="Category slug (repeatable)")
    a.add_argument("--title")
    sub.add_parser("index", help="Rebuild the embedding index")
    sub.add_parser("list", help="List corpus documents")
    args = ap.parse_args()

    if args.cmd == "build":
        from app.corpus.reports import CorpusBuilder
        from app.corpus.survey import build_parquet
        from app.survey import SurveyStore

        build_parquet(settings.survey_dir)
        external = settings.corpus_dir / EXTERNAL
        saved = {p.name: p.read_text() for p in external.glob("*.md")} if external.exists() else {}
        n = CorpusBuilder(SurveyStore()).build(settings.corpus_dir)
        if saved:  # keep imported documents across rebuilds
            external.mkdir(parents=True, exist_ok=True)
            for name, text in saved.items():
                (external / name).write_text(text)
        print(f"Generated {n} demo documents")
        build_index()
    elif args.cmd == "add":
        if add(args.files, args.category, args.title):
            build_index()
    elif args.cmd == "index":
        build_index()
    elif args.cmd == "list":
        from app.retrieval.chunking import load_corpus

        docs, chunks = load_corpus(settings.corpus_dir)
        for d in docs:
            print(f"{d.doc_id:45s} {d.doc_type:16s} {d.title}")
        print(f"\n{len(docs)} documents, {len(chunks)} chunks")


if __name__ == "__main__":
    main()
