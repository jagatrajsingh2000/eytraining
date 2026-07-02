import os
from typing import Any, Callable


SENSITIVE_KEYS = {"health_report_text"}
MAX_TEXT_LENGTH = 1200


def _enabled() -> bool:
    return os.getenv("LANGSMITH_TRACING", "").lower() in {"1", "true", "yes", "on"}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if key in SENSITIVE_KEYS else _sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str) and len(value) > MAX_TEXT_LENGTH:
        return f"{value[:MAX_TEXT_LENGTH]}...[truncated]"
    return value


def _sanitize_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    return _sanitize(inputs)


def _sanitize_outputs(outputs: Any) -> Any:
    return _sanitize(outputs)


def traceable(name: str, run_type: str = "chain") -> Callable:
    def decorator(func: Callable) -> Callable:
        if not _enabled():
            return func

        try:
            from langsmith import traceable as langsmith_traceable
        except Exception:
            return func

        try:
            return langsmith_traceable(
                name=name,
                run_type=run_type,
                process_inputs=_sanitize_inputs,
                process_outputs=_sanitize_outputs,
            )(func)
        except TypeError:
            return langsmith_traceable(name=name, run_type=run_type)(func)
        except Exception:
            return func

    return decorator
