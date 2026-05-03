import json
import tempfile
import unittest
from pathlib import Path

from rules_index.chunking import (
    ingest_markdown_tree,
    write_chunks_jsonl,
    write_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "rules_md"


class RulesChunkingTests(unittest.TestCase):
    def test_ingest_markdown_tree_builds_heading_chunks(self):
        chunks = ingest_markdown_tree(
            source_root=FIXTURE_ROOT,
            source_system="srd_5_1_omu",
            commit_or_release="fixture-v1",
        )
        self.assertGreaterEqual(len(chunks), 6)
        first = chunks[0]
        self.assertEqual(first.source_system, "srd_5_1_omu")
        self.assertIn(first.heading_path, {"Gameplay", "Spells"})
        self.assertTrue(first.chunk_id)

    def test_jsonl_and_manifest_export(self):
        chunks = ingest_markdown_tree(
            source_root=FIXTURE_ROOT,
            source_system="srd_5_1_omu",
            commit_or_release="fixture-v1",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            jsonl_path = tmp_path / "chunks.jsonl"
            manifest_path = tmp_path / "manifest.json"
            write_chunks_jsonl(chunks, jsonl_path)
            manifest = write_manifest(
                chunks=chunks,
                source_root=FIXTURE_ROOT,
                source_system="srd_5_1_omu",
                commit_or_release="fixture-v1",
                output_path=manifest_path,
            )

            lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), len(chunks))
            parsed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed_manifest["chunk_count"], len(chunks))
            self.assertEqual(manifest["file_count"], 2)


if __name__ == "__main__":
    unittest.main()
