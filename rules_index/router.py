import re
from dataclasses import dataclass
from typing import Any


ENTITY_HINTS: dict[str, tuple[str, ...]] = {
    "spells": ("spell", "cantrip"),
    "monsters": ("monster", "creature", "stat block", "ac", "hit points"),
    "classes": ("class", "subclass"),
    "equipment": ("equipment", "item", "weapon", "armor"),
}

RULES_HINTS = ("rule", "how does", "when can", "combat", "condition", "adjudicate")


@dataclass(frozen=True)
class RetrievalPlan:
    mode: str
    resource_type: str | None
    normalized_query: str
    requires_rules_context: bool


def _contains_hint(text: str, hint: str) -> bool:
    if " " in hint:
        return hint in text
    return re.search(rf"\b{re.escape(hint)}\b", text) is not None


def route_query(text: str, session_flags: dict[str, Any] | None = None) -> RetrievalPlan:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    session_flags = session_flags or {}
    requires_rules_context = any(token in normalized for token in RULES_HINTS)

    for resource_type, hints in ENTITY_HINTS.items():
        if any(_contains_hint(normalized, hint) for hint in hints):
            return RetrievalPlan(
                mode="entity_first",
                resource_type=resource_type,
                normalized_query=normalized,
                requires_rules_context=requires_rules_context,
            )

    if session_flags.get("in_combat"):
        return RetrievalPlan(
            mode="rules_first",
            resource_type=None,
            normalized_query=f"combat {normalized}".strip(),
            requires_rules_context=True,
        )

    return RetrievalPlan(
        mode="rules_first",
        resource_type=None,
        normalized_query=normalized,
        requires_rules_context=requires_rules_context,
    )
