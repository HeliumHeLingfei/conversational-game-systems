#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rules_index.entities import EntityStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import 5e JSON snapshot into SQLite entity tables."
    )
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument("--release", type=str, required=True)
    parser.add_argument(
        "--db-path", type=Path, default=Path("build/entities.sqlite")
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.snapshot_root.exists():
        print(f"Snapshot root not found: {args.snapshot_root}")
        return 1

    store = EntityStore(args.db_path)
    try:
        store.setup()
        count = store.ingest_json_snapshot(args.snapshot_root, args.release)
    finally:
        store.close()

    print(f"Imported entities: {count} into {args.db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
