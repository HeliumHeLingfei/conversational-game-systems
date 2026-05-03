import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class StoryPackValidationError(Exception):
    pass


@dataclass
class StoryPack:
    data: dict[str, Any]

    @property
    def metadata(self) -> dict[str, Any]:
        return self.data["metadata"]

    @property
    def encounters(self) -> list[dict[str, Any]]:
        return self.data["encounters"]["encounters"]

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        for event in self.data["events"]["events"]:
            if event.get("id") == event_id:
                return event
        return None

    def get_encounter(self, encounter_id: str) -> dict[str, Any] | None:
        for encounter in self.encounters:
            if encounter.get("id") == encounter_id:
                return encounter
        return None

    def find_triggered_events(
        self, trigger_type: str, source_id: str | None, runtime_state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        triggered_events: list[dict[str, Any]] = []

        for event in self.data["events"]["events"]:
            trigger = event.get("trigger", {})
            if not isinstance(trigger, dict):
                continue
            if trigger.get("type") != trigger_type:
                continue
            if source_id is not None and trigger.get("sourceId") != source_id:
                continue
            if not _conditions_match(event.get("conditions", []), runtime_state):
                continue
            triggered_events.append(event)

        return triggered_events

    def can_enter_encounter(self, encounter_id: str, runtime_state: dict[str, Any]) -> bool:
        """Return True if encounter exists and its entryCondition list matches runtime_state.

        Conditions use the same shape and operators as event conditions. The runtime_state
        dict is a flat key-value map (orchestration may merge flags/questVariables upstream).
        """
        encounter = self.get_encounter(encounter_id)
        if encounter is None:
            return False
        entry = encounter.get("entryCondition", [])
        if not isinstance(entry, list):
            return False
        return _conditions_match(entry, runtime_state)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _format_json_path(path_parts: list[Any]) -> str:
    return ".".join(str(part) for part in path_parts) or "<root>"


def _condition_matches(condition: dict[str, Any], runtime_state: dict[str, Any]) -> bool:
    key = condition.get("key")
    operator = condition.get("operator")
    expected = condition.get("value")
    actual = runtime_state.get(key)

    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "gt":
        return isinstance(actual, (int, float)) and actual > expected
    if operator == "gte":
        return isinstance(actual, (int, float)) and actual >= expected
    if operator == "lt":
        return isinstance(actual, (int, float)) and actual < expected
    if operator == "lte":
        return isinstance(actual, (int, float)) and actual <= expected
    if operator == "in":
        return isinstance(expected, list) and actual in expected
    if operator == "not_in":
        return isinstance(expected, list) and actual not in expected
    return False


def _conditions_match(conditions: list[dict[str, Any]], runtime_state: dict[str, Any]) -> bool:
    for condition in conditions:
        if not isinstance(condition, dict):
            return False
        if not _condition_matches(condition, runtime_state):
            return False
    return True


def _validate_cross_references(pack: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    encounter_ids = {
        entry.get("id")
        for entry in pack.get("encounters", {}).get("encounters", [])
        if isinstance(entry, dict)
    }
    enemy_template_ids = {
        entry.get("id")
        for entry in pack.get("actors", {}).get("enemyTemplates", [])
        if isinstance(entry, dict)
    }
    location_ids = {
        entry.get("id")
        for entry in pack.get("world", {}).get("locations", [])
        if isinstance(entry, dict)
    }

    scene_registry = _scene_id_registry(pack.get("world", {}))

    for event_index, event in enumerate(pack.get("events", {}).get("events", [])):
        if not isinstance(event, dict):
            continue

        trigger = event.get("trigger", {})
        if isinstance(trigger, dict) and trigger.get("type") == "enter_location":
            source_id = trigger.get("sourceId")
            if source_id and source_id not in location_ids:
                issues.append(
                    f"events.events[{event_index}].trigger.sourceId references "
                    f"missing location id '{source_id}'"
                )

        for outcome_index, outcome in enumerate(event.get("outcomes", [])):
            if not isinstance(outcome, dict):
                continue
            if outcome.get("kind") != "start_encounter":
                continue

            payload = outcome.get("payload", {})
            encounter_id = payload.get("encounterId") if isinstance(payload, dict) else None
            if encounter_id and encounter_id not in encounter_ids:
                issues.append(
                    f"events.events[{event_index}].outcomes[{outcome_index}].payload."
                    f"encounterId references missing encounter id '{encounter_id}'"
                )

    for encounter_index, encounter in enumerate(pack.get("encounters", {}).get("encounters", [])):
        if not isinstance(encounter, dict):
            continue

        scene_id = encounter.get("sceneId")
        if scene_registry is not None and isinstance(scene_id, str) and scene_id:
            if scene_id not in scene_registry:
                issues.append(
                    f"encounters.encounters[{encounter_index}].sceneId references "
                    f"missing scene id '{scene_id}'"
                )

        for wave_index, enemy_id in enumerate(encounter.get("enemyWave", [])):
            if enemy_id not in enemy_template_ids:
                issues.append(
                    f"encounters.encounters[{encounter_index}].enemyWave[{wave_index}] "
                    f"references missing enemy template id '{enemy_id}'"
                )

    return issues


def _scene_id_registry(world: dict[str, Any]) -> set[str] | None:
    """If world.scenes is a non-empty list of objects with id, return those ids; else None (skip scene xref)."""
    raw = world.get("scenes")
    if not isinstance(raw, list) or not raw:
        return None
    ids: set[str] = set()
    for entry in raw:
        if isinstance(entry, dict):
            sid = entry.get("id")
            if isinstance(sid, str) and sid:
                ids.add(sid)
    return ids or None


def _validate_duplicate_ids(pack: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    def check(entries: Any, label: str) -> None:
        if not isinstance(entries, list):
            return
        seen: dict[str, int] = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            entry_id = entry.get("id")
            if not isinstance(entry_id, str) or not entry_id:
                continue
            if entry_id in seen:
                issues.append(
                    f"{label}: duplicate id '{entry_id}' at index {index} "
                    f"(first at index {seen[entry_id]})"
                )
            else:
                seen[entry_id] = index

    world = pack.get("world", {})
    if isinstance(world, dict):
        check(world.get("factions", []), "world.factions")
        check(world.get("locations", []), "world.locations")
        check(world.get("scenes", []), "world.scenes")

    actors = pack.get("actors", {})
    if isinstance(actors, dict):
        check(actors.get("playerArchetypes", []), "actors.playerArchetypes")
        check(actors.get("npcs", []), "actors.npcs")
        check(actors.get("enemyTemplates", []), "actors.enemyTemplates")

    events_obj = pack.get("events", {})
    if isinstance(events_obj, dict):
        check(events_obj.get("events", []), "events.events")

    enc_obj = pack.get("encounters", {})
    if isinstance(enc_obj, dict):
        check(enc_obj.get("encounters", []), "encounters.encounters")

    return issues


def load_story_pack(pack_path: Path | str, schema_path: Path | str) -> StoryPack:
    pack_path = Path(pack_path)
    schema_path = Path(schema_path)

    if not pack_path.exists():
        raise FileNotFoundError(f"Pack file not found: {pack_path}")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema = _load_json(schema_path)
    pack = _load_json(pack_path)

    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(pack), key=lambda error: list(error.path))
    if schema_errors:
        message_lines = [f"Schema validation failed: {len(schema_errors)} error(s)"]
        for idx, error in enumerate(schema_errors, start=1):
            message_lines.append(
                f"{idx}. {_format_json_path(list(error.path))}: {error.message}"
            )
        raise StoryPackValidationError("\n".join(message_lines))

    duplicate_issues = _validate_duplicate_ids(pack)
    if duplicate_issues:
        message_lines = [f"Duplicate id(s): {len(duplicate_issues)} issue(s)"]
        for idx, issue in enumerate(duplicate_issues, start=1):
            message_lines.append(f"{idx}. {issue}")
        raise StoryPackValidationError("\n".join(message_lines))

    cross_ref_issues = _validate_cross_references(pack)
    if cross_ref_issues:
        message_lines = [f"Cross-reference failed: {len(cross_ref_issues)} issue(s)"]
        for idx, issue in enumerate(cross_ref_issues, start=1):
            message_lines.append(f"{idx}. {issue}")
        raise StoryPackValidationError("\n".join(message_lines))

    return StoryPack(data=pack)
