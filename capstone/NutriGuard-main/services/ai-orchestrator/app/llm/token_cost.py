from typing import Any


OPENAI_INPUT_COST_PER_1M = 0.15
OPENAI_OUTPUT_COST_PER_1M = 0.60
GEMINI_INPUT_COST_PER_1M = 0.0
GEMINI_OUTPUT_COST_PER_1M = 0.0


def _provider_rates(provider: str) -> tuple[float, float]:
    if provider == "openai":
        return OPENAI_INPUT_COST_PER_1M, OPENAI_OUTPUT_COST_PER_1M
    if provider == "gemini":
        return GEMINI_INPUT_COST_PER_1M, GEMINI_OUTPUT_COST_PER_1M
    return 0.0, 0.0


def estimate_cost_usd(provider: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = _provider_rates(provider)
    return round(
        (input_tokens / 1_000_000 * input_rate)
        + (output_tokens / 1_000_000 * output_rate),
        8,
    )


def token_usage_payload(
    *,
    provider: str,
    model: str,
    usage: dict[str, Any],
) -> dict[str, Any]:
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)

    return {
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimate_cost_usd(provider, input_tokens, output_tokens),
    }
