import json
import logging
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from app.llm.gemini_client import _extract_json_object

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
logger = logging.getLogger("nutriguard.orchestrator.openai")


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or DEFAULT_MODEL

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate_text(self, prompt: str) -> str:
        if not self.enabled:
            raise RuntimeError("OPENAI_API_KEY is not set")

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            data=json.dumps(
                {
                    "model": self.model_name,
                    "temperature": 0.2,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices") or []
        text = ""
        if choices:
            text = ((choices[0].get("message") or {}).get("content") or "").strip()
        if not text:
            raise RuntimeError("OpenAI returned an empty response")
        return text

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        text = self.generate_text(prompt)
        return _extract_json_object(text)


openai_client = OpenAIClient()
