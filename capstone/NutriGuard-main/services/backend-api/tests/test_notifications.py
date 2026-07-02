from datetime import datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.routes.notifications import meal_local_date, serialize_notification


def test_meal_local_date_converts_aware_timestamp_to_app_timezone():
    meal = SimpleNamespace(
        meal_time=datetime(2026, 7, 1, 20, 0, tzinfo=timezone.utc),
        created_at=None,
    )

    assert meal_local_date(meal, ZoneInfo("Asia/Kolkata")).isoformat() == "2026-07-02"


def test_meal_local_date_falls_back_to_created_at():
    meal = SimpleNamespace(
        meal_time=None,
        created_at=datetime(2026, 7, 2, 9, 15),
    )

    assert meal_local_date(meal, ZoneInfo("Asia/Kolkata")).isoformat() == "2026-07-02"


def test_serialize_notification_keeps_user_visible_fields():
    created_at = datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)
    notification = SimpleNamespace(
        id=3,
        user_id=11,
        type="missed_breakfast",
        title="Breakfast not logged yet",
        message="Add breakfast when you get a minute.",
        status="unread",
        notification_date="2026-07-02",
        created_at=created_at,
    )

    result = serialize_notification(notification)

    assert result == {
        "id": 3,
        "user_id": 11,
        "type": "missed_breakfast",
        "title": "Breakfast not logged yet",
        "message": "Add breakfast when you get a minute.",
        "status": "unread",
        "notification_date": "2026-07-02",
        "created_at": created_at,
    }
