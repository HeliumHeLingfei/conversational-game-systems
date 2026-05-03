#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.story_pack import StoryPackValidationError, load_story_pack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Story Pack JSON file against a JSON Schema."
    )
    parser.add_argument("pack", type=Path, help="Path to story-pack JSON file.")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("documents/story-pack-v1.schema.json"),
        help="Path to schema JSON file (default: documents/story-pack-v1.schema.json).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pack_path = args.pack
    schema_path = args.schema

    if not pack_path.exists():
        print(f"Pack file not found: {pack_path}")
        return 1

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return 1

    try:
        load_story_pack(pack_path, schema_path)
    except (FileNotFoundError, StoryPackValidationError, ValueError) as exc:
        print(str(exc))
        return 1

    print(f"Validation passed: {pack_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
