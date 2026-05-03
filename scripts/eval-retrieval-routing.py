#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rules_index.eval import evaluate_routing, load_query_cases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate retrieval router query set.")
    parser.add_argument(
        "--query-set", type=Path, default=Path("eval/queries.yaml")
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.query_set.exists():
        print(f"Query set not found: {args.query_set}")
        return 1
    cases = load_query_cases(args.query_set)
    report = evaluate_routing(cases)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["accuracy"] >= 0.7 else 2


if __name__ == "__main__":
    sys.exit(main())
