import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .router import RetrievalPlan, route_query


@dataclass(frozen=True)
class QueryCase:
    case_id: str
    query: str
    expected_mode: str
    expected_contains: str


def load_query_cases(path: Path) -> list[QueryCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases: list[QueryCase] = []
    for item in raw:
        cases.append(
            QueryCase(
                case_id=str(item["id"]),
                query=str(item["query"]),
                expected_mode=str(item["expected_mode"]),
                expected_contains=str(item["expected_contains"]),
            )
        )
    return cases


def evaluate_routing(cases: list[QueryCase]) -> dict[str, Any]:
    passed = 0
    results: list[dict[str, Any]] = []
    for case in cases:
        plan: RetrievalPlan = route_query(case.query)
        ok = plan.mode == case.expected_mode and case.expected_contains in plan.normalized_query
        if ok:
            passed += 1
        results.append(
            {
                "id": case.case_id,
                "query": case.query,
                "expected_mode": case.expected_mode,
                "actual_mode": plan.mode,
                "ok": ok,
            }
        )
    total = len(cases)
    return {
        "total": total,
        "passed": passed,
        "accuracy": (passed / total) if total else 0.0,
        "results": results,
    }


def recall_at_k(
    queries: list[dict[str, str]],
    search_fn: Callable[[str, int], list[str]],
    k: int,
) -> float:
    if not queries:
        return 0.0
    hit_count = 0
    for item in queries:
        query = item["query"]
        expected = item["expected"]
        hits = search_fn(query, k)
        if expected in hits:
            hit_count += 1
    return hit_count / len(queries)
