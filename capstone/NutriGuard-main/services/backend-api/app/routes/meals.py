from datetime import date
import logging
import os
from typing import Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.auth import get_current_user, require_user_id
from app.database import SessionLocal
from app.events.meal_context import build_processing_payload
from app.models import DailyReport, MealLog, MetricEvent, NutritionFlag, OutboxEvent, ReportFeedback, User, UserProfile
from app.rate_limiter import limiter, LIMIT_MEAL_WRITE, LIMIT_FEEDBACK_WRITE, LIMIT_READ
from app.schemas import MealCreate, MealResponse, ReportFeedbackCreate, ReportResponse

router = APIRouter(tags=["meals"])
EVENT_TRANSPORT = os.getenv("EVENT_TRANSPORT", "outbox")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
logger = logging.getLogger("nutriguard.backend.meals")


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


def app_local_date(value):
    if not value:
        return None
    timezone = ZoneInfo(APP_TIMEZONE)
    if value.tzinfo:
        return value.astimezone(timezone).date()
    return value.date()


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


def serialize_feedback(feedback: ReportFeedback | None) -> dict | None:
    if not feedback:
        return None
    return {
        "id": feedback.id,
        "user_id": feedback.user_id,
        "meal_log_id": feedback.meal_log_id,
        "category": feedback.category,
        "rating": feedback.rating,
        "comment": feedback.comment or "",
        "source": feedback.source,
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
    }


def serialize_feedback_map(feedback_items: list[ReportFeedback]) -> dict:
    return {
        feedback.category: serialize_feedback(feedback)
        for feedback in feedback_items
        if feedback.category
    }


def save_meal_result(db: Session, meal_log_id: int, result: dict) -> None:
    trace_id = result.get("trace_id")
    logger.info("Saving meal result trace_id=%s meal_log_id=%s", trace_id, meal_log_id)
    meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    db.query(NutritionFlag).filter(NutritionFlag.meal_log_id == meal_log_id).delete()
    risk_flags = result.get("risk_flags", [])
    for flag in risk_flags:
        db.add(
            NutritionFlag(
                meal_log_id=meal_log_id,
                type=flag.get("type", "unknown"),
                severity=flag.get("severity", "medium"),
                message=flag.get("message", ""),
            )
        )

    report_text = result.get("report", "")
    recommendations = []
    safety_note = "Follow your doctor's advice for iron supplements."
    if "protein" in report_text.lower():
        recommendations.append("Add protein such as sprouts, curd, paneer, tofu, chana, or soy chunks.")
    if "tea" in report_text.lower() and "iron" in report_text.lower():
        recommendations.append("Keep tea away from iron-rich meals or prescribed supplement timing.")

    report = db.query(DailyReport).filter(DailyReport.meal_log_id == meal_log_id).first()
    if report:
        report.summary = report_text
        report.recommendations = recommendations
        report.safety_note = safety_note
    else:
        db.add(
            DailyReport(
                user_id=meal.user_id,
                meal_log_id=meal_log_id,
                summary=report_text,
                recommendations=recommendations,
                safety_note=safety_note,
            )
        )

    for event in result.get("metric_events", []) or []:
        db.add(
            MetricEvent(
                name=event.get("name", "unknown"),
                source=event.get("source"),
                user_id=meal.user_id,
                meal_log_id=meal_log_id,
                payload=event.get("payload") or {},
            )
        )

    meal.status = "COMPLETED"
    db.commit()
    logger.info("Saved meal result trace_id=%s meal_log_id=%s", trace_id, meal_log_id)


@router.post("/meals", response_model=MealResponse)
@limiter.limit(LIMIT_MEAL_WRITE)
def create_meal(
    payload: MealCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(payload.user_id, current_user)
    trace_id = str(uuid4())
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

    if EVENT_TRANSPORT == "service_bus":
        from app.events.service_bus import publish_meal_event

        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.user_id).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Create your health profile before logging meals.")
        meal.status = "QUEUED"
        logger.info("Queueing meal event trace_id=%s meal_log_id=%s user_id=%s", trace_id, meal.id, payload.user_id)
        publish_meal_event(build_processing_payload(db, meal, profile, trace_id=trace_id))
        db.commit()
    else:
        event = OutboxEvent(
            event_type="MealLogged",
            payload={"meal_log_id": meal.id, "user_id": payload.user_id},
            status="PENDING",
        )
        db.add(event)
        db.commit()

    return {
        "meal_log_id": meal.id,
        "trace_id": trace_id,
        "status": meal.status,
        "message": "Meal received and processing started.",
    }


@router.get("/meals/{meal_log_id}", response_model=dict)
@limiter.limit(LIMIT_READ)
def get_meal(
    meal_log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    require_user_id(meal.user_id, current_user)
    return serialize_meal(meal)


@router.get("/users/{user_id}/meals", response_model=list)
def list_user_meals(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
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
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
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
        if app_local_date(meal.meal_time or meal.created_at) == target_date
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


@router.post("/internal/meal-results", response_model=dict)
def receive_meal_result(
    payload: dict,
    db: Session = Depends(get_db),
    x_internal_api_key: str | None = Header(default=None),
):
    if INTERNAL_API_KEY and x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    meal_log_id = payload.get("meal_log_id")
    trace_id = payload.get("trace_id")
    if not meal_log_id:
        raise HTTPException(status_code=400, detail="meal_log_id is required")
    logger.info("Received internal meal result trace_id=%s meal_log_id=%s", trace_id, meal_log_id)
    save_meal_result(db, meal_log_id, payload)
    return {"status": "saved", "meal_log_id": meal_log_id}


@router.get("/users/{user_id}/daily-report/details", response_model=dict)
def get_daily_report_details(
    user_id: int,
    report_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
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
        if app_local_date(meal.meal_time or meal.created_at) == target_date
    ]
    day_meals.sort(key=lambda meal: meal.meal_time or meal.created_at)

    timeline = []
    latest_report = None
    latest_status = "NO_MEALS" if not day_meals else day_meals[-1].status

    for meal in day_meals:
        report = db.query(DailyReport).filter(DailyReport.meal_log_id == meal.id).first()
        report_payload = None
        if report:
            feedback_items = (
                db.query(ReportFeedback)
                .filter(ReportFeedback.user_id == user_id, ReportFeedback.meal_log_id == meal.id)
                .all()
            )
            report_payload = {
                "status": "COMPLETED",
                "summary": report.summary,
                "recommendations": report.recommendations or [],
                "safety_note": report.safety_note or "",
                "feedback": serialize_feedback_map(feedback_items),
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
def get_report(
    meal_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    require_user_id(meal.user_id, current_user)

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


@router.post("/meals/{meal_log_id}/feedback", response_model=dict)
def save_report_feedback(
    meal_log_id: int,
    payload: ReportFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = payload.rating.strip().lower()
    if rating not in {"liked", "disliked"}:
        raise HTTPException(status_code=400, detail="rating must be liked or disliked")
    category = (payload.category or "suggestions").strip().lower()
    if category not in {"needs_attention", "suggestions"}:
        raise HTTPException(status_code=400, detail="category must be needs_attention or suggestions")

    meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    require_user_id(meal.user_id, current_user)

    report = db.query(DailyReport).filter(DailyReport.meal_log_id == meal_log_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    feedback = (
        db.query(ReportFeedback)
        .filter(
            ReportFeedback.user_id == meal.user_id,
            ReportFeedback.meal_log_id == meal_log_id,
            ReportFeedback.category == category,
        )
        .first()
    )
    if feedback:
        feedback.category = category
        feedback.rating = rating
        feedback.comment = payload.comment
        feedback.source = payload.source or "daily_report"
    else:
        feedback = ReportFeedback(
            user_id=meal.user_id,
            meal_log_id=meal_log_id,
            category=category,
            rating=rating,
            comment=payload.comment,
            source=payload.source or "daily_report",
        )
        db.add(feedback)
    db.commit()
    db.refresh(feedback)
    logger.info("Saved report feedback meal_log_id=%s category=%s rating=%s", meal_log_id, category, rating)
    return serialize_feedback(feedback)
