"""
PatchPilot Vision Agent

Primary responsibility: Analyze supplied screenshots and convert visual
information into useful technical observations.

This agent uses a vision-capable AI model (Claude 3.5 Sonnet or GPT-4o)
to examine screenshots and identify:
- Visible error messages
- UI anomalies and unexpected behavior
- Readable text and error messages
- Affected UI components
- Suspicious elements (broken layouts, missing elements, overlapping components, etc.)
- Distinguishing actual errors from design preferences

The Vision Agent sends its findings to the Triage Agent through the
shared Switch/SDK conversation layer.

Important limitations:
- Cannot claim to know the underlying source-code cause from a screenshot alone
- Cannot invent invisible browser logs
- Cannot claim an API request failed unless evidence is supplied
- Cannot claim to have executed tests
- Cannot modify source code
"""

import base64
import asyncio
from typing import List, Optional

from backend.config import GEMINI_MODEL

from agents.vision.prompts import build_vision_prompt
from backend.models import (
    PydanticVisionObservations,
    ConfidenceLevel,
    AgentRole,
    PydanticAgentActivity,
)


class VisionAgent:
    """Vision Agent that analyzes screenshots using AI vision models."""

    def __init__(self, client=None, api_key: str = ""):
        self.client = client
        self.api_key = api_key
        self.role = AgentRole.VISION
        self.activity_log: List[PydanticAgentActivity] = []

    async def analyze_screenshot(
        self,
        screenshot_base64: str,
        mime_type: str = "image/png",
        user_description: str = "",
        application_context: str = "",
    ) -> PydanticVisionObservations:
        """
        Analyze a screenshot and produce structured observations.

        Args:
            screenshot_base64: Base64-encoded screenshot image
            mime_type: MIME type of the image (image/png, image/jpeg, etc.)
            user_description: Optional developer description of the issue
            application_context: Optional context about the application

        Returns:
            PydanticVisionObservations containing structured findings
        """
        # Log the start of analysis
        self._log_action(
            action="starting_analysis",
            details=f"Analyzing screenshot with user description: '{user_description[:80]}...'",
        )

        # Construct the vision prompt
        vision_prompt = self._build_vision_prompt(
            user_description=user_description,
            application_context=application_context,
        )

        # Send to Claude model with image via Anthropic
        observations = await self._call_vision_model(
            vision_prompt,
            screenshot_base64=screenshot_base64,
            mime_type=mime_type,
        )

        # Log completion
        self._log_action(
            action="analysis_complete",
            details=f"Found {len(observations.error_messages)} error messages, "
                    f"{len(observations.affected_components)} affected components",
        )

        return observations

    def _build_vision_prompt(
        self,
        user_description: str,
        application_context: str,
    ) -> str:
        """Build the prompt for the Vision Agent (text lives in prompts.py)."""
        return build_vision_prompt(user_description, application_context)
    async def _call_vision_model(
        self,
        prompt: str,
        screenshot_base64: str,
        mime_type: str,
    ) -> PydanticVisionObservations:
        """Call the vision-capable AI model with the screenshot."""

        if not self.api_key:
            # No API key: return honest, clearly-marked observations instead of inventing findings
            return PydanticVisionObservations(
                error_messages=[],
                affected_components=[],
                evidence=[],
                possible_behavioral_implications=[],
                confidence=ConfidenceLevel.UNCERTAIN,
                uncertainties=[
                    "No GEMINI_API_KEY configured, so the screenshot was not analyzed by a vision model."
                ],
                raw_observation=(
                    "Vision analysis skipped: no GEMINI_API_KEY configured, so the "
                    "screenshot was not analyzed. No visual findings are claimed."
                ),
            )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        # Prepare the multimodal content: prompt text + the screenshot bytes
        image_part = types.Part.from_bytes(
            data=base64.b64decode(screenshot_base64),
            mime_type=mime_type,
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=4000,
            ),
        )
        text_content = response.text or ""

        # Parse the response into structured observations
        return self._parse_vision_response(text_content)

    def _parse_vision_response(self, response: str) -> PydanticVisionObservations:
        """Parse the AI response into structured observations."""

        # Extract error messages - look for common patterns
        error_messages = []
        affected_components = []
        evidence = []
        uncertainties = []
        possible_implications = []

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line_stripped = line.strip()
            lower = line_stripped.lower()

            # Detect sections
            if any(kw in lower for kw in ["error:", "error summary", "detected"]):
                current_section = "errors"
            elif any(kw in lower for kw in ["component", "affected", "ui element"]):
                current_section = "components"
            elif any(kw in lower for kw in ["evidence", "screenshot shows"]):
                current_section = "evidence"
            elif any(kw in lower for kw in ["confidence", "certainty"]):
                current_section = "confidence"
            elif any(kw in lower for kw in ["uncertain", "unknown", "limitation"]):
                current_section = "uncertainties"
            elif any(kw in lower for kw in ["implication", "behaviour", "affects"]):
                current_section = "implications"
            else:
                current_section = None

            # Parse based on section
            if current_section == "errors" and line_stripped:
                error_messages.append(line_stripped)
            elif current_section == "components" and line_stripped:
                affected_components.append(line_stripped)
            elif current_section == "evidence" and line_stripped:
                evidence.append(line_stripped)
            elif current_section == "uncertainties" and line_stripped:
                uncertainties.append(line_stripped)
            elif current_section == "implications" and line_stripped:
                possible_implications.append(line_stripped)

        # If no sections detected, try to extract key info from the full text
        if not error_messages and "error" in response.lower():
            for line in lines:
                if any(kw in line.lower() for kw in ["error", "500", "404", "failed", "exception"]):
                    error_messages.append(line.strip())

        if not affected_components and "component" in response.lower():
            for line in lines:
                if any(word in line.lower() for word in ["button", "form", "input", "page", "error"]):
                    affected_components.append(line.strip())

        # Set confidence based on what we found
        if error_messages:
            confidence = ConfidenceLevel.HIGH
        elif affected_components:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        return PydanticVisionObservations(
            issue_id="",  # will be set by the system
            error_messages=error_messages[:10],  # limit to 10
            affected_components=affected_components[:10],
            evidence=evidence[:10],
            possible_behavioral_implications=possible_implications[:5],
            confidence=confidence,
            uncertainties=uncertainties[:5],
            raw_observation=response[:500] if response else None,  # first 500 chars as summary
        )

    def _log_action(
        self,
        action: str,
        details: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log an activity trace."""
        from datetime import datetime
        self.activity_log.append(
            {
                "timestamp": datetime.utcnow(),
                "agent_role": self.role,
                "action": action,
                "details": details,
                "success": success,
                "error_message": error_message,
            }
        )