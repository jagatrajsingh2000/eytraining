import os
from zoneinfo import ZoneInfo

from app.models import MealLog, UserProfile

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")


def to_app_time(value):
    if not value:
        return None
    timezone = ZoneInfo(APP_TIMEZONE)
    if value.tzinfo:
        return value.astimezone(timezone)
    return value.replace(tzinfo=timezone)


def app_time_iso(value):
    local_time = to_app_time(value)
    return local_time.isoformat() if local_time else None


def build_processing_payload(db, meal: MealLog, profile: UserProfile, trace_id: str | None = None) -> dict:
    previous_meal = (
        db.query(MealLog)
        .filter(MealLog.user_id == meal.user_id, MealLog.id != meal.id)
        .order_by(MealLog.created_at.desc())
        .first()
    )
    current_time = meal.meal_time or meal.created_at
    previous_time = previous_meal.meal_time or previous_meal.created_at if previous_meal else None
    minutes_since_previous_meal = None
    if current_time and previous_time:
        minutes_since_previous_meal = int((current_time - previous_time).total_seconds() / 60)
        if minutes_since_previous_meal < 0:
            minutes_since_previous_meal = None

    day_meals = []
    if current_time:
        current_local_time = to_app_time(current_time)
        meals_for_day = (
            db.query(MealLog)
            .filter(MealLog.user_id == meal.user_id)
            .order_by(MealLog.created_at.asc())
            .limit(50)
            .all()
        )
        for item in meals_for_day:
            item_time = item.meal_time or item.created_at
            item_local_time = to_app_time(item_time)
            if not item_local_time or item_local_time.date() != current_local_time.date():
                continue
            day_meals.append(
                {
                    "meal_log_id": item.id,
                    "meal_type": item.meal_type,
                    "meal_text": item.meal_text,
                    "foods_text": item.foods_text,
                    "drinks_text": item.drinks_text,
                    "supplements_text": item.supplements_text,
                    "notes_text": item.notes_text,
                    "meal_time": app_time_iso(item_time),
                    "status": item.status,
                }
            )
        day_meals.sort(key=lambda item: item.get("meal_time") or "")

    return {
        "trace_id": trace_id,
        "meal_log_id": meal.id,
        "user_id": meal.user_id,
        "meal_text": meal.meal_text,
        "meal_type": meal.meal_type,
        "meal_time": app_time_iso(current_time),
        "previous_meal_text": previous_meal.meal_text if previous_meal else None,
        "previous_meal_time": app_time_iso(previous_time),
        "minutes_since_previous_meal": minutes_since_previous_meal,
        "timezone": APP_TIMEZONE,
        "day_meals": day_meals,
        "goal": profile.goal,
        "goals": profile.goals or ([profile.goal] if profile.goal else []),
        "diet_type": profile.diet_type,
        "health_conditions": profile.health_conditions or [],
        "deficiencies": profile.deficiencies or [],
        "supplements": profile.supplements or [],
        "health_report_text": profile.health_report_text or "",
    }
