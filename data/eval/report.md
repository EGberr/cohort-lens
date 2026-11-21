# Cohort Lens evaluation — 2026-11-21

Corpus: 67 documents, 527 chunks.

## Retrieval (208 queries)

| Mode | Hit@1 | Hit@5 | MRR@10 | Section Hit@5 | p50 latency |
|---|---|---|---|---|---|
| bm25 | 81.7% | 97.1% | 0.871 | 32.7% | 0.3 ms |
| dense | 84.1% | 97.1% | 0.900 | 36.1% | 4.4 ms |
| hybrid | 91.3% | 99.5% | 0.949 | 39.4% | 4.9 ms |
| hybrid_rerank | 90.9% | 99.5% | 0.944 | 49.5% | 453.3 ms |

## Answers (40 questions, offline / offline-analyst)

- Numeric accuracy: 100.0%
- Answers citing a survey dataset: 100.0%
- Error rate: 0.0%
- Median latency: 1.89 s
