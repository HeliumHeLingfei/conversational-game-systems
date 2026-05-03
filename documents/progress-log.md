# Project Progress Log

This file is the durable project memory for cross-session continuity.
Update it at the end of meaningful work sessions.

## 2026-05-03

### Goals

- Establish durable agent workflow and project context layers
- Align repository structure for product-facing pages
- Install and enable high-value skills for repeatable execution

### Completed

- Created and pushed root `AGENTS.md` with workflow, verification, and skill trigger guidance.
- Added layered instructions:
  - `pages/AGENTS.md`
  - `templates/AGENTS.md`
- Added Cursor project rules:
  - `.cursor/rules/agent-hard-constraints.mdc`
  - `.cursor/rules/web-content-standards.mdc`
- Added repo-scoped skills:
  - `.agents/skills/story-pack-spec/SKILL.md`
  - `.agents/skills/release-checklist/SKILL.md`
- Converged structure from legacy `docs/` and `documents/` assets into `pages/`.
- Updated `README.md` to use GitHub Pages source folder `/pages`.
- Pushed all commits to `origin/main`.

### In Progress

- Story pack spec refinement is active in `documents/story-pack-v1-spec.md`.

### Decisions

- Keep `AGENTS.md` concise and behavior-changing only.
- Use rules for hard constraints and file-scoped standards.
- Use skills for repeatable workflows and project-specific operations.
- Keep project continuity in repository files rather than chat history.

### Next

- Continue iterative work on `documents/story-pack-v1-spec.md`.
- Add release readiness usage in future sessions via `release-checklist` skill.
- Keep this log updated after each major task batch.

### Session Update (Story-Pack v1 Execution)

#### Story-Pack Completed

- Added `documents/story-pack-v1-spec.md` as a concrete v1 draft spec with required sections, validation rules, and backward compatibility notes.
- Added `documents/story-pack-v1.schema.json` for machine-readable validation and `documents/story-pack-v1.minimal.json` as a runnable minimal sample.
- Added public draft page `pages/story-pack-v1.html` and linked it from `pages/index.html`.
- Updated `README.md` to index story-pack spec/schema/sample and current build focus.
- Added local validation script `scripts/validate-story-pack.py`.
- Added tests `tests/test_validate_story_pack.py` (valid pack, invalid pack, missing pack file).

#### Verification

- `python -m unittest tests/test_validate_story_pack.py -v` -> pass (3 tests).
- `python scripts/validate-story-pack.py documents/story-pack-v1.minimal.json` -> validation passed.
- Lint checks for edited files -> no linter errors.

#### Story-Pack Decisions

- Keep both human-facing spec (`story-pack-v1-spec.md`) and machine-facing schema (`story-pack-v1.schema.json`) in sync.
- Treat `.vscode/` as local editor config and ignore it via `.gitignore`.

#### Story-Pack Next

- Add ID cross-reference checks (event/encounter/scene existence) in a higher-level validator layer.
- Optionally wire schema validation into CI after local workflow stabilizes.

### Session Update (Cross-Reference Validator)

#### Validator Completed

- Extended `scripts/validate-story-pack.py` with cross-reference validation after schema pass.
- Added checks for:
  - `events.events[*].outcomes[*].payload.encounterId` -> existing encounter IDs
  - `encounters.encounters[*].enemyWave[*]` -> existing enemy template IDs
  - `events.events[*].trigger.sourceId` when `type=enter_location` -> existing location IDs
- Expanded test coverage in `tests/test_validate_story_pack.py` from 3 to 6 cases.

#### Validator Verification

- `python -m unittest tests/test_validate_story_pack.py -v` -> pass (6 tests).

#### Validator Decisions

- Deferred strict `sceneId` existence check until a canonical `scenes` registry field is defined in schema/spec.

#### Validator Next

- If `world.scenes` (or equivalent) is introduced, add `sceneId` cross-reference validation and tests.

### Session Update (Runtime Entry Implementation)

#### Runtime Completed

- Added runtime package:
  - `runtime/__init__.py`
  - `runtime/story_pack.py`
- Implemented `load_story_pack(pack_path, schema_path)` as a reusable business entrypoint.
- Added `StoryPack` data wrapper with query helpers:
  - `get_event(event_id)`
  - `get_encounter(encounter_id)`
- Refactored `scripts/validate-story-pack.py` to consume runtime API instead of duplicating validation logic.

#### Runtime Verification

- `python -m unittest tests/test_validate_story_pack.py tests/test_story_pack_runtime.py -v` -> pass (9 tests).
- `python scripts/validate-story-pack.py documents/story-pack-v1.minimal.json` -> validation passed.

#### Runtime Decisions

- Treat runtime loader (`runtime/story_pack.py`) as the canonical place for schema + cross-reference validation logic.
- Keep CLI script as a thin wrapper around runtime code for consistency and lower maintenance.

#### Runtime Next

- Add orchestration helpers in runtime (e.g., next event candidates by trigger type).
- Introduce scene registry when schema is ready, then enforce `sceneId` cross-reference.

### Session Update (Event Trigger Selector)

#### Selector Completed

- Added `StoryPack.find_triggered_events(trigger_type, source_id, runtime_state)` in `runtime/story_pack.py`.
- Implemented runtime condition evaluation for operators:
  - `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`.
- Added runtime tests for trigger selection behavior in `tests/test_story_pack_runtime.py`.

#### Selector Verification

- `python -m unittest tests/test_story_pack_runtime.py -v` -> pass (5 tests).
- `python -m unittest tests/test_validate_story_pack.py -v` -> pass (6 tests).
- `python scripts/validate-story-pack.py documents/story-pack-v1.minimal.json` -> validation passed.

#### Selector Next

- Add deterministic event ordering policy (e.g., priority or declaration order contract).
- Extend state adapter to merge `questVariables` + `flags` defaults before evaluation.

### Session Update (Story-pack validation, encounter entry, docs)

#### Completed

- Added `StoryPack.can_enter_encounter(encounter_id, runtime_state)` in `runtime/story_pack.py` (reuses event condition evaluation for `entryCondition`).
- Extended `load_story_pack` validation: duplicate IDs within scoped lists; optional `world.scenes` registry with `encounters[].sceneId` cross-reference when non-empty.
- Added `world.scenes` to `documents/story-pack-v1.minimal.json` and documented optional `scenes` in `documents/story-pack-v1.schema.json`.
- Expanded tests: `tests/test_story_pack_runtime.py` (load errors, operators, `source_id=None`, `can_enter_encounter`); `tests/test_validate_story_pack.py` (duplicate event id, bad `sceneId`).
- Added root `requirements.txt` pinning `jsonschema` for reproducible installs.
- Aligned human-facing docs: `documents/story-pack-v1-spec.md` §2/§5/§7, `pages/story-pack-v1.html`, `README.md`.

#### Verification

- `python -m unittest tests/test_story_pack_runtime.py tests/test_validate_story_pack.py -v` -> pass (22 tests).
- `python scripts/validate-story-pack.py documents/story-pack-v1.minimal.json` -> validation passed.

#### Decisions

- Scene cross-reference is enforced only when `world.scenes` is a non-empty list; otherwise `sceneId` is not validated by reference tooling (engines may resolve scenes out-of-band).

#### Next

- Add deterministic event ordering policy for `find_triggered_events` return order.
- Optional: merge `state.flags` + `state.questVariables` in a small runtime adapter before condition evaluation.

### Session Update (Dual-layer rules retrieval foundation)

#### Completed

- Added `documents/rules-data-sources.md` to define:
  - approved upstream corpora (`oldmanumby/dnd.srd`, `5e-bits/5e-database`)
  - version honesty rules (`srd_5_1_omu` vs `srd_5_2_1`)
  - pinning/provenance policy and legal/safety engineering boundaries
- Added `rules_index/` package:
  - `chunking.py` (Markdown heading-stack chunking, stable `chunk_id`, JSONL + manifest export)
  - `storage.py` (SQLite `chunks` + external-content FTS5 + `bm25` search + rebuild)
  - `entities.py` (5e JSON snapshot ingest to SQLite + spell/monster/entity lookup APIs)
  - `router.py` (entity-first vs rules-first query routing)
  - `eval.py` (query-set loading, routing evaluation, recall@k helper)
- Added retrieval scripts:
  - `scripts/build-rules-index.py`
  - `scripts/import-5e-snapshot.py`
  - `scripts/eval-retrieval-routing.py`
- Added retrieval benchmark and fixtures:
  - `eval/queries.yaml`
  - `tests/fixtures/rules_md/*.md`
  - `tests/fixtures/5e_snapshot/{spells,monsters}/*.json`
- Added test coverage:
  - `tests/test_rules_chunking.py`
  - `tests/test_rules_fts.py`
  - `tests/test_rules_entities.py`
  - `tests/test_rules_router_eval.py`
- Added embedding defer decision record:
  - `documents/rules-retrieval-embedding-adr.md`
- Updated `AGENTS.md` and `README.md` for new directories, commands, and retrieval workflow.

#### Verification

- `python -m unittest tests/test_story_pack_runtime.py tests/test_validate_story_pack.py tests/test_rules_chunking.py tests/test_rules_fts.py tests/test_rules_entities.py tests/test_rules_router_eval.py -v` -> pass (32 tests).
- `python scripts/build-rules-index.py --source-root tests/fixtures/rules_md --source-system srd_5_1_omu --release fixture-v1 --db-path build/rules-test.sqlite --jsonl-path build/chunks-test.jsonl --manifest-path build/chunks-test.manifest.json` -> indexed chunks and generated artifacts.
- `python scripts/import-5e-snapshot.py --snapshot-root tests/fixtures/5e_snapshot --release fixture-v1 --db-path build/entities-test.sqlite` -> imported entities.
- `python scripts/eval-retrieval-routing.py --query-set eval/queries.yaml` -> routing accuracy 1.0 on current query set.

#### Decisions

- Keep lexical/structured dual path as default production retrieval baseline.
- Delay embedding/reranker integration until query-set volume and failure analysis justify added complexity.

#### Next

- Expand `eval/queries.yaml` toward >=50 production-like queries with expected retrieval targets.
- Add end-to-end retrieval integration at game runtime call sites once product UI flow is finalized.

### Session Update (Real upstream data validation)

#### Completed

- Cloned real upstream corpora into local `vendor/` for snapshot-only verification:
  - `vendor/dnd.srd` @ `f1424f9c9a2b73b80650db90e9ce208243fe0476`
  - `vendor/5e-database` @ `e6ac5584f60484c3a355a2e24bc559c2e318f5f4`
- Built real rules text index using `scripts/build-rules-index.py`:
  - `build/real-srd_chunks.sqlite`
  - `build/real-chunks.jsonl`
  - `build/real-chunks.manifest.json`
- Imported real 5e structured snapshot using `scripts/import-5e-snapshot.py`:
  - `build/real-entities.sqlite`
- Added importer hardening for real 5e-database shape:
  - dedupe on `(resource_type, index_key)` to avoid unique-key collisions
  - infer `resource_type` from locale-grouped filenames (for example `5e-SRD-Spells.json` -> `spells`)
- Added/updated tests in `tests/test_rules_entities.py` for both duplicate-index and locale-grouped file layouts.
- Added helper inspection script `scripts/inspect-entities-db.py` for quick DB sanity checks.

#### Verification

- `python scripts/build-rules-index.py --source-root vendor/dnd.srd --source-system srd_5_1_omu --release f1424f9c9a2b73b80650db90e9ce208243fe0476 --db-path build/real-srd_chunks.sqlite --jsonl-path build/real-chunks.jsonl --manifest-path build/real-chunks.manifest.json` -> indexed `3523` chunks from `1028` files.
- `python scripts/import-5e-snapshot.py --snapshot-root vendor/5e-database/src/2014 --release e6ac5584f60484c3a355a2e24bc559c2e318f5f4 --db-path build/real-entities.sqlite` -> imported `2027` entities.
- Real text retrieval samples (FTS/BM25) succeeded for:
  - `fireball`
  - `cover`
  - `actions in combat`
- Real entity lookup samples succeeded for:
  - spell `fireball`
  - monster `goblin`
- `python scripts/eval-retrieval-routing.py --query-set eval/queries.yaml` -> routing accuracy `1.0`.
- `python -m unittest tests/test_rules_entities.py -v` -> pass (4 tests).

#### Decisions

- Current implementation uses **two SQLite databases** for retrieval:
  - rules DB: chunks + FTS (`build/real-srd_chunks.sqlite`)
  - entities DB: structured lookup (`build/real-entities.sqlite`)
- Keep two-DB split for now (clear separation of concerns); optional future work can merge into one SQLite file with separate tables if operational simplicity is preferred.

#### Next

- Extend `eval/queries.yaml` with real-source expectations (chunk/resource targets) and track recall@k over time.
- Consider adding optional locale filter for entity import (`en` only by default) to reduce cross-locale ambiguity in deterministic lookups.

### Session Update (Session handoff hygiene)

#### Completed

- Updated `AGENTS.md` to include:
  - `scripts/`, `vendor/`, and `build/` in the repository map
  - explicit guidance to avoid accidental commits of local `vendor/` snapshots and generated `build/` artifacts unless explicitly requested
  - verification checklist item for staging hygiene on `vendor/` and `build/`
- Updated `.cursor/rules/agent-hard-constraints.mdc` with an always-on guardrail:
  - no committing local `vendor/` snapshots or generated `build/` artifacts unless explicitly requested

#### Decisions

- Treat `vendor/` and `build/` as local workflow surfaces by default, not release artifacts.
- Keep handoff safety rules close to both human-facing (`AGENTS.md`) and always-on (`.cursor/rules`) instructions.

#### Next

- In the next implementation session, scope whether `vendor/` should be ignored in `.gitignore` or managed via explicit fetch scripts and documented artifact policy.

---

## Update Template

Copy this block for new entries:

```md
## YYYY-MM-DD

### Goals
- ...

### Completed
- ...

### In Progress
- ...

### Decisions
- ...

### Next
- ...
```
