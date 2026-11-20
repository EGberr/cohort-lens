# Cohort Lens evaluation — 2026-11-20

Corpus: 65 documents, 459 chunks.

## Retrieval (200 queries)

| Mode | Hit@1 | Hit@5 | MRR@10 | Section Hit@5 | p50 latency |
|---|---|---|---|---|---|
| bm25 | 79.0% | 98.0% | 0.851 | 34.0% | 0.3 ms |
| dense | 77.5% | 92.5% | 0.840 | 44.0% | 4.9 ms |
| hybrid | 88.5% | 99.0% | 0.928 | 48.0% | 5.4 ms |
| hybrid_rerank | 87.0% | 99.5% | 0.920 | 56.5% | 482.0 ms |

## Answers (40 questions, offline / offline-analyst)

- Numeric accuracy: 100.0%
- Answers citing a survey dataset: 100.0%
- Error rate: 0.0%
- Median latency: 2.0 s
