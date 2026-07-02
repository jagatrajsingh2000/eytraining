import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"


def _tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return set().union(*(_tokens(item) for item in value))
    if isinstance(value, dict):
        return set().union(*(_tokens(item) for item in value.values()))
    return set(re.findall(r"[a-z0-9_]+", str(value).lower()))


@lru_cache(maxsize=1)
def load_knowledge() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            items.extend(data)
        elif isinstance(data, dict):
            items.append(data)
    return items


def _state_query_tokens(state: dict[str, Any]) -> set[str]:
    fields = [
        state.get("meal_text"),
        state.get("meal_type"),
        state.get("goal"),
        state.get("goals"),
        state.get("diet_type"),
        state.get("health_conditions"),
        state.get("deficiencies"),
        state.get("supplements"),
        state.get("meal_analysis"),
        state.get("risk_flags"),
        state.get("day_meals"),
    ]
    return set().union(*(_tokens(field) for field in fields))


def _score_item(item: dict[str, Any], query_tokens: set[str], state: dict[str, Any]) -> int:
    diet_type = state.get("diet_type")
    item_diet_types = set(item.get("diet_types") or [])
    if diet_type and item_diet_types and diet_type not in item_diet_types:
        return 0

    item_tags = _tokens(item.get("tags"))
    if item.get("evidence_level") == "traditional_ayurveda":
        generic_ayurveda_tags = {"ayurveda", "viruddha", "viruddha_ahara", "traditional_context"}
        specific_tags = item_tags - generic_ayurveda_tags
        if not query_tokens & specific_tags:
            return 0

    item_tokens = _tokens(
        [
            item.get("topic"),
            item.get("goals"),
            item.get("diet_types"),
            item.get("conditions"),
            item.get("tags"),
            item.get("content"),
        ]
    )
    score = len(query_tokens & item_tokens)

    state_goals = set(state.get("goals") or ([state.get("goal")] if state.get("goal") else []))
    if state_goals & set(item.get("goals") or []):
        score += 5

    if diet_type and diet_type in item_diet_types:
        score += 4

    conditions = set((state.get("health_conditions") or []) + (state.get("deficiencies") or []))
    if conditions & set(item.get("conditions") or []):
        score += 5

    if item.get("evidence_level") == "traditional_ayurveda":
        ayurveda_markers = {"ayurveda", "ayurvedic", "viruddha", "viruddha_ahara"}
        if query_tokens & ayurveda_markers or query_tokens & item_tags:
            score += 2

    return score


def retrieve_nutrition_context(state: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    query_tokens = _state_query_tokens(state)
    ranked = []
    for item in load_knowledge():
        score = _score_item(item, query_tokens, state)
        if score > 0:
            ranked.append((score, item))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {
            "id": item.get("id"),
            "topic": item.get("topic"),
            "content": item.get("content"),
            "source": item.get("source"),
            "evidence_level": item.get("evidence_level"),
            "safety": item.get("safety"),
        }
        for _, item in ranked[:limit]
    ]


def retrieve_health_context(query: str) -> list[str]:
    context = retrieve_nutrition_context({"meal_text": query})
    return [item["content"] for item in context]
