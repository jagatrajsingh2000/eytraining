from typing import Dict, Any
from datetime import datetime
import logging

from app.llm.gemini_client import gemini_client
from app.observability.langsmith import traceable
from app.rag.retriever import retrieve_nutrition_context

logger = logging.getLogger("nutriguard.orchestrator.health_risk")

def _fallback_risk_flags(
    meal_analysis: Dict[str, Any],
    health_conditions: list,
    deficiencies: list,
    minutes_since_previous_meal: int | None,
    meal_text: str,
    day_meals: list,
) -> list:
    risk_flags = []
    if not meal_analysis.get("protein_sources"):
        risk_flags.append(
            {
                "type": "low_protein",
                "severity": "medium",
                "message": "Breakfast appears low in protein.",
            }
        )

    all_conditions = set(health_conditions + deficiencies)
    if "iron_deficiency" in all_conditions and "tea" in meal_analysis.get("beverages", []):
        risk_flags.append(
            {
                "type": "iron_attention",
                "severity": "medium",
                "message": "Tea near meals may need attention for iron deficiency.",
            }
        )
    if minutes_since_previous_meal is not None and minutes_since_previous_meal < 120:
        risk_flags.append(
            {
                "type": "short_meal_gap",
                "severity": "medium",
                "message": "This meal was logged within two hours of the previous meal. Check whether it was a snack or part of the same eating window.",
            }
        )
    lowered = meal_text.lower()
    mixed_markers = ["breakfast", "lunch", "dinner", "snack"]
    if sum(1 for marker in mixed_markers if marker in lowered) > 1:
        risk_flags.append(
            {
                "type": "possible_mixed_meals",
                "severity": "low",
                "message": "This entry may include multiple meals. Splitting meals can improve analysis accuracy.",
            }
        )
    risk_flags.extend(_fallback_day_timeline_flags(day_meals, all_conditions))
    return risk_flags


def _parse_time(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _minutes_between(first: str | None, second: str | None):
    first_time = _parse_time(first)
    second_time = _parse_time(second)
    if not first_time or not second_time:
        return None
    return abs(int((second_time - first_time).total_seconds() / 60))


def _fallback_day_timeline_flags(day_meals: list, all_conditions: set) -> list:
    if "iron_deficiency" not in all_conditions:
        return []

    flags = []
    iron_keywords = ["iron tablet", "iron supplement", "ferrous", "iron pill"]
    tea_keywords = ["tea", "coffee", "chai"]
    dairy_keywords = ["dahi", "curd", "paneer", "milk", "yogurt", "cheese", "calcium"]

    iron_events = [
        item for item in day_meals if _contains_any(item.get("meal_text", ""), iron_keywords)
    ]
    tea_events = [
        item for item in day_meals if _contains_any(item.get("meal_text", ""), tea_keywords)
    ]
    dairy_events = [
        item for item in day_meals if _contains_any(item.get("meal_text", ""), dairy_keywords)
    ]

    for iron_event in iron_events:
        for tea_event in tea_events:
            gap = _minutes_between(iron_event.get("meal_time"), tea_event.get("meal_time"))
            if gap is not None and gap <= 90:
                flags.append(
                    {
                        "type": "tea_near_iron_supplement",
                        "severity": "high",
                        "message": "Tea or coffee was logged close to an iron supplement. Consider keeping a wider gap based on your clinician's guidance.",
                    }
                )
                break
        for dairy_event in dairy_events:
            gap = _minutes_between(iron_event.get("meal_time"), dairy_event.get("meal_time"))
            if gap is not None and gap <= 120:
                flags.append(
                    {
                        "type": "calcium_near_iron_supplement",
                        "severity": "medium",
                        "message": "Dairy/calcium foods such as dahi, paneer, or milk were logged close to an iron supplement. This may reduce iron absorption.",
                    }
                )
                break

    unique = []
    seen = set()
    for flag in flags:
        if flag["type"] not in seen:
            unique.append(flag)
            seen.add(flag["type"])
    return unique


@traceable(name="Health Risk Agent", run_type="chain")
def health_risk_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    meal_analysis = state.get("meal_analysis") or {}
    health_conditions = state.get("health_conditions") or []
    deficiencies = state.get("deficiencies") or []
    supplements = state.get("supplements") or []
    goal = state.get("goal", "")
    goals = state.get("goals") or ([goal] if goal else [])
    diet_type = state.get("diet_type")
    meal_text = state.get("meal_text", "")
    meal_type = state.get("meal_type")
    meal_time = state.get("meal_time")
    previous_meal_text = state.get("previous_meal_text")
    previous_meal_time = state.get("previous_meal_time")
    minutes_since_previous_meal = state.get("minutes_since_previous_meal")
    day_meals = state.get("day_meals") or []
    health_report_text = (state.get("health_report_text") or "")[:6000]

    context = retrieve_nutrition_context(
        {
            **state,
            "meal_analysis": meal_analysis,
            "meal_text": meal_text,
            "goal": goal,
            "goals": goals,
            "diet_type": diet_type,
            "health_conditions": health_conditions,
            "deficiencies": deficiencies,
            "supplements": supplements,
            "day_meals": day_meals,
        }
    )
    try:
        result = gemini_client.generate_json(
            f"""
You are the Health Risk Agent for NutriGuard.

Check the meal against the user profile and retrieved nutrition context.
Return only valid JSON with this shape:
{{
  "risk_flags": [
    {{
      "type": "short_snake_case",
      "severity": "low|medium|high",
      "message": "brief user-safe message"
    }}
  ]
}}

Rules:
- Keep guidance nutrition-focused and conservative.
- Do not diagnose, prescribe, or change supplement dosage.
- Include safety-sensitive flags when the profile makes them relevant.
- Check whether the user has enough gap from the previous meal.
- Analyze the whole day timeline, not only this single meal.
- Look for combinations across meals, for example tea/coffee near iron supplement or dairy/calcium foods near iron supplement.
- Flag possible mixed meals when the text appears to combine breakfast/lunch/dinner/snacks.
- Use the uploaded/pasted health report as context, but do not diagnose.
- Treat retrieved items with evidence_level=traditional_ayurveda as Ayurveda/traditional context only, not clinical proof.

Meal text: {meal_text}
Meal type: {meal_type}
Meal time: {meal_time}
Previous meal text: {previous_meal_text}
Previous meal time: {previous_meal_time}
Minutes since previous meal: {minutes_since_previous_meal}
Day meals timeline: {day_meals}
Goal: {goal}
Goals: {goals}
Diet type: {diet_type}
Health conditions: {health_conditions}
Deficiencies: {deficiencies}
Supplements: {supplements}
Health report text: {health_report_text}
Meal analysis: {meal_analysis}
Retrieved context: {context}
"""
        )
        risk_flags = result.get("risk_flags") or []
    except Exception:
        logger.exception("Health risk Gemini call failed; using fallback flags")
        risk_flags = _fallback_risk_flags(
            meal_analysis,
            health_conditions,
            deficiencies,
            minutes_since_previous_meal,
            meal_text,
            day_meals,
        )
        state = {
            **state,
            "metric_events": [
                *(state.get("metric_events") or []),
                {"name": "gemini_fallback", "source": "health_risk"},
            ],
        }

    return {
        **state,
        "risk_flags": risk_flags,
        "context": context,
    }
