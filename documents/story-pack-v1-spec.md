# Story Pack v1 Specification (Draft)

## Purpose

This specification defines an executable story-pack format for Conversational Game Systems.  
The format is designed to support:

- narrative session runtime orchestration
- persistent and resumable state
- explicit narrative-to-encounter transitions

This is a draft baseline for implementation and validation tooling.

Companion artifacts:

- `documents/story-pack-v1.schema.json` (machine-readable validation schema)
- `documents/story-pack-v1.minimal.json` (minimal valid sample pack)

## 1. Metadata

Required fields:

- `id` (string): globally unique pack identifier, e.g. `cgs.pack.emberfall_intro`
- `version` (string): semantic version for the pack content, e.g. `1.0.0`
- `language` (string): BCP-47 tag, e.g. `en-US`
- `author` (string): creator or studio name
- `compatibility` (object):
  - `minRuntimeVersion` (string)
  - `maxRuntimeVersion` (string, optional)

## 2. World

Required fields:

- `setting` (object):
  - `title` (string)
  - `tone` (string)
  - `summary` (string)
- `factions` (array of objects):
  - `id` (string)
  - `name` (string)
  - `stance` (string; one of `ally`, `neutral`, `hostile`)
- `locations` (array of objects):
  - `id` (string)
  - `name` (string)
  - `description` (string)
- `scenes` (array of objects, optional): tactical scene registry for encounter `sceneId` resolution
  - `id` (string)
  - `name` (string)
  - `description` (string)

## 3. Actors

Required fields:

- `playerArchetypes` (array of objects):
  - `id` (string)
  - `label` (string)
  - `starterStats` (object of number values)
  - `starterInventory` (array of string item IDs)
- `npcs` (array of objects):
  - `id` (string)
  - `name` (string)
  - `role` (string)
  - `dialogueStyle` (string)
- `enemyTemplates` (array of objects):
  - `id` (string)
  - `name` (string)
  - `baseStats` (object of number values)
  - `abilities` (array of strings)

## 4. State

Required fields:

- `questVariables` (object): key-value runtime variables (`string | number | boolean`)
- `inventoryKeys` (array of strings): canonical item keys expected in runtime inventory
- `flags` (object of booleans): binary progression and world-state switches
- `progression` (object):
  - `currentChapter` (string)
  - `milestones` (array of string milestone IDs)

## 5. Events

Required fields:

- `events` (array of objects):
  - `id` (string)
  - `trigger` (object):
    - `type` (string; `enter_location`, `dialogue_choice`, `state_threshold`, `manual`)
    - `sourceId` (string, optional): when querying triggered events at runtime, passing `source_id=None` matches any `sourceId` (filter disabled for that dimension)
  - `conditions` (array of objects):
    - `key` (string)
    - `operator` (string; `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`)
    - `value` (string | number | boolean)
  - `outcomes` (array of objects):
    - `kind` (string; `set_flag`, `set_variable`, `grant_item`, `start_encounter`, `narrate`)
    - `payload` (object)
  - `sideEffects` (array of strings, optional): human-readable audit notes

## 6. Encounters

Required fields:

- `encounters` (array of objects):
  - `id` (string)
  - `entryCondition` (array of condition objects; same shape as event conditions)
  - `sceneId` (string): tactical map scene reference; when `world.scenes` is present and non-empty, it must match a scene `id` in that registry (see §7)
  - `turnConfig` (object):
    - `initiativeMode` (string; `speed`, `round_robin`, `scripted`)
    - `maxRounds` (number)
  - `enemyWave` (array of enemy template IDs)

## 7. Validation Rules

### 7.1 JSON Schema (structure and enums)

1. Top-level required keys: `metadata`, `world`, `actors`, `state`, `events`, `encounters`.
2. IDs in schema-valid objects must be non-empty strings where the schema marks them required.
3. `compatibility.minRuntimeVersion` must be present.
4. Unknown top-level keys should be allowed but ignored by default (forward-compatible parser behavior).

### 7.2 Runtime / CLI (`load_story_pack`, `scripts/validate-story-pack.py`)

After schema validation, the reference implementation additionally enforces:

1. **Duplicate IDs** (within each list scope): `events.events`, `encounters.encounters`, `world.factions`, `world.locations`, `world.scenes` (if present), `actors.playerArchetypes`, `actors.npcs`, `actors.enemyTemplates`.
2. **Cross-references**
   - `trigger.type = enter_location` → `trigger.sourceId` exists in `world.locations[].id`
   - `outcomes[].kind = start_encounter` → `payload.encounterId` exists in `encounters.encounters[].id`
   - `encounters.encounters[].enemyWave[]` → each id exists in `actors.enemyTemplates[].id`
   - **Scenes:** if `world.scenes` is a non-empty array, each `encounters.encounters[].sceneId` must exist in `world.scenes[].id`. If `world.scenes` is absent or empty, scene cross-reference is **not** enforced (packs may still ship `sceneId` for engines that resolve scenes elsewhere).

### 7.3 Planned / not yet enforced in reference tooling

- NPC / item / dialogue graph references beyond the checks in §7.2
- Merging nested `state.flags` / `state.questVariables` into a single evaluation map inside `load_story_pack` (callers may merge before calling `find_triggered_events` / `can_enter_encounter`)

## 8. Minimal Valid Example

```json
{
  "metadata": {
    "id": "cgs.pack.emberfall_intro",
    "version": "1.0.0",
    "language": "en-US",
    "author": "Conversational Game Systems",
    "compatibility": {
      "minRuntimeVersion": "0.1.0"
    }
  },
  "world": {
    "setting": {
      "title": "Emberfall Outpost",
      "tone": "grim-hopeful",
      "summary": "A frontier outpost under pressure from raiders."
    },
    "factions": [
      { "id": "f_outpost", "name": "Outpost Watch", "stance": "ally" },
      { "id": "f_ashclaw", "name": "Ashclaw Raiders", "stance": "hostile" }
    ],
    "locations": [
      {
        "id": "loc_gate",
        "name": "North Gate",
        "description": "Main gate and defensive rampart."
      }
    ],
    "scenes": [
      {
        "id": "scene_gate_square",
        "name": "Gate Square",
        "description": "Tactical encounter space outside the north gate."
      }
    ]
  },
  "actors": {
    "playerArchetypes": [
      {
        "id": "a_vanguard",
        "label": "Vanguard",
        "starterStats": { "hp": 24, "atk": 6, "def": 4 },
        "starterInventory": ["it_bandage"]
      }
    ],
    "npcs": [
      {
        "id": "npc_marla",
        "name": "Captain Marla",
        "role": "quest_giver",
        "dialogueStyle": "direct"
      }
    ],
    "enemyTemplates": [
      {
        "id": "e_raider_scout",
        "name": "Raider Scout",
        "baseStats": { "hp": 12, "atk": 4, "def": 2 },
        "abilities": ["quick_strike"]
      }
    ]
  },
  "state": {
    "questVariables": { "raidersRepelled": 0 },
    "inventoryKeys": ["it_bandage", "it_gate_key"],
    "flags": { "metCaptainMarla": false, "northGateSecured": false },
    "progression": {
      "currentChapter": "chapter_1",
      "milestones": []
    }
  },
  "events": {
    "events": [
      {
        "id": "ev_meet_captain",
        "trigger": { "type": "enter_location", "sourceId": "loc_gate" },
        "conditions": [],
        "outcomes": [
          {
            "kind": "set_flag",
            "payload": { "key": "metCaptainMarla", "value": true }
          },
          {
            "kind": "narrate",
            "payload": { "text": "Captain Marla briefs your first defense." }
          }
        ]
      },
      {
        "id": "ev_start_gate_skirmish",
        "trigger": { "type": "state_threshold", "sourceId": "raidersRepelled" },
        "conditions": [{ "key": "raidersRepelled", "operator": "eq", "value": 0 }],
        "outcomes": [
          {
            "kind": "start_encounter",
            "payload": { "encounterId": "enc_gate_skirmish" }
          }
        ]
      }
    ]
  },
  "encounters": {
    "encounters": [
      {
        "id": "enc_gate_skirmish",
        "entryCondition": [
          { "key": "metCaptainMarla", "operator": "eq", "value": true }
        ],
        "sceneId": "scene_gate_square",
        "turnConfig": {
          "initiativeMode": "speed",
          "maxRounds": 8
        },
        "enemyWave": ["e_raider_scout"]
      }
    ]
  }
}
```

## 9. Backward Compatibility Notes

- Runtime parsers should ignore unknown fields to allow additive evolution.
- Breaking changes must increment major version in `metadata.version`.
- Pack migration tooling should be introduced before v2 schema rollout.
