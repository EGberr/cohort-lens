"""Section-aware Markdown chunking with contextual headers.

Each chunk keeps the document title and section heading as a prefix (a light form of
"contextual retrieval"), so a passage like "64% of purchases happen on resale apps" stays
attributable to its category even when retrieved alone.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

MAX_CHARS = 1100
FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)


@dataclass
class Document:
    doc_id: str
    title: str
    doc_type: str
    path: str
    meta: dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def categories(self) -> list[str]:
        if "category" in self.meta:
            return [self.meta["category"]]
        raw = self.meta.get("categories", "")
        return [c.strip() for c in raw.strip("[]").split(",") if c.strip()]


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    section: str
    text: str
    doc_type: str
    categories: list[str]
    group: str | None
    ordinal: int

    @property
    def contextual_text(self) -> str:
        return f"{self.title} — {self.section}\n{self.text}"

    def to_dict(self) -> dict:
        return asdict(self)


def parse_document(path: Path, root: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    m = FRONT_MATTER.match(raw)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        raw = raw[m.end() :]
    title = meta.get("title")
    if not title:
        h1 = re.search(r"^# (.+)$", raw, re.M)
        title = h1.group(1).strip() if h1 else path.stem.replace("-", " ").title()
    doc_id = meta.get("id") or re.sub(r"[^a-z0-9]+", "-", str(path.relative_to(root)).lower()).strip("-")
    return Document(
        doc_id=doc_id,
        title=title,
        doc_type=meta.get("type", "external"),
        path=str(path.relative_to(root)),
        meta=meta,
        body=raw,
    )


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    parts, buf = [], ""
    for para in re.split(r"\n{2,}|(?<=[.!?])\s+(?=[A-Z0-9€])", text):
        if buf and len(buf) + len(para) + 1 > MAX_CHARS:
            parts.append(buf.strip())
            buf = ""
        buf += para + ("\n" if para.startswith("-") else " ")
    if buf.strip():
        parts.append(buf.strip())
    return parts


def chunk_document(doc: Document) -> list[Chunk]:
    body = re.sub(r"^# .+$", "", doc.body, count=1, flags=re.M)
    body = re.sub(r"^> \*\*Synthetic data notice\.\*\*.*$", "", body, flags=re.M)
    sections = re.split(r"^## (.+)$", body, flags=re.M)
    pieces: list[tuple[str, str]] = []
    intro = sections[0].strip()
    if intro:
        pieces.append(("Overview", intro))
    for i in range(1, len(sections), 2):
        pieces.append((sections[i].strip(), sections[i + 1].strip()))
    # A short preamble (e.g. an "also covers" line) is folded into the first real section.
    if len(pieces) > 1 and pieces[0][0] == "Overview" and len(pieces[0][1]) < 240:
        intro_text = pieces.pop(0)[1]
        pieces[0] = (pieces[0][0], f"{intro_text}\n\n{pieces[0][1]}")

    chunks: list[Chunk] = []
    for heading, text in pieces:
        if not text:
            continue
        for j, part in enumerate(_split_long(text)):
            ordinal = len(chunks)
            suffix = f"-{j + 1}" if j else ""
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}#{_slug(heading)}{suffix}",
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=heading,
                    text=part,
                    doc_type=doc.doc_type,
                    categories=doc.categories,
                    group=doc.meta.get("group"),
                    ordinal=ordinal,
                )
            )
    return chunks


def load_corpus(corpus_dir: Path) -> tuple[list[Document], list[Chunk]]:
    docs, chunks = [], []
    for path in sorted(corpus_dir.rglob("*.md")):
        doc = parse_document(path, corpus_dir)
        docs.append(doc)
        chunks.extend(chunk_document(doc))
    return docs, chunks
