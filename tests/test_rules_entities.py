import tempfile
import unittest
from pathlib import Path

from rules_index.entities import EntityStore


REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = REPO_ROOT / "tests" / "fixtures" / "5e_snapshot"


class RulesEntitiesTests(unittest.TestCase):
    def test_ingest_and_lookup_entities(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "entities.sqlite"
            store = EntityStore(db_path)
            try:
                store.setup()
                ingested = store.ingest_json_snapshot(
                    snapshot_root=SNAPSHOT_ROOT,
                    source_release="5e-fixture-v1",
                )
                self.assertEqual(ingested, 2)

                fireball = store.get_spell("fireball")
                self.assertIsNotNone(fireball)
                self.assertEqual(fireball.payload["range"], "150 feet")

                goblin = store.get_monster("goblin")
                self.assertIsNotNone(goblin)
                self.assertEqual(goblin.payload["armor_class"], 15)
            finally:
                store.close()

    def test_search_spell_by_name(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "entities.sqlite"
            store = EntityStore(db_path)
            try:
                store.setup()
                store.ingest_json_snapshot(
                    snapshot_root=SNAPSHOT_ROOT,
                    source_release="5e-fixture-v1",
                )
                hits = store.search_by_name("spells", "fire", limit=3)
                self.assertEqual(len(hits), 1)
                self.assertEqual(hits[0].index_key, "fireball")
            finally:
                store.close()

    def test_ingest_snapshot_with_duplicate_index_keeps_latest_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            snapshot_root = tmp_root / "snapshot"
            spells_dir = snapshot_root / "spells"
            spells_dir.mkdir(parents=True)
            (spells_dir / "a.json").write_text(
                '{"index":"fireball","name":"Fireball","level":3}',
                encoding="utf-8",
            )
            (spells_dir / "b.json").write_text(
                '{"index":"fireball","name":"Fireball","level":4}',
                encoding="utf-8",
            )

            db_path = tmp_root / "entities.sqlite"
            store = EntityStore(db_path)
            try:
                store.setup()
                ingested = store.ingest_json_snapshot(
                    snapshot_root=snapshot_root,
                    source_release="dup-fixture",
                )
                self.assertEqual(ingested, 1)
                fireball = store.get_spell("fireball")
                self.assertIsNotNone(fireball)
                self.assertEqual(fireball.payload["level"], 4)
            finally:
                store.close()

    def test_ingest_locale_grouped_json_infers_resource_type_from_filename(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            snapshot_root = tmp_root / "snapshot" / "en"
            snapshot_root.mkdir(parents=True)
            (snapshot_root / "5e-SRD-Spells.json").write_text(
                '[{"index":"fireball","name":"Fireball","level":3}]',
                encoding="utf-8",
            )
            (snapshot_root / "5e-SRD-Monsters.json").write_text(
                '[{"index":"goblin","name":"Goblin","armor_class":15}]',
                encoding="utf-8",
            )

            db_path = tmp_root / "entities.sqlite"
            store = EntityStore(db_path)
            try:
                store.setup()
                ingested = store.ingest_json_snapshot(
                    snapshot_root=tmp_root / "snapshot",
                    source_release="locale-fixture",
                )
                self.assertEqual(ingested, 2)
                self.assertIsNotNone(store.get_spell("fireball"))
                self.assertIsNotNone(store.get_monster("goblin"))
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
