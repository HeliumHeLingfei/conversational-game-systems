import subprocess
import sys
import tempfile
import unittest
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-story-pack.py"
SCHEMA_PATH = REPO_ROOT / "documents" / "story-pack-v1.schema.json"
VALID_PACK_PATH = REPO_ROOT / "documents" / "story-pack-v1.minimal.json"


class ValidateStoryPackScriptTests(unittest.TestCase):
    def run_script(self, pack_path: Path):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(pack_path),
                "--schema",
                str(SCHEMA_PATH),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

    def write_temp_pack(self, pack_obj):
        tmp_dir = tempfile.TemporaryDirectory()
        pack_path = Path(tmp_dir.name) / "pack.json"
        pack_path.write_text(json.dumps(pack_obj), encoding="utf-8")
        return tmp_dir, pack_path

    def test_valid_pack_returns_success(self):
        result = self.run_script(VALID_PACK_PATH)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Validation passed", result.stdout)

    def test_invalid_pack_returns_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            invalid_pack = Path(tmp_dir) / "invalid-pack.json"
            invalid_pack.write_text("{}", encoding="utf-8")

            result = self.run_script(invalid_pack)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Schema validation failed", result.stdout)

    def test_missing_pack_file_returns_failure(self):
        missing_path = REPO_ROOT / "documents" / "missing-pack.json"
        result = self.run_script(missing_path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Pack file not found", result.stdout)

    def test_start_encounter_must_reference_existing_encounter(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["events"]["events"][1]["outcomes"][0]["payload"]["encounterId"] = "enc_missing"
        tmp_dir, invalid_pack_path = self.write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)

        result = self.run_script(invalid_pack_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cross-reference failed", result.stdout)
        self.assertIn("enc_missing", result.stdout)

    def test_enemy_wave_ids_must_exist_in_enemy_templates(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["encounters"]["encounters"][0]["enemyWave"] = ["e_not_found"]
        tmp_dir, invalid_pack_path = self.write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)

        result = self.run_script(invalid_pack_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cross-reference failed", result.stdout)
        self.assertIn("e_not_found", result.stdout)

    def test_enter_location_trigger_must_reference_existing_location(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["events"]["events"][0]["trigger"]["sourceId"] = "loc_missing"
        tmp_dir, invalid_pack_path = self.write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)

        result = self.run_script(invalid_pack_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cross-reference failed", result.stdout)
        self.assertIn("loc_missing", result.stdout)

    def test_duplicate_event_id_returns_failure(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        dup = json.loads(json.dumps(pack["events"]["events"][0]))
        dup["id"] = pack["events"]["events"][0]["id"]
        pack["events"]["events"].append(dup)

        tmp_dir, invalid_pack_path = self.write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)

        result = self.run_script(invalid_pack_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate id(s)", result.stdout)

    def test_scene_id_must_resolve_when_scenes_registry_present(self):
        pack = json.loads(VALID_PACK_PATH.read_text(encoding="utf-8"))
        pack["encounters"]["encounters"][0]["sceneId"] = "scene_unknown"

        tmp_dir, invalid_pack_path = self.write_temp_pack(pack)
        self.addCleanup(tmp_dir.cleanup)

        result = self.run_script(invalid_pack_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cross-reference failed", result.stdout)
        self.assertIn("scene_unknown", result.stdout)


if __name__ == "__main__":
    unittest.main()
