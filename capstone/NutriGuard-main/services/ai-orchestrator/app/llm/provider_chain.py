import logging
from typing import Any, Dict

from app.llm.gemini_client import _extract_json_object, gemini_client
from app.llm.openai_client import openai_client
from app.llm.token_cost import token_usage_payload

logger = logging.getLogger("nutriguard.orchestrator.llm_chain")


class LLMProviderChainError(RuntimeError):
    def __init__(self, message: str, metric_events: list[dict[str, Any]]):
        super().__init__(message)
        self.metric_events = metric_events


def _event(name: str, source: str, **payload) -> dict[str, Any]:
    return {
        "name": name,
        "source": source,
        "payload": payload,
    }


def _token_usage_event(agent_source: str, llm_response: dict[str, Any]) -> dict[str, Any]:
    return _event(
        "llm_token_usage",
        agent_source,
        **token_usage_payload(
            provider=llm_response.get("provider") or "unknown",
            model=llm_response.get("model") or "unknown",
            usage=llm_response.get("usage") or {},
        ),
    )


def generate_text_with_provider_fallback(prompt: str, agent_source: str) -> tuple[str, list[dict[str, Any]]]:
    metric_events: list[dict[str, Any]] = []

    try:
        response = gemini_client.generate_text_with_usage(prompt)
        metric_events.append(_token_usage_event(agent_source, response))
        return response["text"], metric_events
    except Exception as exc:
        logger.warning("Gemini failed for %s; trying OpenAI", agent_source, exc_info=True)
        metric_events.append(
            _event(
                "gemini_fallback",
                agent_source,
                fallback_to="openai",
                error_type=exc.__class__.__name__,
            )
        )

    try:
        response = openai_client.generate_text_with_usage(prompt)
        text = response["text"]
        metric_events.append(_token_usage_event(agent_source, response))
        metric_events.append(_event("openai_answer", agent_source, used_after="gemini_fallback"))
        return text, metric_events
    except Exception as exc:
        logger.warning("OpenAI failed for %s; using rule fallback", agent_source, exc_info=True)
        metric_events.append(
            _event(
                "openai_fallback",
                agent_source,
                fallback_to="rule_fallback",
                error_type=exc.__class__.__name__,
            )
        )
        metric_events.append(_event("rule_fallback", agent_source, reason="all_llm_providers_failed"))
        raise LLMProviderChainError("All LLM providers failed", metric_events) from exc


def generate_json_with_provider_fallback(prompt: str, agent_source: str) -> tuple[Dict[str, Any], list[dict[str, Any]]]:
    text, metric_events = generate_text_with_provider_fallback(prompt, agent_source)
    try:
        return _extract_json_object(text), metric_events
    except Exception as exc:
        metric_events.append(
            _event(
                "llm_parse_fallback",
                agent_source,
                fallback_to="rule_fallback",
                error_type=exc.__class__.__name__,
            )
        )
        raise LLMProviderChainError("LLM response could not be parsed", metric_events) from exc
