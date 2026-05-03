# ADR: Delay Embedding/Reranker Until Query Set Stabilizes

- Date: 2026-05-03
- Status: Accepted
- Owners: Conversational Game Systems

## Context

The project now has a dual retrieval foundation:

1. Markdown chunk retrieval via SQLite FTS5/BM25.
2. Structured entity lookup via 5e JSON snapshots ingested into SQLite tables.

Current product phase prioritizes deterministic behavior, source traceability, and
testability over semantic recall maximization.

## Decision

Do not introduce embedding storage or reranker components in the first retrieval
delivery.

Adopt a staged policy:

1. Build and validate retrieval quality using:
   - BM25 lexical retrieval for rule text
   - exact/near-exact entity lookup for structured records
2. Maintain and grow a query-set benchmark (`eval/queries.yaml`) with expected outcomes.
3. Revisit embedding + reranker only when:
   - query set size is sufficient (target: >= 50 production-like queries)
   - baseline metrics plateau under lexical/entity-only approach
   - retrieval failure modes are categorized and reproducible

## Rationale

- Lower operational complexity at MVP stage.
- Easier debugging and legal/source traceability.
- Better test determinism for CI and regression checks.
- Avoid premature infrastructure coupling (vector DB decisions can be deferred).

## Trigger Conditions For Reconsideration

Move to evaluation of embeddings when any of the following is true:

- Recall@K on benchmark remains below target despite query normalization and routing.
- User-reported misses are primarily semantic paraphrase misses.
- Product requirements explicitly demand cross-paragraph semantic recall beyond BM25.

## Follow-up Actions

- Keep `eval/queries.yaml` updated with real user prompts and expected hits.
- Add per-intent metrics (entity lookup hit rate, rule-text recall@k, route accuracy).
- Prepare a separate ADR for:
  - embedding model choice
  - storage backend (SQLite extension vs external vector DB)
  - reranker placement (server-side post-retrieval stage)
