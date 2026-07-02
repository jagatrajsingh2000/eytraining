import time
from typing import Any


def start_timer() -> float:
    return time.perf_counter()


def metric_event(name: str, source: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "source": source,
        "payload": payload,
    }


def agent_latency_event(
    agent: str,
    started_at: float,
    *,
    status: str,
    trace_id: str | None = None,
    meal_log_id: int | None = None,
) -> dict[str, Any]:
    return metric_event(
        "agent_latency",
        agent,
        {
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "status": status,
            "trace_id": trace_id,
            "meal_log_id": meal_log_id,
        },
    )
