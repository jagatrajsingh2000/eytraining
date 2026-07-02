from typing import Dict, Any
import logging

from app.llm.provider_chain import LLMProviderChainError, generate_json_with_provider_fallback
from app.observability.langsmith import traceable

logger = logging.getLogger("nutriguard.orchestrator.meal_analyzer")

def _fallback_meal_analysis(meal_text: str) -> Dict[str, Any]:
    foods = []
    beverages = []
    carb_sources = []
    protein_sources = []

    lowered = meal_text.lower()
    if "poha" in lowered:
        foods.append("poha")
        carb_sources.append("poha")
    if "tea" in lowered:
        foods.append("tea")
        beverages.append("tea")

    return {
        "foods": foods,
        "carb_sources": carb_sources,
        "protein_sources": protein_sources,
        "beverages": beverages,
        "possible_issues": ["breakfast appears low in protein"],
    }


@traceable(name="Meal Analyzer Agent", run_type="chain")
def meal_analyzer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    meal_text = state.get("meal_text", "")

    prompt = f"""
You are the Meal Analyzer Agent for NutriGuard.

Convert the user's meal text into structured food data.
Do not give medical advice.
Return only valid JSON with this shape:
{{
  "foods": ["food names"],
  "carb_sources": ["food names"],
  "protein_sources": ["food names"],
  "beverages": ["beverage names"],
  "possible_issues": ["short nutrition observations, no medical advice"]
}}

Meal text: {meal_text}
"""
    try:
        meal_analysis, metric_events = generate_json_with_provider_fallback(prompt, "meal_analyzer")
        state = {
            **state,
            "metric_events": [
                *(state.get("metric_events") or []),
                *metric_events,
            ],
        }
    except LLMProviderChainError as exc:
        logger.exception("Meal analyzer LLM chain failed; using fallback analysis")
        meal_analysis = _fallback_meal_analysis(meal_text)
        state = {
            **state,
            "metric_events": [
                *(state.get("metric_events") or []),
                *exc.metric_events,
            ],
        }

    return {
        **state,
        "meal_analysis": {
            "foods": meal_analysis.get("foods") or [],
            "carb_sources": meal_analysis.get("carb_sources") or [],
            "protein_sources": meal_analysis.get("protein_sources") or [],
            "beverages": meal_analysis.get("beverages") or [],
            "possible_issues": meal_analysis.get("possible_issues") or [],
        },
    }
