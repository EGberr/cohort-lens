"""Hybrid retriever: BM25 + dense embeddings fused with Reciprocal Rank Fusion, then an
optional cross-encoder rerank. Embeddings are cached on disk and keyed by a corpus hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np

from app.config import settings
from app.retrieval.bm25 import BM25
from app.retrieval.chunking import Chunk, Document, load_corpus

log = logging.getLogger(__name__)
Mode = Literal["bm25", "dense", "hybrid", "hybrid_rerank"]
RRF_K = 60
CANDIDATES = 40
RERANK_WEIGHT = 0.3  # chosen on the retrieval eval set; see README


@dataclass
class Hit:
    chunk: Chunk
    score: float
    ranks: dict[str, int]

    def to_dict(self) -> dict:
        return {**self.chunk.to_dict(), "score": round(self.score, 4), "ranks": self.ranks}


class Retriever:
    def __init__(
        self,
        corpus_dir: Path | None = None,
        index_dir: Path | None = None,
        use_dense: bool | None = None,
        use_reranker: bool | None = None,
    ) -> None:
        self.corpus_dir = corpus_dir or settings.corpus_dir
        self.index_dir = index_dir or settings.index_dir
        self.docs, self.chunks = load_corpus(self.corpus_dir)
        self.doc_by_id: dict[str, Document] = {d.doc_id: d for d in self.docs}
        self.chunk_by_id: dict[str, Chunk] = {c.chunk_id: c for c in self.chunks}
        self.bm25 = BM25([c.contextual_text for c in self.chunks])
        self._embedder = None
        self._reranker = None
        self.embeddings: np.ndarray | None = None
        want_dense = settings.use_dense if use_dense is None else use_dense
        self.rerank_enabled = settings.use_reranker if use_reranker is None else use_reranker
        if want_dense:
            try:
                self.embeddings = self._load_or_build_embeddings()
            except Exception as exc:  # model download blocked, no disk, ...
                log.warning("Dense retrieval disabled: %s", exc)
                self.embeddings = None

    # ── models ───────────────────────────────────────────────────────────────
    @property
    def corpus_hash(self) -> str:
        h = hashlib.sha256(settings.embedding_model.encode())
        for c in self.chunks:
            h.update(c.chunk_id.encode())
            h.update(c.contextual_text.encode())
        return h.hexdigest()[:16]

    def _embedder_model(self):
        if self._embedder is None:
            from fastembed import TextEmbedding

            self._embedder = TextEmbedding(settings.embedding_model)
        return self._embedder

    def _reranker_model(self):
        if self._reranker is None:
            from fastembed.rerank.cross_encoder import TextCrossEncoder

            self._reranker = TextCrossEncoder(settings.reranker_model)
        return self._reranker

    def _load_or_build_embeddings(self) -> np.ndarray:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.index_dir / "manifest.json"
        emb_path = self.index_dir / "embeddings.npy"
        if manifest_path.exists() and emb_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("corpus_hash") == self.corpus_hash:
                return np.load(emb_path)
        t0 = time.perf_counter()
        vecs = np.array(
            list(self._embedder_model().passage_embed([c.contextual_text for c in self.chunks])), dtype=np.float32
        )
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        np.save(emb_path, vecs)
        manifest_path.write_text(
            json.dumps(
                {
                    "corpus_hash": self.corpus_hash,
                    "model": settings.embedding_model,
                    "chunks": len(self.chunks),
                    "dim": int(vecs.shape[1]),
                    "build_seconds": round(time.perf_counter() - t0, 2),
                },
                indent=2,
            )
        )
        return vecs

    @property
    def dense_available(self) -> bool:
        return self.embeddings is not None

    def available_modes(self) -> list[str]:
        modes = ["bm25"]
        if self.dense_available:
            modes += ["dense", "hybrid"]
            if self.rerank_enabled:
                modes.append("hybrid_rerank")
        return modes

    def default_mode(self) -> Mode:
        return self.available_modes()[-1]  # type: ignore[return-value]

    # ── search ───────────────────────────────────────────────────────────────
    def _mask(self, categories: list[str] | None, doc_types: list[str] | None) -> np.ndarray:
        mask = np.ones(len(self.chunks), dtype=bool)
        if categories:
            cats = set(categories)
            mask &= np.array([bool(cats & set(c.categories)) or c.doc_type == "thematic_report" for c in self.chunks])
        if doc_types:
            mask &= np.array([c.doc_type in doc_types for c in self.chunks])
        return mask

    def search(
        self,
        query: str,
        k: int = 6,
        mode: Mode | None = None,
        categories: list[str] | None = None,
        doc_types: list[str] | None = None,
    ) -> list[Hit]:
        mode = mode or self.default_mode()
        if mode != "bm25" and not self.dense_available:
            mode = "bm25"
        mask = self._mask(categories, doc_types)
        if not mask.any():
            return []
        ranked: dict[str, list[int]] = {}
        if mode in ("bm25", "hybrid", "hybrid_rerank"):
            s = np.where(mask, self.bm25.scores(query), -np.inf)
            ranked["bm25"] = [i for i in np.argsort(-s)[:CANDIDATES] if np.isfinite(s[i]) and s[i] > 0]
        if mode in ("dense", "hybrid", "hybrid_rerank"):
            q = np.array(next(iter(self._embedder_model().query_embed([query]))), dtype=np.float32)
            q /= np.linalg.norm(q)
            s = np.where(mask, self.embeddings @ q, -np.inf)
            ranked["dense"] = [i for i in np.argsort(-s)[:CANDIDATES] if np.isfinite(s[i])]

        fused: dict[int, float] = {}
        ranks: dict[int, dict[str, int]] = {}
        for name, idxs in ranked.items():
            for r, i in enumerate(idxs):
                fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + r + 1)
                ranks.setdefault(i, {})[name] = r + 1
        order = sorted(fused, key=lambda i: -fused[i])

        if mode == "hybrid_rerank" and order:
            # Blend min-max normalised cross-encoder and RRF scores. A pure cross-encoder
            # order wins on section precision but loses document recall (see eval report).
            pool = order[:20]
            ce = np.array(
                list(self._reranker_model().rerank(query, [self.chunks[i].contextual_text for i in pool])), dtype=float
            )
            rrf = np.array([fused[i] for i in pool])
            blended = RERANK_WEIGHT * (ce - ce.min()) / (np.ptp(ce) or 1.0) + (1 - RERANK_WEIGHT) * (
                rrf - rrf.min()
            ) / (np.ptp(rrf) or 1.0)
            pool_sorted = sorted(zip(pool, blended, ce, strict=True), key=lambda x: -x[1])
            for r, (i, _, _ce) in enumerate(pool_sorted):
                ranks[i]["rerank"] = r + 1
            return [Hit(self.chunks[i], float(sc), ranks[i]) for i, sc, _ in pool_sorted[:k]]
        return [Hit(self.chunks[i], fused[i], ranks[i]) for i in order[:k]]


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever()
