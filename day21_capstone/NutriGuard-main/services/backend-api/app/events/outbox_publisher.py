import os
from threading import Event
import requests
from app.database import SessionLocal
from app.models import DailyReport, MealLog, NutritionFlag, OutboxEvent, UserProfile

AI_ORCHESTRATOR_URL = os.getenv("AI_ORCHESTRATOR_URL")
PUBLISH_INTERVAL_SECONDS = int(os.getenv("OUTBOX_PUBLISH_INTERVAL_SECONDS", "5"))


def publish_pending_events():
    db = SessionLocal()
    try:
        pending_events = db.query(OutboxEvent).filter(OutboxEvent.status == "PENDING").all()
        for event in pending_events:
            payload = event.payload
            meal_log_id = payload["meal_log_id"]
            user_id = payload["user_id"]

            meal = db.query(MealLog).filter(MealLog.id == meal_log_id).first()
            if not meal:
                continue

            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                continue

            meal.status = "PROCESSING"
            db.commit()

            previous_meal = (
                db.query(MealLog)
                .filter(MealLog.user_id == user_id, MealLog.id != meal_log_id)
                .order_by(MealLog.created_at.desc())
                .first()
            )
            current_time = meal.meal_time or meal.created_at
            previous_time = None
            minutes_since_previous_meal = None
            if previous_meal:
                previous_time = previous_meal.meal_time or previous_meal.created_at
            if current_time and previous_time:
                minutes_since_previous_meal = int((current_time - previous_time).total_seconds() / 60)
                if minutes_since_previous_meal < 0:
                    minutes_since_previous_meal = None

            day_meals = []
            if current_time:
                meals_for_day = (
                    db.query(MealLog)
                    .filter(MealLog.user_id == user_id)
                    .order_by(MealLog.created_at.asc())
                    .limit(50)
                    .all()
                )
                for item in meals_for_day:
                    item_time = item.meal_time or item.created_at
                    if not item_time or item_time.date() != current_time.date():
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
                            "meal_time": item_time.isoformat() if item_time else None,
                            "status": item.status,
                        }
                    )
                day_meals.sort(key=lambda item: item.get("meal_time") or "")

            response = requests.post(
                f"{AI_ORCHESTRATOR_URL}/process-meal",
                json={
                    "meal_log_id": meal_log_id,
                    "user_id": user_id,
                    "meal_text": meal.meal_text,
                    "meal_type": meal.meal_type,
                    "meal_time": current_time.isoformat() if current_time else None,
                    "previous_meal_text": previous_meal.meal_text if previous_meal else None,
                    "previous_meal_time": previous_time.isoformat() if previous_time else None,
                    "minutes_since_previous_meal": minutes_since_previous_meal,
                    "day_meals": day_meals,
                    "goal": profile.goal,
                    "goals": profile.goals or ([profile.goal] if profile.goal else []),
                    "health_conditions": profile.health_conditions or [],
                    "deficiencies": profile.deficiencies or [],
                    "supplements": profile.supplements or [],
                    "health_report_text": profile.health_report_text or "",
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

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
                recommendations.append(
                    "Add protein such as sprouts, curd, paneer, tofu, chana, or soy chunks."
                )
            if "tea" in report_text.lower() and "iron" in report_text.lower():
                recommendations.append(
                    "Keep tea away from iron-rich meals or prescribed supplement timing."
                )

            report = db.query(DailyReport).filter(DailyReport.meal_log_id == meal_log_id).first()
            if report:
                report.summary = report_text
                report.recommendations = recommendations
                report.safety_note = safety_note
            else:
                db.add(
                    DailyReport(
                        user_id=user_id,
                        meal_log_id=meal_log_id,
                        summary=report_text,
                        recommendations=recommendations,
                        safety_note=safety_note,
                    )
                )

            meal.status = "COMPLETED"
            event.status = "PUBLISHED"
            db.commit()
    except requests.RequestException:
        db.rollback()
    finally:
        db.close()


def run_publisher_loop(stop_event: Event):
    while not stop_event.is_set():
        publish_pending_events()
        stop_event.wait(PUBLISH_INTERVAL_SECONDS)


if __name__ == "__main__":
    stop = Event()
    try:
        run_publisher_loop(stop)
    except KeyboardInterrupt:
        stop.set()
