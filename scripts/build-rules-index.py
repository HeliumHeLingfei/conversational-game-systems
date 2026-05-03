#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rules_index.chunking import ingest_markdown_tree, write_chunks_jsonl, write_manifest
from rules_index.storage import RuleIndexStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build heading-based rule chunks and SQLite FTS5 index."
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-system", type=str, required=True)
    parser.add_argument("--release", type=str, required=True)
    parser.add_argument(
        "--db-path", type=Path, default=Path("build/srd_chunks.sqlite")
    )
    parser.add_argument(
        "--jsonl-path", type=Path, default=Path("build/chunks.jsonl")
    )
    parser.add_argument(
        "--manifest-path", type=Path, default=Path("build/chunks.manifest.json")
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.source_root.exists():
        print(f"Source root not found: {args.source_root}")
        return 1

    chunks = ingest_markdown_tree(
        source_root=args.source_root,
        source_system=args.source_system,
        commit_or_release=args.release,
    )
    write_chunks_jsonl(chunks, args.jsonl_path)
    manifest = write_manifest(
        chunks=chunks,
        source_root=args.source_root,
        source_system=args.source_system,
        commit_or_release=args.release,
        output_path=args.manifest_path,
    )

    store = RuleIndexStore(args.db_path)
    try:
        store.setup()
        store.replace_chunks(chunks)
    finally:
        store.close()

    print(
        "Indexed chunks:",
        manifest["chunk_count"],
        "| files:",
        manifest["file_count"],
        "| db:",
        args.db_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
