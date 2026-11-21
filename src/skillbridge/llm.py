"""Thin wrapper around the Gemini API."""
from __future__ import annotations

import json
import os
import re
import time


class GeminiError(RuntimeError):
    pass


def is_quota_error(exc: Exception | str) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def parse_json(text: str) -> dict:
    """Parse a model reply as JSON, tolerating ```json fences and stray text."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, temperature: float = 0.2):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        self.temperature = temperature
        if not self.api_key:
            raise GeminiError("No Gemini API key found. Set GEMINI_API_KEY or paste one in the app sidebar.")

    def generate(self, prompt: str, json_mode: bool = True) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover
            raise GeminiError("Install the SDK first: pip install google-genai") from exc

        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            response_mime_type="application/json" if json_mode else "text/plain",
            http_options=types.HttpOptions(timeout=60000),  # 60 s: fail instead of hanging
        )
        response = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=self.model, contents=prompt, config=config)
                break
            except Exception as exc:
                msg = str(exc)
                # Retry timeouts / overload. Never retry a quota error: it only burns more quota.
                if not is_quota_error(msg) and ("503" in msg or "504" in msg) and attempt < 2:
                    time.sleep(10 * (2 ** attempt))
                    continue
                raise GeminiError(f"Gemini request failed: {exc}") from exc
        if response is None or not response.text:
            raise GeminiError("Gemini returned an empty answer (possibly blocked by a safety filter).")
        return response.text
