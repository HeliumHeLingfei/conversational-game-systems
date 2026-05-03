---
name: story-pack-spec
description: Define or refine a story-pack specification for the AI TTRPG product. Use when the user asks about story-pack schema, narrative runtime fields, encounter data, or pack validation rules.
---

# Story Pack Spec

Use this skill when evolving the content container format that powers playable sessions.

## Goals

- Keep story packs executable, not just descriptive text
- Ensure runtime state can be persisted and resumed
- Support narrative-to-battle transitions without ambiguity

## Required Output Sections

When drafting a spec, include:

1. `Metadata`: id, version, language, author, compatibility
2. `World`: setting, factions, key locations
3. `Actors`: player archetypes, NPC definitions, enemy templates
4. `State`: quest variables, inventory keys, flags, progression
5. `Events`: triggers, conditions, outcomes, side effects
6. `Encounters`: battle entry conditions, map scene id, turn config
7. `Validation`: required fields and schema-level constraints

## Workflow

1. Inspect existing product docs and current story assumptions.
2. Identify missing runtime-critical fields.
3. Propose a schema with explicit field names and data types.
4. Add at least one concrete pack example (minimal valid sample).
5. Call out backward-compatibility impact if the schema changes.

## Quality Bar

- No vague "magic behavior"; every trigger must be explicit.
- Narrative and combat state transitions must be traceable.
- The result must be implementable by engineering without extra interpretation.
