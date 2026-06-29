import json
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or DEFAULT_MODEL
        self._model = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _get_model(self):
        if not self.enabled:
            raise RuntimeError("GEMINI_API_KEY is not set")

        if self._model is None:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-generativeai is not installed. Run `pip install -r requirements.txt`."
                ) from exc

            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)

        return self._model

    def generate_text(self, prompt: str) -> str:
        response = self._get_model().generate_content(prompt)
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text.strip()

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
