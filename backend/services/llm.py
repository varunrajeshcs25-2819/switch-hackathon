"""Thin async Gemini REST client that returns parsed JSON.

Uses httpx directly (no SDK) so there is no version drift to debug during a hackathon.
"""

import json
import re
from typing import Any, Dict, Optional

import httpx

from backend.config import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL, LLM_TIMEOUT_SECONDS


class LLMError(Exception):
    pass


def model_configured() -> bool:
    return bool(GEMINI_API_KEY)


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("Model did not return valid JSON")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model returned malformed JSON: {exc}")
    if not isinstance(parsed, dict):
        raise LLMError("Model JSON was not an object")
    return parsed


async def generate_json(
    system_prompt: str,
    user_text: str,
    image_base64: Optional[str] = None,
    mime_type: str = "image/png",
) -> Dict[str, Any]:
    if not model_configured():
        raise LLMError("GEMINI_API_KEY is not configured")

    parts = [{"text": user_text}]
    if image_base64:
        parts.append({"inlineData": {"mimeType": mime_type, "data": image_base64}})

    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent"
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:
        raise LLMError(f"Gemini request failed: {exc}")

    if response.status_code != 200:
        raise LLMError(f"Gemini returned HTTP {response.status_code}: {response.text[:300]}")

    try:
        data = response.json()
        text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMError(f"Unexpected Gemini response shape: {exc}")

    return _extract_json(text)
