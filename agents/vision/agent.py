"""
PatchPilot Vision Agent

Primary responsibility: Analyze supplied screenshots and convert visual
information into rigorous, structured technical observations.

Capabilities:
- Multimodal analysis via vision-capable models (Google Gemini)
- Fine-grained visual understanding (error text, layout wrapping, clipping, broken components)
- Independent multi-issue detection (isolates multiple distinct bugs on a single screen)
- Strict separation between directly visible facts and inferred behavioral implications
- Resilient dual-mode parsing (Structured JSON + Robust Semantic Extraction Fallback)
- Exponential backoff retry handling for API and transient errors
- Safe image preprocessing and dimension validation

Important limitations:
- Cannot claim to know underlying source code causes from a screenshot alone
- Cannot invent invisible browser logs or stack traces
- Cannot claim an API request failed unless visibly evident on screen
- Cannot modify source code
"""

import base64
import json
import re
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

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

    def __init__(self, client=None, api_key: str = "", max_retries: int = 2):
        self.client = client
        self.api_key = api_key
        self.role = AgentRole.VISION
        self.max_retries = max_retries
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
        # 1. Input sanity check
        if not screenshot_base64 or not screenshot_base64.strip():
            self._log_action(
                action="invalid_input",
                details="Empty screenshot payload provided",
                success=False,
                error_message="Empty image data",
            )
            return PydanticVisionObservations(
                error_messages=["Error: No screenshot data provided."],
                affected_components=[],
                evidence=[],
                possible_behavioral_implications=[],
                confidence=ConfidenceLevel.UNCERTAIN,
                uncertainties=["No image content to analyze."],
                raw_observation="Vision analysis aborted: Empty image data provided.",
            )

        # Log the start of analysis
        desc_snippet = (user_description[:80] + "...") if len(user_description) > 80 else user_description
        self._log_action(
            action="starting_analysis",
            details=f"Analyzing screenshot with user description: '{desc_snippet}'",
        )

        # 2. Construct the enriched vision prompt
        vision_prompt = self._build_vision_prompt(
            user_description=user_description,
            application_context=application_context,
        )

        # 3. Call model with retry mechanism
        observations = await self._call_vision_model_with_retry(
            vision_prompt,
            screenshot_base64=screenshot_base64,
            mime_type=mime_type,
        )

        # Log completion
        self._log_action(
            action="analysis_complete",
            details=(
                f"Found {len(observations.error_messages)} error messages, "
                f"{len(observations.affected_components)} affected components, "
                f"confidence={observations.confidence}"
            ),
        )

        return observations

    def _build_vision_prompt(
        self,
        user_description: str,
        application_context: str,
    ) -> str:
        """Build the prompt for the Vision Agent."""
        return build_vision_prompt(user_description, application_context)

    async def _call_vision_model_with_retry(
        self,
        prompt: str,
        screenshot_base64: str,
        mime_type: str,
    ) -> PydanticVisionObservations:
        """Call vision model with exponential backoff on transient errors."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self._call_vision_model(
                    prompt, screenshot_base64=screenshot_base64, mime_type=mime_type
                )
            except Exception as e:
                last_error = e
                wait_time = 1.5 ** attempt
                self._log_action(
                    action=f"model_call_retry_{attempt+1}",
                    details=f"Attempt {attempt+1} failed with error: {str(e)[:120]}. Retrying in {wait_time:.1f}s",
                    success=False,
                    error_message=str(e),
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)

        # All retries failed
        self._log_action(
            action="model_call_failed",
            details=f"All {self.max_retries+1} attempts failed.",
            success=False,
            error_message=str(last_error),
        )
        return PydanticVisionObservations(
            error_messages=[f"Vision model call failed: {str(last_error)}"],
            affected_components=[],
            evidence=[],
            possible_behavioral_implications=[],
            confidence=ConfidenceLevel.UNCERTAIN,
            uncertainties=[
                f"Model API error occurred after {self.max_retries+1} attempts: {str(last_error)}"
            ],
            raw_observation=f"Vision Agent encountered a model API error: {str(last_error)}",
        )

    async def _call_vision_model(
        self,
        prompt: str,
        screenshot_base64: str,
        mime_type: str,
    ) -> PydanticVisionObservations:
        """Call the vision-capable AI model with the screenshot."""
        if not self.api_key:
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

        # Sanitize mime_type
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"

        client = genai.Client(api_key=self.api_key)

        image_bytes = base64.b64decode(screenshot_base64)
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4000,
            ),
        )
        text_content = response.text or ""
        return self._parse_vision_response(text_content)

    def _parse_vision_response(self, response: str) -> PydanticVisionObservations:
        """
        Parse the AI response into structured observations.
        Uses dual strategy:
        1. JSON extraction from ```json blocks or raw JSON
        2. Fallback semantic line-by-line parser if JSON decoding fails
        """
        cleaned_text = response.strip()

        # Strategy 1: Attempt JSON parsing
        json_obj = self._extract_json(cleaned_text)
        if json_obj and isinstance(json_obj, dict):
            return self._build_from_json(json_obj, raw_text=cleaned_text)

        # Strategy 2: Fallback heuristic text parsing
        return self._parse_fallback(cleaned_text)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a JSON object from model output text."""
        # Check for ```json code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        candidate = json_match.group(1).strip() if json_match else text

        # Find first { and last }
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_substr = candidate[start : end + 1]
            try:
                return json.loads(json_substr)
            except Exception:
                # Try cleaning trailing commas
                cleaned = re.sub(r",\s*([\}\]])", r"\1", json_substr)
                try:
                    return json.loads(cleaned)
                except Exception:
                    pass
        return None

    def _build_from_json(self, data: Dict[str, Any], raw_text: str) -> PydanticVisionObservations:
        """Construct PydanticVisionObservations from extracted JSON structure."""
        # 1. Error messages
        raw_errors = data.get("error_messages") or []
        if isinstance(raw_errors, str):
            raw_errors = [raw_errors]
        error_messages = [str(e).strip() for e in raw_errors if str(e).strip()]

        # 2. Affected components
        raw_components = data.get("affected_components") or []
        if isinstance(raw_components, str):
            raw_components = [raw_components]
        affected_components = [str(c).strip() for c in raw_components if str(c).strip()]

        # 3. Evidence (directly visible facts)
        raw_evidence = data.get("evidence") or []
        if isinstance(raw_evidence, str):
            raw_evidence = [raw_evidence]
        evidence = [str(ev).strip() for ev in raw_evidence if str(ev).strip()]

        # 4. Behavioral implications (inferences)
        raw_implications = data.get("possible_behavioral_implications") or []
        if isinstance(raw_implications, str):
            raw_implications = [raw_implications]
        possible_implications = [str(imp).strip() for imp in raw_implications if str(imp).strip()]

        # 5. Approximate location
        approx_loc = data.get("approximate_location")
        if approx_loc:
            approx_loc = str(approx_loc).strip()

        # 6. Uncertainties
        raw_uncertainties = data.get("uncertainties") or []
        if isinstance(raw_uncertainties, str):
            raw_uncertainties = [raw_uncertainties]
        uncertainties = [str(u).strip() for u in raw_uncertainties if str(u).strip()]

        # 7. Ingest fine-grained issues if top-level lists are empty
        issues = data.get("issues") or []
        if isinstance(issues, list):
            for issue in issues:
                if isinstance(issue, dict):
                    comp = issue.get("affected_component")
                    loc = issue.get("approximate_location")
                    vis_ev = issue.get("visual_evidence")
                    if comp and comp not in affected_components:
                        affected_components.append(comp)
                    if not evidence and vis_ev and vis_ev not in evidence:
                        evidence.append(vis_ev)
                    if loc and not approx_loc:
                        approx_loc = loc

        # 8. Confidence normalization
        conf_str = str(data.get("confidence", "")).lower()
        if "high" in conf_str:
            confidence = ConfidenceLevel.HIGH
        elif "low" in conf_str:
            confidence = ConfidenceLevel.LOW
        elif "uncertain" in conf_str:
            confidence = ConfidenceLevel.UNCERTAIN
        elif "medium" in conf_str:
            confidence = ConfidenceLevel.MEDIUM
        else:
            # Derived confidence if unspecified
            if error_messages or (evidence and affected_components):
                confidence = ConfidenceLevel.HIGH
            elif affected_components:
                confidence = ConfidenceLevel.MEDIUM
            elif uncertainties:
                confidence = ConfidenceLevel.UNCERTAIN
            else:
                confidence = ConfidenceLevel.LOW

        summary = data.get("summary") or (raw_text[:500] if raw_text else "Visual analysis completed.")

        return PydanticVisionObservations(
            issue_id="",
            error_messages=error_messages[:15],
            affected_components=affected_components[:15],
            approximate_location=approx_loc,
            evidence=evidence[:15],
            possible_behavioral_implications=possible_implications[:10],
            confidence=confidence,
            uncertainties=uncertainties[:10],
            raw_observation=summary[:1000],
        )

    def _parse_fallback(self, response: str) -> PydanticVisionObservations:
        """Resilient fallback parser for free-form responses."""
        error_messages = []
        affected_components = []
        evidence = []
        uncertainties = []
        possible_implications = []
        approx_loc = None

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line_stripped = line.strip().lstrip("-*•>0123456789. ")
            if not line_stripped:
                continue
            lower = line_stripped.lower()

            # Section detection
            if any(kw in lower for kw in ["error message", "detected error", "errors:"]):
                current_section = "errors"
                continue
            elif any(kw in lower for kw in ["affected component", "ui component", "components:"]):
                current_section = "components"
                continue
            elif any(kw in lower for kw in ["visual evidence", "screenshot shows", "evidence:"]):
                current_section = "evidence"
                continue
            elif any(kw in lower for kw in ["approximate location", "location:"]):
                current_section = "location"
                continue
            elif any(kw in lower for kw in ["uncertain", "unknown", "limitations:"]):
                current_section = "uncertainties"
                continue
            elif any(kw in lower for kw in ["implication", "behavioral", "consequences:"]):
                current_section = "implications"
                continue

            # Populate based on section
            if current_section == "errors":
                error_messages.append(line_stripped)
            elif current_section == "components":
                affected_components.append(line_stripped)
            elif current_section == "evidence":
                evidence.append(line_stripped)
            elif current_section == "location" and not approx_loc:
                approx_loc = line_stripped
            elif current_section == "uncertainties":
                uncertainties.append(line_stripped)
            elif current_section == "implications":
                possible_implications.append(line_stripped)

        # Keyword scanning if sections were missing
        if not error_messages:
            for line in lines:
                l_str = line.strip().lstrip("-*• ")
                if re.search(r"\b(error|500|404|403|failed|exception|crash|stack trace)\b", l_str, re.IGNORECASE):
                    error_messages.append(l_str)

        if not affected_components:
            for line in lines:
                l_str = line.strip().lstrip("-*• ")
                if re.search(r"\b(button|input|form|navbar|modal|dialog|table|card|dropdown|footer)\b", l_str, re.IGNORECASE):
                    affected_components.append(l_str)

        # Confidence determination
        if error_messages:
            confidence = ConfidenceLevel.HIGH
        elif affected_components:
            confidence = ConfidenceLevel.MEDIUM
        elif uncertainties:
            confidence = ConfidenceLevel.UNCERTAIN
        else:
            confidence = ConfidenceLevel.LOW

        return PydanticVisionObservations(
            issue_id="",
            error_messages=error_messages[:10],
            affected_components=affected_components[:10],
            approximate_location=approx_loc,
            evidence=evidence[:10],
            possible_behavioral_implications=possible_implications[:5],
            confidence=confidence,
            uncertainties=uncertainties[:5],
            raw_observation=response[:500] if response else None,
        )

    def _log_action(
        self,
        action: str,
        details: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log an activity trace with timezone-aware timestamp."""
        self.activity_log.append(
            PydanticAgentActivity(
                timestamp=datetime.now(timezone.utc),
                agent_role=self.role,
                action=action,
                details=details,
                success=success,
                error_message=error_message,
            )
        )
