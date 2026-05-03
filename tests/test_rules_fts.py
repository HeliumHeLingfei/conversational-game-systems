import tempfile
import unittest
from pathlib import Path

from rules_index.chunking import ingest_markdown_tree
from rules_index.storage import RuleIndexStore


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "rules_md"


class RulesFtsTests(unittest.TestCase):
    def test_fts_search_returns_ranked_hits(self):
        chunks = ingest_markdown_tree(
            source_root=FIXTURE_ROOT,
            source_system="srd_5_1_omu",
            commit_or_release="fixture-v1",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "rules.sqlite"
            store = RuleIndexStore(db_path)
            try:
                store.setup()
                store.replace_chunks(chunks)
                hits = store.search("fireball", limit=3)
                self.assertGreaterEqual(len(hits), 1)
                self.assertIn("Fireball", hits[0].heading_path)

                combat_hits = store.search("combat", entity_type="rule_section", limit=5)
                self.assertGreaterEqual(len(combat_hits), 1)
            finally:
                store.close()

    def test_rebuild_is_idempotent(self):
        chunks = ingest_markdown_tree(
            source_root=FIXTURE_ROOT,
            source_system="srd_5_1_omu",
            commit_or_release="fixture-v1",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "rules.sqlite"
            store = RuleIndexStore(db_path)
            try:
                store.setup()
                store.replace_chunks(chunks)
                first = store.search("cover", limit=5)
                store.rebuild_fts()
                second = store.search("cover", limit=5)
                self.assertEqual([h.chunk_id for h in first], [h.chunk_id for h in second])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
