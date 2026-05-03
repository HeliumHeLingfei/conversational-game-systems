# Rules Data Sources and Pinning Policy

This document defines which external rules corpora we ingest, how we pin versions,
and what legal and product-safety boundaries we enforce.

## 1) Approved Upstream Sources

### A. Narrative / Rulebook-Style Corpus (Markdown)

- Source: `oldmanumby/dnd.srd`
- Primary use: long-form rules explanation, flow context, adjudication language
- Expected version family: SRD 5.1 lineage
- Ingestion target: heading-based chunks for SQLite FTS5/BM25 and ripgrep fallback

### B. Structured Entity Corpus (JSON)

- Source: `5e-bits/5e-database` (optionally compared against `5e-bits/5e-srd-api`)
- Primary use: exact entity lookups (spells, monsters, classes, equipment, etc.)
- Ingestion target: SQLite entity tables keyed by resource type and `index`

## 2) Version Honesty and Naming Rules

We do not claim a rules version that is not represented by the loaded corpus.

- If using `oldmanumby/dnd.srd`, `source_system` must indicate 5.1 lineage
  (example: `srd_5_1_omu`).
- `srd_5_2_1` is reserved for an actual 5.2.1 corpus and must not be reused as a label
  for 5.1 text.
- User-facing pages and API responses must include source/version attribution when
  answering rules questions.

## 3) Pinning and Reproducibility

We pin external data by immutable version identifiers.

Required metadata for each ingest run:

- upstream repository URL
- pinned `commit` or `release_tag`
- generated-at timestamp
- content hash manifest (`SHA256`) for ingested files

Implementation requirements:

- Ingest pipeline writes a manifest with all fields above.
- CI and local builds use pinned refs only.
- Re-index runs are deterministic from the same pinned source + manifest.

## 4) Legal Boundary (Engineering Policy, Not Legal Advice)

This repository tracks source attribution and redistribution boundaries as engineering
constraints. It does not provide legal conclusions.

- Preserve upstream license notices and attribution references.
- Do not ingest proprietary non-SRD books into the default retrieval corpus.
- Keep source provenance on every chunk/entity record:
  - `source_system`
  - `commit_or_release`
  - `file` (for chunk corpus)
- When uncertain, default to excluding content until provenance is verified.

## 5) Runtime Safety Boundary

The retrieval layer returns source-backed snippets and structured fields.

- Do not merge incompatible rules versions in one answer without explicit comparison.
- If sources disagree, present source-specific outputs with clear labels.
- Keep a strict split between:
  - narrative retrieval (Markdown chunks)
  - exact lookup retrieval (structured entities)

## 6) Operational Policy

- Keep large upstream corpora out of unreviewed direct commits where possible.
- Prefer one of:
  - pinned fetch scripts + local cache
  - submodule with pinned commit
  - controlled artifact snapshot with hashes
- Record ingest updates in `documents/progress-log.md`.
