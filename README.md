# Conversational Game Systems

AI-powered conversational game systems focused on interactive TTRPG experiences with a voice-enabled AI game master and 2D scene visualization.

This repository also serves as the business identity package for OPT self-employment activity under the sole proprietor name **Lingfei He**.

## Positioning

I am building and commercializing software systems that combine:

- Real-time speech input/output for player interaction
- LLM-based game-master orchestration and narrative control
- Structured world-state and encounter-state management
- 2D top-down scene and battle representation
- Story-pack driven gameplay workflows

## Services Offered

- AI product architecture and prototyping
- LLM/RAG integration and evaluation pipelines
- Voice interaction pipeline design
- Backend orchestration for agentic game flows
- Applied ML software consulting

## Repository Structure

- `pages/`: public landing page and printable product brief pages
- `pages/story-pack-v1.html`: published schema draft overview page
- `templates/`: reusable invoice and proposal templates
- `documents/story-pack-v1-spec.md`: full story-pack v1 draft specification
- `documents/story-pack-v1.schema.json`: machine-readable schema for validation
- `documents/story-pack-v1.minimal.json`: minimal valid sample pack
- `documents/rules-data-sources.md`: retrieval corpus source and pinning policy
- `rules_index/`: SQLite FTS5 chunk index + structured entity lookup modules
- `eval/queries.yaml`: routing benchmark query set
- `.cursor/rules/`: project rules for Cursor agent behavior
- `.agents/skills/`: project-scoped reusable agent workflows

## Current Build Focus

- Story-pack v1 draft schema published for engineering review
- Voice pipeline prototype for low-latency conversational play
- AI DM runtime loop covering narrative and encounter turns

## Local Story-Pack Validation

Install Python dependencies once:

```bash
pip install -r requirements.txt
```

Validate a pack against the draft schema:

```bash
python scripts/validate-story-pack.py documents/story-pack-v1.minimal.json
```

The validator performs:

- JSON Schema structure/type checks
- Duplicate ID checks within each scoped list (events, encounters, locations, factions, scenes, player archetypes, NPCs, enemy templates)
- Cross-reference checks (`start_encounter` -> encounter IDs, `enemyWave` -> enemy template IDs, `enter_location` -> location IDs; when `world.scenes` is non-empty, `encounters[].sceneId` -> scene IDs)

Use a custom schema path when needed:

```bash
python scripts/validate-story-pack.py <pack.json> --schema documents/story-pack-v1.schema.json
```

## Runtime (Early)

- `runtime/story_pack.py` provides `load_story_pack(...)` for reusable schema + cross-reference validation in business code.
- `StoryPack` includes baseline query helpers (`get_event`, `get_encounter`) for runtime orchestration wiring.
- `StoryPack.find_triggered_events(...)` filters events by trigger type/source and evaluates condition operators against runtime state (pass `source_id=None` to skip matching on `trigger.sourceId`).
- `StoryPack.can_enter_encounter(encounter_id, runtime_state)` evaluates an encounter's `entryCondition` list using the same condition operators as events.

## Rules Retrieval (Dual-Layer)

- Markdown rules corpus path: heading-based chunking with metadata (`source_system`, `file`, `heading_path`, `entity_type`, `entity_name`) and SQLite FTS5/BM25 ranking.
- Structured entity path: 5e JSON snapshots ingested into SQLite for exact spell/monster/entity lookup.
- Query routing path: entity-first for structured lookup intents, rules-first for open rule/adjudication questions.

Build a local rules index from markdown:

```bash
python scripts/build-rules-index.py --source-root <path-to-markdown-corpus> --source-system srd_5_1_omu --release <pinned-tag-or-commit>
```

Import a 5e JSON snapshot:

```bash
python scripts/import-5e-snapshot.py --snapshot-root <path-to-5e-json> --release <pinned-tag-or-commit>
```

Evaluate routing query set:

```bash
python scripts/eval-retrieval-routing.py --query-set eval/queries.yaml
```

## Contact

- Name: Lingfei He
- Email: `lingfeihe.dev@gmail.com`

## Email Signature Template

Copy and paste into Gmail signature settings:

```text
Lingfei He
ML Engineer | AI Software Developer
Founder, Conversational Game Systems
Email: lingfeihe.dev@gmail.com
GitHub: https://github.com/<your-username>
```

## GitHub Pages

After pushing this repository:

1. Open repository `Settings`
2. Go to `Pages`
3. Set source to branch `main` and folder `/pages`
4. Save and wait for deployment

## License

MIT License
