from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import DailyReport, MealLog, OutboxEvent
from app.schemas import MealCreate, MealResponse, ReportResponse

router = APIRouter(tags=["meals"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_meal_text(payload: MealCreate) -> str:
    if payload.meal_text:
        return payload.meal_text

    parts = []
    if payload.foods_text:
        parts.append(f"Foods: {payload.foods_text}")
    if payload.drinks_text:
        parts.append(f"Drinks: {payload.drinks_text}")
    if payload.supplements_text:
        parts.append(f"Supplements/medicine: {payload.supplements_text}")
    if payload.notes_text:
        parts.append(f"Notes: {payload.notes_text}")
    return "\n".join(parts).strip() or "Meal details not provided"


def extract_labeled_detail(meal_text: str | None, label: str) -> str | None:
    if not meal_text:
        return None
    prefix = f"{label}:"
    for line in meal_text.splitlines():
        if line.lower().startswith(prefix.lower()):
            value = line.split(":", 1)[1].strip()
            return value or None
    return None


def serialize_meal(meal: MealLog) -> dict:
    foods_text = meal.foods_text or extract_labeled_detail(meal.meal_text, "Foods")
    drinks_text = meal.drinks_text or extract_labeled_detail(meal.meal_text, "Drinks")
    supplements_text = (
        meal.supplements_text
        or extract_labeled_detail(meal.meal_text, "Supplements/medicine")
        or extract_labeled_detail(meal.meal_text, "Supplements")
    )
    notes_text = meal.notes_text or extract_labeled_detail(meal.meal_text, "Notes")

    if not any([foods_text, drinks_text, supplements_text, notes_text]) and meal.meal_text:
        foods_text = meal.meal_text

    return {
        "id": meal.id,
        "user_id": meal.user_id,
        "meal_text": meal.meal_text,
        "foods_text": foods_text,
        "drinks_text": drinks_text,
        "supplements_text": supplements_text,
        "notes_text": notes_text,
        "meal_type": meal.meal_type,
        "meal_time": meal.meal_time,
        "status": meal.status,
        "created_at": meal.created_at,
    }


@router.post("/meals", response_model=MealResponse)
def create_meal(payload: MealCreate, db: Session = Depends(get_db)):
    meal_text = build_meal_text(payload)
    meal = MealLog(
        user_id=payload.user_id,
        meal_text=meal_text,
        foods_text=payload.foods_text,
        drinks_text=payload.drinks_text,
        supplements_text=payload.supplements_text,
        notes_text=payload.notes_text,
        meal_type=payload.meal_type,
        meal_time=payload.meal_time,
        status="RECEIVED",
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    event = OutboxEvent(
        event_type="MealLogged",
        payload={"meal_log_id": meal.id, "user_id": payload.user_id},
        status="PENDING",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "meal_log_id": meal.id,
        "status": meal.status,
        "message": "Meal received and processing started.",
    }


@router.get("/meals/{meal_log_id}", response_model=dict)
def get_meal(meal_log_id: int, db: Session = Depends(get_db)):
    meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return serialize_meal(meal)


@router.get("/users/{user_id}/meals", response_model=list)
def list_user_meals(user_id: int, db: Session = Depends(get_db)):
    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id)
        .order_by(MealLog.created_at.desc())
        .limit(20)
        .all()
    )
    return [serialize_meal(meal) for meal in meals]


@router.get("/users/{user_id}/daily-report", response_model=ReportResponse)
def get_daily_report(
    user_id: int,
    report_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    target_date = report_date or date.today()
    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id)
        .order_by(MealLog.created_at.desc())
        .all()
    )
    day_meals = [
        meal
        for meal in meals
        if (meal.meal_time or meal.created_at) and (meal.meal_time or meal.created_at).date() == target_date
    ]
    day_meals.sort(key=lambda meal: meal.meal_time or meal.created_at, reverse=True)
    if not day_meals:
        return {
            "status": "NO_MEALS",
            "summary": "No meals logged for this date.",
            "recommendations": [],
            "safety_note": "",
        }

    latest_meal = day_meals[0]
    if latest_meal.status != "COMPLETED":
        return {
            "status": latest_meal.status,
            "summary": "Daily report is updating.",
            "recommendations": [],
            "safety_note": "Please wait.",
        }

    report = db.query(DailyReport).filter(DailyReport.meal_log_id == latest_meal.id).first()
    if not report:
        return {
            "status": "PROCESSING",
            "summary": "Daily report is being prepared.",
            "recommendations": [],
            "safety_note": "Please wait.",
        }

    return {
        "status": "COMPLETED",
        "summary": report.summary,
        "recommendations": report.recommendations or [],
        "safety_note": report.safety_note or "",
    }


@router.get("/users/{user_id}/daily-report/details", response_model=dict)
def get_daily_report_details(
    user_id: int,
    report_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    target_date = report_date or date.today()
    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id)
        .order_by(MealLog.created_at.asc())
        .all()
    )
    day_meals = [
        meal
        for meal in meals
        if (meal.meal_time or meal.created_at) and (meal.meal_time or meal.created_at).date() == target_date
    ]
    day_meals.sort(key=lambda meal: meal.meal_time or meal.created_at)

    timeline = []
    latest_report = None
    latest_status = "NO_MEALS" if not day_meals else day_meals[-1].status

    for meal in day_meals:
        report = db.query(DailyReport).filter(DailyReport.meal_log_id == meal.id).first()
        report_payload = None
        if report:
            report_payload = {
                "status": "COMPLETED",
                "summary": report.summary,
                "recommendations": report.recommendations or [],
                "safety_note": report.safety_note or "",
            }
            latest_report = report_payload

        meal_payload = serialize_meal(meal)
        meal_payload["report"] = report_payload
        timeline.append(meal_payload)

    combined_report = latest_report or {
        "status": latest_status,
        "summary": "Daily report is updating." if day_meals else "No meals logged for this date.",
        "recommendations": [],
        "safety_note": "Please wait." if day_meals else "",
    }

    return {
        "date": target_date.isoformat(),
        "status": combined_report["status"],
        "combined_report": combined_report,
        "meals": timeline,
    }


@router.get("/meals/{meal_log_id}/report", response_model=ReportResponse)
def get_report(meal_log_id: int, db: Session = Depends(get_db)):
    meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    if meal.status != "COMPLETED":
        return {
            "status": meal.status,
            "summary": "Processing in progress.",
            "recommendations": [],
            "safety_note": "Please wait.",
        }

    report = db.query(DailyReport).filter(DailyReport.meal_log_id == meal_log_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "status": "COMPLETED",
        "summary": report.summary,
        "recommendations": report.recommendations or [],
        "safety_note": report.safety_note or "",
    }
