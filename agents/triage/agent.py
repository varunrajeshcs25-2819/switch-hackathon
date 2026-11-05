"""
PatchPilot Triage Agent

Primary responsibility: Understand incoming bug reports, classify them across
software architectural layers, assess severity strictly using empirical user
impact, identify contradictions between visual evidence and human reports,
and coordinate intelligent, focused task delegation for the Investigation Agent.

Capabilities:
- Multi-category defect classification (UI, functional, backend, API, validation, security, etc.)
- Impact-driven severity engine (strictly guards against inflating severity on visual drama alone)
- Contradiction & discrepancy detection (flags discrepancies between user reports & visual findings)
- Intelligent delegation formulating precise deliverables and determining if source code is required
- Independent evaluation of Investigation findings (challenging unproven or speculative conclusions)
- Dual-strategy parsing with JSON extraction and rich heuristic fallback
- Timezone-aware telemetry and audit logging
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from agents.triage.prompts import build_triage_prompt
from backend.models import (
    IssueClassification,
    SeverityLevel,
    ConfidenceLevel,
    AgentRole,
    PydanticTriageClassification,
    PydanticAgentActivity,
)

from google import genai
from google.genai import types

from backend.config import GEMINI_MODEL


class TriageAgent:
    """Triage Agent that classifies bug reports and coordinates investigation."""

    def __init__(self, api_key: str = "", max_retries: int = 2):
        self.api_key = api_key
        self.role = AgentRole.TRIAGE
        self.max_retries = max_retries
        self.activity_log: List[PydanticAgentActivity] = []

    async def triage_issue(
        self,
        issue_description: str,
        vision_observations: Optional[object] = None,
        screenshot_context: Optional[dict] = None,
        developer_notes: str = "",
    ) -> PydanticTriageClassification:
        """
        Analyze an incoming bug report, classify it, and generate an investigation task.

        Args:
            issue_description: Developer's description of the issue
            vision_observations: Structured observations from Vision Agent
            screenshot_context: Additional screenshot metadata
            developer_notes: Additional notes from the developer

        Returns:
            PydanticTriageClassification with classification, severity, and investigation task
        """
        desc_snippet = (issue_description[:80] + "...") if len(issue_description) > 80 else issue_description
        self._log_action(
            action="starting_triage",
            details=f"Triaging incident: '{desc_snippet}'",
        )

        triage_prompt = self._build_triage_prompt(
            issue_description=issue_description,
            vision_observations=vision_observations,
            developer_notes=developer_notes,
        )

        classification = await self._call_triage_model(
            triage_prompt,
            issue_description=issue_description,
            vision_observations=vision_observations,
        )

        self._log_action(
            action="triage_complete",
            details=(
                f"Classification={classification.classification}, "
                f"Severity={classification.severity}, "
                f"Objective='{classification.investigation_objective[:60]}...'"
            ),
        )

        return classification

    def _build_triage_prompt(
        self,
        issue_description: str,
        vision_observations: object = None,
        developer_notes: str = "",
    ) -> str:
        """Build the prompt for the Triage Agent."""
        return build_triage_prompt(
            issue_description=issue_description,
            vision_observations=vision_observations,
            developer_notes=developer_notes,
        )

    async def _call_triage_model(
        self,
        prompt: str,
        issue_description: str = "",
        vision_observations: Optional[object] = None,
    ) -> PydanticTriageClassification:
        """Call the reasoning model for triage classification with multi-provider retry and robust fallback."""
        from backend.config import GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY, GEMINI_MODEL

        # Priority 1: Groq if key present (high speed, large reasoning model)
        if GROQ_API_KEY:
            try:
                from groq import Groq
                client = Groq(api_key=GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are the Triage Agent. Return strictly valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=2500,
                )
                response_text = completion.choices[0].message.content or ""
                parsed = self._parse_triage_response(response_text)
                if parsed:
                    return parsed
            except Exception as e:
                self._log_action(
                    action="groq_triage_fallback",
                    details=f"Groq triage call failed: {str(e)[:120]}. Falling back to next provider.",
                    success=False,
                    error_message=str(e),
                )

        # Priority 2: Gemini
        if self.api_key:
            for attempt in range(self.max_retries + 1):
                try:
                    client = genai.Client(api_key=self.api_key)
                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=2500,
                        ),
                    )
                    response_text = response.text or ""
                    parsed = self._parse_triage_response(response_text)
                    if parsed:
                        return parsed
                except Exception as e:
                    self._log_action(
                        action=f"triage_call_retry_{attempt+1}",
                        details=f"Attempt {attempt+1} encountered error: {str(e)[:120]}",
                        success=False,
                        error_message=str(e),
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(1.5 ** attempt)

        # Priority 3: Sophisticated deterministic heuristic fallback
        return self._heuristic_fallback(issue_description, vision_observations)

    def _parse_triage_response(self, text: str) -> Optional[PydanticTriageClassification]:
        """Extract structured classification from model JSON output."""
        json_obj = self._extract_json(text)
        if not json_obj or not isinstance(json_obj, dict):
            return None

        # 1. Classification mapping
        raw_cls = str(json_obj.get("classification", "unknown")).lower().strip().replace(" ", "_").replace("-", "_")
        cls_map = {
            "ui": IssueClassification.UI_BUG,
            "ui_bug": IssueClassification.UI_BUG,
            "frontend": IssueClassification.UI_BUG,
            "frontend_bug": IssueClassification.UI_BUG,
            "functional": IssueClassification.FUNCTIONAL_BUG,
            "functional_bug": IssueClassification.FUNCTIONAL_BUG,
            "backend": IssueClassification.BACKEND_ERROR,
            "backend_error": IssueClassification.BACKEND_ERROR,
            "api": IssueClassification.API_INTEGRATION_ERROR,
            "api_error": IssueClassification.API_INTEGRATION_ERROR,
            "api_integration_error": IssueClassification.API_INTEGRATION_ERROR,
            "validation": IssueClassification.VALIDATION_ERROR,
            "validation_error": IssueClassification.VALIDATION_ERROR,
            "performance": IssueClassification.PERFORMANCE_ISSUE,
            "performance_issue": IssueClassification.PERFORMANCE_ISSUE,
            "security": IssueClassification.SECURITY_CONCERN,
            "security_concern": IssueClassification.SECURITY_CONCERN,
        }
        classification = cls_map.get(raw_cls, IssueClassification.UNKNOWN)

        # 2. Severity mapping
        raw_sev = str(json_obj.get("severity", "medium")).lower().strip()
        sev_map = {
            "critical": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW,
        }
        severity = sev_map.get(raw_sev, SeverityLevel.MEDIUM)

        # 3. Affected components
        raw_components = json_obj.get("affected_components") or []
        if isinstance(raw_components, str):
            raw_components = [raw_components]
        affected_components = [str(c).strip() for c in raw_components if str(c).strip()]

        # 4. Supporting observations
        raw_obs = json_obj.get("supporting_observations") or []
        if isinstance(raw_obs, str):
            raw_obs = [raw_obs]
        supporting_obs = [str(o).strip() for o in raw_obs if str(o).strip()]

        # 5. Missing information
        raw_missing = json_obj.get("missing_information") or []
        if isinstance(raw_missing, str):
            raw_missing = [raw_missing]
        missing_info = [str(m).strip() for m in raw_missing if str(m).strip()]

        # Include contradictions in missing/contextual observations
        contradictions = json_obj.get("contradictions_identified") or []
        if isinstance(contradictions, list):
            for c in contradictions:
                if c and str(c).strip():
                    supporting_obs.append(f"Contradiction identified: {str(c).strip()}")

        summary = str(json_obj.get("issue_summary") or "").strip()[:500]
        objective = str(json_obj.get("investigation_objective") or "").strip()[:500]
        if not objective:
            objective = f"Investigate root cause of {classification.value} affecting {', '.join(affected_components[:3]) or 'the application'}"

        reason = str(json_obj.get("reason_for_delegation") or "").strip()[:500]
        if not reason:
            reason = "Delegate to Investigation Agent for source-code root cause identification and fix"

        return PydanticTriageClassification(
            issue_id="",
            classification=classification,
            severity=severity,
            issue_summary=summary or "Incident classified by Triage Agent",
            affected_components=affected_components[:10],
            supporting_observations=supporting_obs[:10],
            missing_information=missing_info[:10],
            investigation_objective=objective,
            assigned_agent=AgentRole.INVESTIGATION,
            reason_for_delegation=reason,
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from string text."""
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        candidate = json_match.group(1).strip() if json_match else text

        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_substr = candidate[start : end + 1]
            try:
                return json.loads(json_substr)
            except Exception:
                cleaned = re.sub(r",\s*([\}\]])", r"\1", json_substr)
                try:
                    return json.loads(cleaned)
                except Exception:
                    pass
        return None

    def _heuristic_fallback(
        self,
        issue_description: str = "",
        vision_observations: Optional[object] = None,
    ) -> PydanticTriageClassification:
        """
        Sophisticated heuristic classification when model calls are unavailable.
        Evaluates actual keywords, visual evidence markers, and impact severity
        directly from the issue description and vision observations.
        """
        vision_text = ""
        if vision_observations:
            error_msgs = getattr(vision_observations, "error_messages", []) or []
            components = getattr(vision_observations, "affected_components", []) or []
            evidence = getattr(vision_observations, "evidence", []) or []
            vision_text = " ".join(error_msgs + components + evidence)

        text_lower = f"{issue_description} {vision_text}".lower()
        classification = IssueClassification.UNKNOWN
        severity = SeverityLevel.MEDIUM
        affected_components = []
        supporting_observations = []
        missing_info = []

        # 1. Security check (leak, token, secret, exploit)
        if re.search(r"\b(password|secret|api_key|token|leak|vulnerability|exploit|injection|auth bypass)\b", text_lower):
            classification = IssueClassification.SECURITY_CONCERN
            severity = SeverityLevel.CRITICAL
            supporting_observations.append("Security-sensitive credentials or authentication mechanism referenced")
        # 2. Backend & Server crash check
        elif re.search(r"\b(500|internal server error|traceback|exception|sql|database error|panic)\b", text_lower):
            classification = IssueClassification.BACKEND_ERROR
            if re.search(r"\b(login|checkout|register|registration|payment|billing|crash|unusable)\b", text_lower):
                severity = SeverityLevel.CRITICAL
                supporting_observations.append("Backend server error blocking core application workflow")
            else:
                severity = SeverityLevel.HIGH
                supporting_observations.append("Backend error detected with potential localized impact")
        # 3. API / Integration
        elif re.search(r"\b(cors|404|400|502|503|gateway|fetch failed|networkerror|api endpoint)\b", text_lower):
            classification = IssueClassification.API_INTEGRATION_ERROR
            severity = SeverityLevel.HIGH
            supporting_observations.append("Network or API communication failure observed")
        # 4. Validation error
        elif re.search(r"\b(validation|invalid|422|required field|format incorrect|password criteria)\b", text_lower):
            classification = IssueClassification.VALIDATION_ERROR
            severity = SeverityLevel.MEDIUM
            supporting_observations.append("Form validation constraints or rejected client input detected")
        # 5. UI Layout Bug
        elif re.search(r"\b(overlap|misaligned|overflow|broken layout|css|blank screen|whiteout|styling|clipped)\b", text_lower):
            classification = IssueClassification.UI_BUG
            if "unusable" in text_lower or "blank screen" in text_lower:
                severity = SeverityLevel.HIGH
            else:
                severity = SeverityLevel.LOW
            supporting_observations.append("Visual styling or component layout anomaly detected")
        # 6. Functional bug
        elif re.search(r"\b(button not working|click|submit does nothing|unresponsive|frozen)\b", text_lower):
            classification = IssueClassification.FUNCTIONAL_BUG
            severity = SeverityLevel.HIGH
            supporting_observations.append("Interactive element failed to execute expected behavior")

        # Preserve vision components if provided
        if vision_observations:
            for c in getattr(vision_observations, "affected_components", []) or []:
                if c and str(c).strip() not in affected_components:
                    affected_components.append(str(c).strip())

        # Extract components if visible in text
        for comp in ["login", "registration", "checkout", "navbar", "form", "table", "button", "input", "modal"]:
            if comp in text_lower and comp.title() not in affected_components:
                affected_components.append(comp.title())

        if not self.api_key:
            missing_info.append("No GEMINI_API_KEY configured; triage determined via empirical heuristic rules")
            missing_info.append("Application source code files required for investigation")

        return PydanticTriageClassification(
            issue_id="",
            classification=classification,
            severity=severity,
            issue_summary=f"Incident triaged as {classification.value} with {severity.value} severity",
            affected_components=affected_components or ["General Application"],
            supporting_observations=supporting_observations or ["Evaluated from incident description and visual observations"],
            missing_information=missing_info,
            investigation_objective=f"Investigate {classification.value} affecting {', '.join(affected_components) or 'application'} and identify root cause in source code",
            assigned_agent=AgentRole.INVESTIGATION,
            reason_for_delegation="Delegated to Investigation Agent for source code analysis and remediation",
        )

    def evaluate_investigation(
        self,
        investigation_findings: object,
        source_code_supplied: bool = False,
    ) -> Dict[str, Any]:
        """
        Rigorous evaluation of the Investigation Agent's deliverables.
        Checks if the investigation actually resolved the objective or needs to be challenged.
        """
        root_cause = getattr(investigation_findings, "suspected_root_cause", "") or ""
        fix = getattr(investigation_findings, "proposed_fix", "") or ""
        files = getattr(investigation_findings, "relevant_source_files", []) or []
        confidence = getattr(investigation_findings, "confidence", "low")

        challenges = []
        addressed = True

        # Challenge 1: Empty root cause
        if not root_cause.strip() or "not determined" in root_cause.lower() or "unable" in root_cause.lower():
            challenges.append("Investigation did not identify a definitive root cause")
            addressed = False

        # Challenge 2: Source code was needed but missing
        if not source_code_supplied:
            challenges.append("No source code was supplied to verify code-level conclusions")
            addressed = False
        elif not files:
            challenges.append("Source code was supplied but no specific relevant files were identified")
            addressed = False

        # Challenge 3: No proposed fix provided
        if not fix.strip():
            challenges.append("No proposed code fix or patch was provided")
            addressed = False

        return {
            "addressed": addressed,
            "confidence": confidence,
            "challenges": challenges,
            "verdict": "Accepted" if addressed else "Challenged / Incomplete",
        }

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
