import json
import logging
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
logger = logging.getLogger("nutriguard.orchestrator.gemini")


def _configured_api_keys(primary_key: Optional[str] = None) -> list[str]:
    raw_keys = os.getenv("GEMINI_API_KEYS", "")
    keys = [key.strip() for key in raw_keys.split(",") if key.strip()]
    fallback_key = primary_key or os.getenv("GEMINI_API_KEY")
    if fallback_key:
        keys.append(fallback_key.strip())

    unique_keys = []
    seen = set()
    for key in keys:
        if key and key not in seen:
            unique_keys.append(key)
            seen.add(key)
    return unique_keys


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "resource_exhausted" in text
        or "429" in text
        or "quota" in text
        or exc.__class__.__name__ == "ResourceExhausted"
    )


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_keys = _configured_api_keys(api_key)
        self.model_name = model_name or DEFAULT_MODEL
        self._models = {}
        self._key_index = 0

    @property
    def enabled(self) -> bool:
        return bool(self.api_keys)

    def _get_model(self, api_key: str):
        if not self.enabled:
            raise RuntimeError("GEMINI_API_KEY or GEMINI_API_KEYS is not set")

        if api_key not in self._models:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-generativeai is not installed. Run `pip install -r requirements.txt`."
                ) from exc

            genai.configure(api_key=api_key)
            self._models[api_key] = genai.GenerativeModel(self.model_name)

        return self._models[api_key]

    def _usage_from_response(self, response: Any) -> dict[str, int]:
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return {}
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        return {
            "input_tokens": input_tokens or 0,
            "output_tokens": output_tokens or 0,
            "total_tokens": total_tokens or ((input_tokens or 0) + (output_tokens or 0)),
        }

    def generate_text_with_usage(self, prompt: str) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("GEMINI_API_KEY or GEMINI_API_KEYS is not set")

        last_error = None
        key_count = len(self.api_keys)
        for offset in range(key_count):
            key_index = (self._key_index + offset) % key_count
            api_key = self.api_keys[key_index]
            try:
                response = self._get_model(api_key).generate_content(prompt)
                text = getattr(response, "text", None)
                if not text:
                    raise RuntimeError("Gemini returned an empty response")
                self._key_index = key_index
                return {
                    "text": text.strip(),
                    "provider": "gemini",
                    "model": self.model_name,
                    "usage": self._usage_from_response(response),
                }
            except Exception as exc:
                last_error = exc
                if not _is_quota_error(exc) or key_count == 1:
                    raise
                logger.warning(
                    "Gemini key quota/rate limit hit; trying next key key_index=%s total_keys=%s",
                    key_index + 1,
                    key_count,
                )

        if last_error:
            raise last_error
        raise RuntimeError("Gemini did not return a response")

    def generate_text(self, prompt: str) -> str:
        return self.generate_text_with_usage(prompt)["text"]

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        text = self.generate_text(prompt)
        return _extract_json_object(text)


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)

    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Gemini response did not contain a JSON object")
        cleaned = cleaned[start : end + 1]

    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response JSON must be an object")
    return parsed


gemini_client = GeminiClient()
