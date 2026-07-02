from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routes.admin import (
    api_latency_metrics,
    llm_fallback_metrics,
    percentile,
    require_admin,
    serialize_rag_eval,
)


def metric_event(name, source=None, payload=None, created_at=None):
    return SimpleNamespace(
        name=name,
        source=source,
        payload=payload,
        created_at=created_at or datetime(2026, 7, 2, tzinfo=timezone.utc),
    )


def test_percentile_handles_empty_and_sorted_values():
    assert percentile([], 0.95) == 0
    assert percentile([300, 100, 200], 0.95) == 300
    assert percentile([300, 100, 200], 0.5) == 200


def test_api_latency_metrics_groups_by_endpoint():
    events = [
        metric_event("api_request", payload={"method": "GET", "path": "/health", "duration_ms": 100, "status_code": 200}),
        metric_event("api_request", payload={"method": "POST", "path": "/users/login", "duration_ms": 300, "status_code": 200}),
        metric_event("api_request", payload={"method": "POST", "path": "/users/login", "duration_ms": 200, "status_code": 401}),
        metric_event("gemini_fallback", source="meal_analyzer"),
    ]

    result = api_latency_metrics(events)

    assert result["total_requests"] == 3
    assert result["average_ms"] == 200
    assert result["p95_ms"] == 300
    assert result["max_ms"] == 300
    assert result["by_endpoint"][0]["endpoint"] == "POST /users/login"
    assert result["by_endpoint"][0]["count"] == 2
    assert result["by_endpoint"][0]["latest_status"] == 401


def test_llm_fallback_metrics_returns_totals_and_agent_breakdown():
    events = [
        metric_event("gemini_fallback", source="meal_analyzer"),
        metric_event("openai_answer", source="meal_analyzer"),
        metric_event("gemini_fallback", source="report_agent"),
        metric_event("openai_fallback", source="report_agent"),
        metric_event("rule_fallback", source="report_agent"),
        metric_event("llm_parse_fallback", source="health_risk_agent"),
        metric_event("api_request", payload={"duration_ms": 20}),
    ]

    result = llm_fallback_metrics(events)

    assert result["gemini_fallback_total"] == 2
    assert result["openai_answer_total"] == 1
    assert result["openai_fallback_total"] == 1
    assert result["rule_fallback_total"] == 1
    assert result["parse_fallback_total"] == 1
    assert result["by_agent"]["meal_analyzer"]["gemini_fallback"] == 1
    assert result["by_agent"]["report_agent"]["rule_fallback"] == 1


def test_serialize_rag_eval_handles_empty_and_latest_run():
    assert serialize_rag_eval(None) == {"latest": None}

    run = SimpleNamespace(
        id=7,
        source="local_ragas",
        average_hit_rate=0.75,
        total_cases=4,
        passed_cases=3,
        metrics={"retrieval_metrics": {"context_recall": 0.75}},
        created_at=datetime(2026, 7, 2, 10, 30, tzinfo=timezone.utc),
    )

    result = serialize_rag_eval(run)

    assert result["latest"]["id"] == 7
    assert result["latest"]["source"] == "local_ragas"
    assert result["latest"]["average_hit_rate"] == 0.75
    assert result["latest"]["metrics"]["retrieval_metrics"]["context_recall"] == 0.75
    assert result["latest"]["created_at"] == "2026-07-02T10:30:00+00:00"


def test_require_admin_blocks_non_admin_users():
    require_admin(SimpleNamespace(is_admin=True))

    with pytest.raises(HTTPException) as exc:
        require_admin(SimpleNamespace(is_admin=False))

    assert exc.value.status_code == 403
