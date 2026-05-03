#!/usr/bin/env python
import argparse
import sqlite3
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect entities SQLite database.")
    parser.add_argument("db_path", type=Path)
    parser.add_argument("--name", type=str, default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.db_path.exists():
        print(f"DB not found: {args.db_path}")
        return 1
    conn = sqlite3.connect(str(args.db_path))
    cur = conn.cursor()
    top = cur.execute(
        "SELECT resource_type, count(1) FROM entities GROUP BY resource_type ORDER BY count(1) DESC LIMIT 20"
    ).fetchall()
    print("top_resource_types=", top)
    if args.name:
        rows = cur.execute(
            "SELECT resource_type, index_key, name FROM entities WHERE lower(name)=lower(?) LIMIT 20",
            (args.name,),
        ).fetchall()
        print(f"name_lookup[{args.name}]=", rows)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
