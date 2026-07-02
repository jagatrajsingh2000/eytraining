import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_user_id
from app.database import SessionLocal
from app.models import MealLog, Notification, User

router = APIRouter(tags=["notifications"])

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
EXPECTED_MEALS = {
    "breakfast": {
        "cutoff": time(10, 30),
        "title": "Breakfast not logged yet",
        "message": "Add breakfast when you get a minute so today's nutrition report stays complete.",
    },
    "lunch": {
        "cutoff": time(15, 30),
        "title": "Lunch is missing",
        "message": "Log lunch to help NutriGuard understand your day-level meal timing.",
    },
    "dinner": {
        "cutoff": time(21, 30),
        "title": "Dinner not logged yet",
        "message": "Add dinner when possible so your combined daily report can catch gaps and combinations.",
    },
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def app_now() -> datetime:
    return datetime.now(ZoneInfo(APP_TIMEZONE))


def meal_local_date(meal: MealLog, timezone: ZoneInfo):
    meal_time = meal.meal_time or meal.created_at
    if not meal_time:
        return None
    if meal_time.tzinfo:
        return meal_time.astimezone(timezone).date()
    return meal_time.date()


def sync_missing_meal_notifications(db: Session, user_id: int) -> None:
    timezone = ZoneInfo(APP_TIMEZONE)
    now = app_now()
    today = now.date()
    today_key = today.isoformat()

    meals = db.query(MealLog).filter(MealLog.user_id == user_id).all()
    logged_meal_types = {
        (meal.meal_type or "").strip().lower()
        for meal in meals
        if meal_local_date(meal, timezone) == today
    }

    for meal_type, details in EXPECTED_MEALS.items():
        notification_type = f"missed_{meal_type}"
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.type == notification_type,
                Notification.notification_date == today_key,
            )
            .first()
        )

        if meal_type in logged_meal_types:
            if existing and existing.status == "unread":
                existing.status = "read"
                db.commit()
            continue

        if now.time() < details["cutoff"]:
            continue

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=details["title"],
            message=details["message"],
            notification_date=today_key,
            status="unread",
        )
        db.add(notification)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()


def serialize_notification(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "status": notification.status,
        "notification_date": notification.notification_date,
        "created_at": notification.created_at,
    }


@router.get("/users/{user_id}/notifications", response_model=list)
def list_notifications(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_user_id(user_id, current_user)
    sync_missing_meal_notifications(db, user_id)
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    return [serialize_notification(notification) for notification in notifications]


@router.patch("/notifications/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    require_user_id(notification.user_id, current_user)
    notification.status = "read"
    db.commit()
    return serialize_notification(notification)
