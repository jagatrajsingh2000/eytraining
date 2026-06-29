from fastapi import FastAPI
from app.graph.nutriguard_graph import graph
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

app = FastAPI(title="NutriGuard AI Orchestrator")


class ProcessMealInput(BaseModel):
    meal_log_id: int
    user_id: int
    meal_text: str
    meal_type: Optional[str] = None
    meal_time: Optional[str] = None
    previous_meal_text: Optional[str] = None
    previous_meal_time: Optional[str] = None
    minutes_since_previous_meal: Optional[int] = None
    day_meals: Optional[List[Dict[str, Any]]] = None
    goal: str
    goals: Optional[List[str]] = None
    health_conditions: Optional[List[str]] = None
    deficiencies: Optional[List[str]] = None
    supplements: Optional[List[str]] = None
    health_report_text: Optional[str] = None


@app.post("/process-meal")
def process_meal(payload: ProcessMealInput):
    result = graph.invoke(
        {
            "meal_log_id": payload.meal_log_id,
            "user_id": payload.user_id,
            "meal_text": payload.meal_text,
            "meal_type": payload.meal_type,
            "meal_time": payload.meal_time,
            "previous_meal_text": payload.previous_meal_text,
            "previous_meal_time": payload.previous_meal_time,
            "minutes_since_previous_meal": payload.minutes_since_previous_meal,
            "day_meals": payload.day_meals or [],
            "goal": payload.goal,
            "goals": payload.goals or ([payload.goal] if payload.goal else []),
            "health_conditions": payload.health_conditions or [],
            "deficiencies": payload.deficiencies or [],
            "supplements": payload.supplements or [],
            "health_report_text": payload.health_report_text or "",
            "meal_analysis": None,
            "risk_flags": [],
            "report": None,
        }
    )
    return {
        "meal_analysis": result.get("meal_analysis") or {},
        "risk_flags": result.get("risk_flags") or [],
        "report": result.get("report") or "",
    }

@app.get("/health")
def health():
    return {"status": "ok"}
