"""Vision Agent: describes what is visibly wrong in a screenshot."""

from backend.agents.common import as_float, as_str, as_str_list
from backend.models import PydanticVisionObservations
from backend.services import llm

SYSTEM_PROMPT = """You are the Vision Agent in a software debugging team.
You are given a screenshot of a software problem and an optional user description.
Report ONLY what is visible. Never guess about code you cannot see.
Return a JSON object with keys:
  summary (string), visible_elements (list of strings), visible_error_messages (list of
  strings, copied exactly as shown), anomalies (list of strings: things that look broken,
  misaligned, missing or inconsistent), ui_state (string), confidence (number 0-1)."""


class VisionAgent:
    async def analyze_screenshot(
        self, screenshot_base64: str, mime_type: str = "image/png", user_description: str = ""
    ) -> PydanticVisionObservations:
        if not llm.model_configured():
            return PydanticVisionObservations(
                summary="Screenshot received but not analyzed: no model is configured (set GEMINI_API_KEY).",
                confidence=0.0,
                analyzed_by_model=False,
            )

        data = await llm.generate_json(
            SYSTEM_PROMPT,
            f"User description: {user_description or '(none provided)'}",
            image_base64=screenshot_base64,
            mime_type=mime_type,
        )
        return PydanticVisionObservations(
            summary=as_str(data.get("summary")),
            visible_elements=as_str_list(data.get("visible_elements")),
            visible_error_messages=as_str_list(data.get("visible_error_messages")),
            anomalies=as_str_list(data.get("anomalies")),
            ui_state=as_str(data.get("ui_state")),
            confidence=as_float(data.get("confidence")),
            analyzed_by_model=True,
        )
