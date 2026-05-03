import json
import tempfile
import unittest
from pathlib import Path

import runtime.story_pack as story_pack_module
from runtime.story_pack import StoryPackValidationError, load_story_pack


REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_PACK_PATH = REPO_ROOT / "documents" / "story-pack-v1.minimal.json"
SCHEMA_PATH = REPO_ROOT / "documents" / "story-pack-v1.schema.json"


def _write_temp_pack(pack: dict):
    tmp_dir = tempfile.TemporaryDirectory()
    pack_path = Path(tmp_dir.name) / "pack.json"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")
    return pack_path, tmp_dir


class StoryPackRuntimeTests(unittest.TestCase):
    def test_load_story_pack_success(self):
        story_pack = load_story_pack(VALID_PACK_PATH, SCHEMA_PATH)
        self.assertEqual(story_pack.metadata["id"], "cgs.pack.emberfall_intro")
        self.assertEqual(len(story_pack.encounters), 1)

    def test_load_story_pack_pack_not_found(self):
        missing = REPO_ROOT / "documents" / "no-such-pack-xyz.json"
        with self.assertRaises(FileNotFoundError):
            load_story_pack(missing, SCHEMA_PATH)

    def test_load_story_pack_schema_not_found(self):
        missing_schema = REPO_ROOT / "documents" / "no-such-schema-xyz.json"
        with self.assertRaises(FileNotFoundError):
            load_story_pack(VALID_PACK_PATH, missing_schema)

    def test_load_story_pack_schema_validation_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_pack_path = Path(tmp_dir) / "bad.json"
            bad_pack_path.write_text("{}", encoding="utf-8")
            with self.assertRaises(StoryPackValidationError) as ctx:
                load_story_pack(bad_pack_path, SCHEMA_PATH)
            msg = str(ctx.exception)
        self.assertIn("Schema validation failed", msg)

    def test_invalid_cross_reference_raises_validation_error(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["events"]["events"][1]["outcomes"][0]["payload"]["encounterId"] = "enc_missing"

        with tempfile.TemporaryDirectory() as tmp_dir:
            invalid_pack_path = Path(tmp_dir) / "invalid-pack.json"
            invalid_pack_path.write_text(json.dumps(pack), encoding="utf-8")

            with self.assertRaises(StoryPackValidationError) as ctx:
                load_story_pack(invalid_pack_path, SCHEMA_PATH)

        self.assertIn("enc_missing", str(ctx.exception))

    def test_getters_return_expected_entities(self):
        story_pack = load_story_pack(VALID_PACK_PATH, SCHEMA_PATH)
        event = story_pack.get_event("ev_meet_captain")
        encounter = story_pack.get_encounter("enc_gate_skirmish")

        self.assertIsNotNone(event)
        self.assertIsNotNone(encounter)
        self.assertEqual(encounter["sceneId"], "scene_gate_square")

    def test_find_triggered_events_for_enter_location(self):
        story_pack = load_story_pack(VALID_PACK_PATH, SCHEMA_PATH)

        triggered = story_pack.find_triggered_events(
            trigger_type="enter_location",
            source_id="loc_gate",
            runtime_state={"metCaptainMarla": False},
        )

        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0]["id"], "ev_meet_captain")

    def test_find_triggered_events_source_id_none_does_not_filter_source(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["world"]["locations"].append(
            {
                "id": "loc_other",
                "name": "Other",
                "description": "Another place.",
            }
        )
        pack["events"]["events"].append(
            {
                "id": "ev_other_loc",
                "trigger": {"type": "enter_location", "sourceId": "loc_other"},
                "conditions": [],
                "outcomes": [
                    {"kind": "narrate", "payload": {"text": "You arrive elsewhere."}}
                ],
            }
        )

        pack_path, tmp_dir = _write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)

        story_pack = load_story_pack(pack_path, SCHEMA_PATH)
        triggered = story_pack.find_triggered_events(
            trigger_type="enter_location",
            source_id=None,
            runtime_state={},
        )
        ids = {e["id"] for e in triggered}
        self.assertEqual(ids, {"ev_meet_captain", "ev_other_loc"})

    def test_find_triggered_events_respects_conditions(self):
        story_pack = load_story_pack(VALID_PACK_PATH, SCHEMA_PATH)

        triggered = story_pack.find_triggered_events(
            trigger_type="state_threshold",
            source_id="raidersRepelled",
            runtime_state={"raidersRepelled": 0},
        )
        not_triggered = story_pack.find_triggered_events(
            trigger_type="state_threshold",
            source_id="raidersRepelled",
            runtime_state={"raidersRepelled": 1},
        )

        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0]["id"], "ev_start_gate_skirmish")
        self.assertEqual(not_triggered, [])

    def test_find_triggered_events_condition_operators(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        extras = [
            {
                "id": "ev_op_neq",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "n", "operator": "neq", "value": 1}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "neq"}}],
            },
            {
                "id": "ev_op_gt",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "x", "operator": "gt", "value": 2}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "gt"}}],
            },
            {
                "id": "ev_op_gte",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "x", "operator": "gte", "value": 3}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "gte"}}],
            },
            {
                "id": "ev_op_lt",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "x", "operator": "lt", "value": 5}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "lt"}}],
            },
            {
                "id": "ev_op_lte",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "x", "operator": "lte", "value": 4}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "lte"}}],
            },
            {
                "id": "ev_op_in",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "role", "operator": "in", "value": ["a", "b"]}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "in"}}],
            },
            {
                "id": "ev_op_not_in",
                "trigger": {"type": "manual", "sourceId": "op"},
                "conditions": [{"key": "role", "operator": "not_in", "value": ["x", "y"]}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "not_in"}}],
            },
        ]
        pack["events"]["events"] = pack["events"]["events"] + extras

        pack_path, tmp_dir = _write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)
        story_pack = load_story_pack(pack_path, SCHEMA_PATH)

        state = {"n": 2, "x": 4, "role": "a"}
        triggered = story_pack.find_triggered_events("manual", "op", state)
        ids = {e["id"] for e in triggered}
        self.assertEqual(
            ids,
            {
                "ev_op_neq",
                "ev_op_gt",
                "ev_op_gte",
                "ev_op_lt",
                "ev_op_lte",
                "ev_op_in",
                "ev_op_not_in",
            },
        )

    def test_find_triggered_events_gt_on_non_numeric_does_not_match(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["events"]["events"].append(
            {
                "id": "ev_bad_gt",
                "trigger": {"type": "manual", "sourceId": "m"},
                "conditions": [{"key": "x", "operator": "gt", "value": 1}],
                "outcomes": [{"kind": "narrate", "payload": {"text": "no"}}],
            }
        )
        pack_path, tmp_dir = _write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)
        story_pack = load_story_pack(pack_path, SCHEMA_PATH)
        self.assertEqual(
            story_pack.find_triggered_events("manual", "m", {"x": "not-a-number"}),
            [],
        )

    def test_unknown_operator_condition_evaluates_false(self):
        """Schema rejects unknown operators; runtime treats unknown as non-match if reached."""
        self.assertFalse(
            story_pack_module._condition_matches(
                {"key": "x", "operator": "bogus", "value": 1},
                {"x": 1},
            )
        )

    def test_can_enter_encounter_respects_entry_condition(self):
        story_pack = load_story_pack(VALID_PACK_PATH, SCHEMA_PATH)
        self.assertTrue(
            story_pack.can_enter_encounter(
                "enc_gate_skirmish", {"metCaptainMarla": True}
            )
        )
        self.assertFalse(
            story_pack.can_enter_encounter(
                "enc_gate_skirmish", {"metCaptainMarla": False}
            )
        )

    def test_can_enter_encounter_unknown_id_returns_false(self):
        story_pack = load_story_pack(VALID_PACK_PATH, SCHEMA_PATH)
        self.assertFalse(story_pack.can_enter_encounter("enc_missing", {}))


if __name__ == "__main__":
    unittest.main()
