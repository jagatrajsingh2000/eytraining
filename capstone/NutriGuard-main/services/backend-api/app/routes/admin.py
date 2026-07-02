import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.models import DailyReport, MealLog, MetricEvent, Notification, RagEvalRun, ReportFeedback, User

router = APIRouter(prefix="/admin", tags=["admin"])
internal_router = APIRouter(prefix="/internal", tags=["internal"])
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "dev-internal-key")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(current_user: User) -> None:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


def local_date(value):
    if not value:
        return None
    timezone = ZoneInfo(APP_TIMEZONE)
    if value.tzinfo:
        return value.astimezone(timezone).date()
    return value.date()


def default_date_range():
    timezone = ZoneInfo(APP_TIMEZONE)
    today = datetime.now(timezone).date()
    return today - timedelta(days=6), today


def filter_by_date(items, start_date: date, end_date: date):
    return [
        item
        for item in items
        if (item_date := local_date(item.created_at)) and start_date <= item_date <= end_date
    ]


def daily_counts(items, start_date: date, end_date: date):
    days = max((end_date - start_date).days + 1, 1)
    counts = Counter(local_date(item.created_at) for item in items)
    return [
        {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "count": counts.get(start_date + timedelta(days=offset), 0),
        }
        for offset in range(days)
    ]


def percentile(values, percent):
    if not values:
        return 0
    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * percent)
    return round(sorted_values[index], 2)


def api_latency_metrics(metric_events):
    request_events = [event for event in metric_events if event.name == "api_request" and isinstance(event.payload, dict)]
    durations = [event.payload.get("duration_ms", 0) for event in request_events if event.payload.get("duration_ms") is not None]
    by_endpoint = defaultdict(list)
    latest_status = {}

    for event in request_events:
        payload = event.payload or {}
        duration = payload.get("duration_ms")
        if duration is None:
            continue
        endpoint = f"{payload.get('method', 'GET')} {payload.get('path', 'unknown')}"
        by_endpoint[endpoint].append(duration)
        latest_status[endpoint] = payload.get("status_code")

    endpoint_rows = []
    for endpoint, endpoint_durations in by_endpoint.items():
        endpoint_rows.append(
            {
                "endpoint": endpoint,
                "count": len(endpoint_durations),
                "average_ms": round(sum(endpoint_durations) / len(endpoint_durations), 2),
                "p95_ms": percentile(endpoint_durations, 0.95),
                "max_ms": round(max(endpoint_durations), 2),
                "latest_status": latest_status.get(endpoint),
            }
        )

    endpoint_rows.sort(key=lambda item: item["average_ms"], reverse=True)

    return {
        "total_requests": len(request_events),
        "average_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "p95_ms": percentile(durations, 0.95),
        "max_ms": round(max(durations), 2) if durations else 0,
        "by_endpoint": endpoint_rows[:10],
    }


def agent_latency_metrics(metric_events):
    latency_events = [
        event
        for event in metric_events
        if event.name == "agent_latency" and isinstance(event.payload, dict)
    ]
    durations = [
        event.payload.get("duration_ms", 0)
        for event in latency_events
        if event.payload.get("duration_ms") is not None
    ]
    by_agent = defaultdict(list)
    fallback_counts = Counter()

    for event in latency_events:
        payload = event.payload or {}
        duration = payload.get("duration_ms")
        if duration is None:
            continue
        agent = event.source or "unknown"
        by_agent[agent].append(duration)
        if payload.get("status") == "fallback":
            fallback_counts[agent] += 1

    agent_rows = []
    for agent, agent_durations in by_agent.items():
        agent_rows.append(
            {
                "agent": agent,
                "count": len(agent_durations),
                "average_ms": round(sum(agent_durations) / len(agent_durations), 2),
                "p95_ms": percentile(agent_durations, 0.95),
                "max_ms": round(max(agent_durations), 2),
                "fallback_count": fallback_counts[agent],
            }
        )

    agent_rows.sort(key=lambda item: item["average_ms"], reverse=True)

    return {
        "total_runs": len(latency_events),
        "average_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "p95_ms": percentile(durations, 0.95),
        "max_ms": round(max(durations), 2) if durations else 0,
        "by_agent": agent_rows,
    }


def token_cost_metrics(metric_events):
    usage_events = [
        event
        for event in metric_events
        if event.name == "llm_token_usage" and isinstance(event.payload, dict)
    ]
    by_provider = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_cost_usd": 0.0, "calls": 0})
    by_agent = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_cost_usd": 0.0, "calls": 0})

    for event in usage_events:
        payload = event.payload or {}
        provider = payload.get("provider") or "unknown"
        agent = event.source or "unknown"
        input_tokens = int(payload.get("input_tokens") or 0)
        output_tokens = int(payload.get("output_tokens") or 0)
        total_tokens = int(payload.get("total_tokens") or input_tokens + output_tokens)
        estimated_cost = float(payload.get("estimated_cost_usd") or 0)

        for bucket in (by_provider[provider], by_agent[agent]):
            bucket["input_tokens"] += input_tokens
            bucket["output_tokens"] += output_tokens
            bucket["total_tokens"] += total_tokens
            bucket["estimated_cost_usd"] = round(bucket["estimated_cost_usd"] + estimated_cost, 8)
            bucket["calls"] += 1

    total_input = sum(item["input_tokens"] for item in by_provider.values())
    total_output = sum(item["output_tokens"] for item in by_provider.values())
    total_tokens = sum(item["total_tokens"] for item in by_provider.values())
    total_cost = round(sum(item["estimated_cost_usd"] for item in by_provider.values()), 8)

    return {
        "calls": len(usage_events),
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_tokens,
        "estimated_cost_usd": total_cost,
        "by_provider": dict(by_provider),
        "by_agent": dict(by_agent),
    }


def llm_fallback_metrics(metric_events):
    event_names = {
        "gemini_fallback",
        "openai_answer",
        "openai_fallback",
        "rule_fallback",
        "llm_parse_fallback",
    }
    llm_events = [event for event in metric_events if event.name in event_names]
    by_name = Counter(event.name for event in llm_events)
    by_agent = defaultdict(lambda: defaultdict(int))

    for event in llm_events:
        by_agent[event.source or "unknown"][event.name] += 1

    return {
        "gemini_fallback_total": by_name["gemini_fallback"],
        "openai_answer_total": by_name["openai_answer"],
        "openai_fallback_total": by_name["openai_fallback"],
        "rule_fallback_total": by_name["rule_fallback"],
        "parse_fallback_total": by_name["llm_parse_fallback"],
        "by_agent": {agent: dict(counts) for agent, counts in by_agent.items()},
    }


def serialize_rag_eval(run: RagEvalRun | None) -> dict:
    if not run:
        return {
            "latest": None,
        }
    return {
        "latest": {
            "id": run.id,
            "source": run.source,
            "average_hit_rate": run.average_hit_rate or 0,
            "total_cases": run.total_cases or 0,
            "passed_cases": run.passed_cases or 0,
            "metrics": run.metrics or {},
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
    }


@internal_router.post("/rag-eval-results", response_model=dict)
def receive_rag_eval_result(
    payload: dict,
    db: Session = Depends(get_db),
    x_internal_api_key: str | None = Header(default=None),
):
    if INTERNAL_API_KEY and x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal API key")

    average_hit_rate = payload.get("average_hit_rate")
    cases = payload.get("cases") or []
    total_cases = payload.get("total_cases") or len(cases)
    passed_cases = payload.get("passed_cases")
    if passed_cases is None:
        passed_cases = sum(1 for item in cases if item.get("hit_rate", 0) >= 1)

    run = RagEvalRun(
        source=payload.get("source") or "local_ragas",
        average_hit_rate=average_hit_rate,
        total_cases=total_cases,
        passed_cases=passed_cases,
        metrics=payload,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"status": "saved", "id": run.id}


@router.get("/metrics", response_model=dict)
def get_admin_metrics(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    default_start, default_end = default_date_range()
    start_date = start_date or default_start
    end_date = end_date or default_end
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    all_meals = db.query(MealLog).all()
    all_reports = db.query(DailyReport).all()
    all_feedback = db.query(ReportFeedback).all()
    all_notifications = db.query(Notification).all()
    all_metric_events = db.query(MetricEvent).all()

    meals = filter_by_date(all_meals, start_date, end_date)
    reports = filter_by_date(all_reports, start_date, end_date)
    feedback = filter_by_date(all_feedback, start_date, end_date)
    notifications = filter_by_date(all_notifications, start_date, end_date)
    metric_events = filter_by_date(all_metric_events, start_date, end_date)

    completed_report_durations = []
    meals_by_id = {meal.id: meal for meal in meals}
    for report in reports:
        meal = meals_by_id.get(report.meal_log_id)
        if meal and meal.created_at and report.created_at:
            completed_report_durations.append((report.created_at - meal.created_at).total_seconds())

    feedback_by_category = defaultdict(lambda: {"liked": 0, "disliked": 0})
    feedback_totals = {"liked": 0, "disliked": 0}
    for item in feedback:
        if item.rating in feedback_totals:
            feedback_totals[item.rating] += 1
            feedback_by_category[item.category or "unknown"][item.rating] += 1

    missed_notifications = [item for item in notifications if (item.type or "").startswith("missed_")]
    unread_notifications = [item for item in notifications if item.status == "unread"]
    failed_meals = [meal for meal in meals if (meal.status or "").upper() in {"ERROR", "FAILED"}]
    fallback_events = [event for event in metric_events if event.name == "gemini_fallback"]
    llm_fallbacks = llm_fallback_metrics(metric_events)
    latest_rag_eval = db.query(RagEvalRun).order_by(RagEvalRun.created_at.desc()).first()

    return {
        "users": {
            "total": db.query(User).count(),
            "admins": db.query(User).filter(User.is_admin.is_(True)).count(),
        },
        "date_range": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "meals": {
            "total": len(meals),
            "submitted_per_day": daily_counts(meals, start_date, end_date),
        },
        "reports": {
            "completed_total": len(reports),
            "completed_per_day": daily_counts(reports, start_date, end_date),
            "failed_total": len(failed_meals),
            "average_processing_seconds": round(sum(completed_report_durations) / len(completed_report_durations), 2)
            if completed_report_durations
            else 0,
        },
        "feedback": {
            "total": len(feedback),
            "liked": feedback_totals["liked"],
            "disliked": feedback_totals["disliked"],
            "by_category": dict(feedback_by_category),
        },
        "notifications": {
            "missed_meal_total": len(missed_notifications),
            "unread_total": len(unread_notifications),
        },
        "gemini": {
            "fallback_total": len(fallback_events),
            "fallback_by_source": dict(Counter(event.source or "unknown" for event in fallback_events)),
        },
        "llm_fallbacks": llm_fallbacks,
        "api_latency": api_latency_metrics(metric_events),
        "agent_latency": agent_latency_metrics(metric_events),
        "token_cost": token_cost_metrics(metric_events),
        "rag_eval": serialize_rag_eval(latest_rag_eval),
    }
