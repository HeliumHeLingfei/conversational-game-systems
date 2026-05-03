import unittest
from pathlib import Path

from rules_index.eval import evaluate_routing, load_query_cases, recall_at_k
from rules_index.router import route_query


REPO_ROOT = Path(__file__).resolve().parents[1]
QUERY_SET_PATH = REPO_ROOT / "eval" / "queries.yaml"


class RulesRouterEvalTests(unittest.TestCase):
    def test_route_query_entity_first_for_spell_query(self):
        plan = route_query("Spell fireball range and damage")
        self.assertEqual(plan.mode, "entity_first")
        self.assertEqual(plan.resource_type, "spells")

    def test_route_query_rules_first_for_open_rules_question(self):
        plan = route_query("How does cover work in combat?")
        self.assertEqual(plan.mode, "rules_first")
        self.assertTrue(plan.requires_rules_context)

    def test_evaluate_routing_query_set(self):
        cases = load_query_cases(QUERY_SET_PATH)
        report = evaluate_routing(cases)
        self.assertEqual(report["total"], 4)
        self.assertGreaterEqual(report["accuracy"], 0.75)

    def test_recall_at_k_helper(self):
        queries = [
            {"query": "fireball", "expected": "fireball"},
            {"query": "goblin", "expected": "goblin"},
        ]

        def fake_search(query: str, k: int) -> list[str]:
            if query == "fireball":
                return ["magic-missile", "fireball"][:k]
            return ["orc", "goblin"][:k]

        score = recall_at_k(queries, fake_search, k=2)
        self.assertEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
