from typing import Dict, Any
import logging

from app.llm.gemini_client import gemini_client
from app.observability.langsmith import traceable

logger = logging.getLogger("nutriguard.orchestrator.report")

def _fallback_report(meal_analysis: Dict[str, Any], risk_flags: list, context: list | None = None) -> str:
    foods = meal_analysis.get("foods", [])
    context = context or []

    summary = f"Today's Nutrition Summary\n\nYou had {', '.join(foods)}."
    recommendations = []
    safety_note = "Follow your doctor's advice for iron supplements."

    if any(flag.get("type") == "low_protein" for flag in risk_flags):
        recommendations.append(
            "Add protein such as sprouts, curd, paneer, tofu, chana, or soy chunks."
        )
    if any(flag.get("type") == "iron_attention" for flag in risk_flags):
        recommendations.append(
            "Keep tea away from iron-rich meals or prescribed supplement timing."
        )
    if any(flag.get("type") == "short_meal_gap" for flag in risk_flags):
        recommendations.append("Leave a clearer gap between meals when possible, or log snacks separately.")
    if any(flag.get("type") == "possible_mixed_meals" for flag in risk_flags):
        recommendations.append("Split breakfast, lunch, dinner, and snacks into separate logs for better analysis.")
    if any(flag.get("type") == "tea_near_iron_supplement" for flag in risk_flags):
        recommendations.append("Keep tea or coffee farther away from iron supplement timing unless your clinician advised otherwise.")
    if any(flag.get("type") == "calcium_near_iron_supplement" for flag in risk_flags):
        recommendations.append("Avoid taking iron close to calcium-rich foods like dahi, paneer, milk, or calcium supplements.")
    for item in context[:3]:
        content = item.get("content") if isinstance(item, dict) else str(item)
        evidence_level = item.get("evidence_level") if isinstance(item, dict) else None
        if content and evidence_level == "traditional_ayurveda":
            recommendations.append(f"Optional Ayurveda context: {content}")
        elif content:
            recommendations.append(content)
    if not recommendations:
        recommendations.append("Keep meals balanced with protein, fiber, and fluids.")

    recommendation_lines = "\n".join(f"- {item}" for item in recommendations)
    report = (
        f"{summary}\n\n"
        f"Needs Attention:\n- Breakfast has low protein.\n"
        f"- Since you have iron deficiency, tea near meals may not be ideal.\n\n"
        f"Suggestions:\n{recommendation_lines}\n\n"
        f"Safety:\n- {safety_note}"
    )
    return report


@traceable(name="Report Agent", run_type="chain")
def report_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    meal_analysis = state.get("meal_analysis") or {}
    risk_flags = state.get("risk_flags") or []
    goal = state.get("goal", "")
    goals = state.get("goals") or ([goal] if goal else [])
    diet_type = state.get("diet_type")
    health_conditions = state.get("health_conditions") or []
    supplements = state.get("supplements") or []
    deficiencies = state.get("deficiencies") or []
    meal_type = state.get("meal_type")
    meal_time = state.get("meal_time")
    timezone = state.get("timezone") or "user local time"
    previous_meal_text = state.get("previous_meal_text")
    previous_meal_time = state.get("previous_meal_time")
    minutes_since_previous_meal = state.get("minutes_since_previous_meal")
    day_meals = state.get("day_meals") or []
    health_report_text = (state.get("health_report_text") or "")[:6000]
    context = state.get("context") or []

    try:
        report = gemini_client.generate_text(
            f"""
You are the Report Agent for NutriGuard.

Create a short, simple user-facing nutrition report.
Use this structure:

Today's Nutrition Summary

Needs Attention:
- ...

Suggestions:
- ...

Safety:
- ...

Rules:
- Be practical and non-alarming.
- Use plain text only. Do not use Markdown syntax such as **bold**, headings with **, or bullet markers with *.
- Use hyphen bullets only under Needs Attention, Suggestions, and Safety.
- Use the provided meal times as {timezone}; do not convert them to another timezone.
- Do not diagnose, prescribe, or change supplement dosage.
- Include a safety note for health conditions or supplements when relevant.
- Mention meal timing if there may not be enough gap from the previous meal.
- Write this as a day-level nutrition timeline report when day meals are available.
- Mention risky combinations across the day, such as tea/coffee near iron supplement or dahi/paneer/calcium near iron supplement.
- Ask the user to split the log if it appears to combine multiple meals.
- Use the health report context conservatively.
- Use retrieved nutrition context for protein, energy, muscle gain, and fat loss suggestions.
- Items marked evidence_level=traditional_ayurveda are Ayurveda/traditional context. Phrase them as optional traditional guidance, not as clinical claims.

Goal: {goal}
Goals: {goals}
Diet type: {diet_type}
Health conditions: {health_conditions}
Deficiencies: {deficiencies}
Supplements: {supplements}
Meal type: {meal_type}
Meal time: {meal_time}
Timezone: {timezone}
Previous meal text: {previous_meal_text}
Previous meal time: {previous_meal_time}
Minutes since previous meal: {minutes_since_previous_meal}
Day meals timeline: {day_meals}
Health report text: {health_report_text}
Meal analysis: {meal_analysis}
Risk flags: {risk_flags}
Retrieved context: {context}
"""
        )
    except Exception:
        logger.exception("Report Gemini call failed; using fallback report")
        report = _fallback_report(meal_analysis, risk_flags, context)
        state = {
            **state,
            "metric_events": [
                *(state.get("metric_events") or []),
                {"name": "gemini_fallback", "source": "report"},
            ],
        }

    return {
        **state,
        "report": report,
    }
