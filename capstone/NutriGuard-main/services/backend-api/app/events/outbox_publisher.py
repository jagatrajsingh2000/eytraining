import os
from threading import Event
import requests
from app.database import SessionLocal
from app.models import DailyReport, MealLog, NutritionFlag, OutboxEvent, UserProfile
from app.events.meal_context import build_processing_payload

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

            response = requests.post(
                f"{AI_ORCHESTRATOR_URL}/process-meal",
                json=build_processing_payload(db, meal, profile),
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
