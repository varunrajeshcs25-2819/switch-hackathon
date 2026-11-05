"""PatchPilot Triage Agent

Primary responsibility: Understand incoming bug reports, classify them,
estimate severity, and coordinate investigation.

The Triage Agent receives:
- Vision Agent observations
- Original screenshot context
- Developer descriptions
- Previous findings from the shared Switch conversation

Responsibilities:
1. Understand the incoming observations
2. Determine whether the report represents:
   - UI bug
   - Functional bug
   - Backend error
   - API/integration error
   - Validation error
   - Performance issue
   - Security-related concern
   - Unknown or insufficiently specified issue
3. Estimate severity using consistent classification:
   - Critical.
   - High.
   - Medium.
   - Low.
4. Identify potentially affected components.
5. Identify missing information required for investigation.
6. Determine whether source code is required.
7. Create a concise investigation task.
8. Delegate the investigation to the Investigation Agent through Switch.
9. Monitor the response.
10. Evaluate whether the investigation addresses the original issue.

Important limitations:
- Must not invent root causes
- Must not claim the issue has been fixed
- Must not replace the Vision Agent's observations
- Must not make unsupported assumptions about the codebase

Severity considerations:
- Critical: The application or an essential workflow is unusable, or there is strong evidence of a serious security or data-integrity problem.
- High: An important feature is broken and significantly affects users.
- Medium: A feature behaves incorrectly but a workaround exists.
- Low: A minor visual or functional issue with limited impact.

Do not assign severity based solely on dramatic-looking screenshots. Consider actual impact and available evidence.
"""

import asyncio
import json
from typing import List, Optional

from agents.triage.prompts import build_triage_prompt
from backend.models import (
    IssueClassification,
    SeverityLevel,
    ConfidenceLevel,
    AgentRole,
    PydanticTriageClassification,
    PydanticAgentActivity,
    IssueStatus,
)

from google import genai
from google.genai import types

from backend.config import GEMINI_MODEL


class TriageAgent:
    """Triage Agent that classifies bug reports and coordinates investigation."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.role = AgentRole.TRIAGE
        self.activity_log: List[PydanticAgentActivity] = []

    async def triage_issue(
        self,
        issue_description: str,
        vision_observations: Optional[object] = None,
        screenshot_context: Optional[dict] = None,
        developer_notes: str = "",
    ) -> PydanticTriageClassification:
        """Analyze an incoming bug report and classify it.

        Args:
            issue_description: Developer's description of the issue
            vision_observations: Structured observations from Vision Agent
            screenshot_context: Additional screenshot metadata
            developer_notes: Additional notes from the developer

        Returns:
            PydanticTriageClassification with classification and investigation task
        """
        # Log the start of triage
        self._log_action(
            action="starting_triage",
            details=f"Triage issue: '{issue_description[:80]}...'",
        )

        # Build the triage prompt
        triage_prompt = self._build_triage_prompt(
            issue_description=issue_description,
            vision_observations=vision_observations,
            developer_notes=developer_notes,
        )

        # Classify the issue using the model
        classification = await self._call_triage_model(triage_prompt)

        # Log completion
        self._log_action(
            action="triage_complete",
            details=f"Classified as {classification.classification} / {classification.severity}",
        )

        return classification

    def _build_triage_prompt(
        self,
        issue_description: str,
        vision_observations: object = None,
        developer_notes: str = "",
    ) -> str:
        """Build the prompt for the Triage Agent (text lives in prompts.py)."""
        return build_triage_prompt(
            issue_description=issue_description,
            vision_observations=vision_observations,
            developer_notes=developer_notes,
        )
    async def _call_triage_model(self, prompt: str) -> PydanticTriageClassification:
        """Call the reasoning model for triage classification."""

        import json

        # Use Gemini if API key is available, otherwise keyword fallback
        if self.api_key:
            try:
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        max_output_tokens=2000,
                    ),
                )
                response_text = response.text or ""

                # Try to parse the structured response
                try:
                    # Try to extract JSON from the response
                    start = response_text.index("{")
                    end = response_text.rindex("}") + 1
                    json_str = response_text[start:end]
                    parsed = json.loads(json_str)

                    # Map to our Pydantic model
                    classification = parsed.get("classification", "unknown").lower()
                    severity = parsed.get("severity", "medium").lower()

                    # Validate enum values
                    try:
                        classification_enum = IssueClassification(classification)
                    except ValueError:
                        classification_enum = IssueClassification.UNKNOWN

                    try:
                        severity_enum = SeverityLevel(severity)
                    except ValueError:
                        severity_enum = SeverityLevel.MEDIUM

                    return PydanticTriageClassification(
                        issue_id="",  # will be set by the system
                        classification=classification_enum,
                        severity=severity_enum,
                        issue_summary=parsed.get("issue_summary", prompt[:200]),
                        affected_components=parsed.get("affected_components", []) or [],
                        supporting_observations=parsed.get("supporting_observations", []) or [],
                        missing_information=parsed.get("missing_information", []) or [],
                        investigation_objective=parsed.get("investigation_objective", ""),
                        assigned_agent=AgentRole.INVESTIGATION,
                        reason_for_delegation=parsed.get("reason_for_delegation", "Delegate to Investigation Agent for root-cause analysis"),
                    )
                except (ValueError, IndexError, KeyError) as e:
                    print(f"Failed to parse triage JSON: {e}. Falling back to manual parsing.")

                    # Determine classification based on keywords in the response
                    text_lower = response_text.lower()
                    classification = IssueClassification.UNKNOWN
                    severity = SeverityLevel.MEDIUM

                    # Simple keyword-based classification
                    if any(kw in text_lower for kw in ["500", "internal server error", "crash", "unusable", "data breach", "security"]):
                        classification = IssueClassification.BACKEND_ERROR
                        severity = SeverityLevel.CRITICAL
                    elif any(kw in text_lower for kw in ["button not working", "form submission", "ui not responding"]):
                        classification = IssueClassification.UI_BUG
                        severity = SeverityLevel.HIGH
                    elif any(kw in text_lower for kw in ["api", "integration", "request failed"]):
                        classification = IssueClassification.API_INTEGRATION_ERROR
                        severity = SeverityLevel.HIGH
                    elif any(kw in text_lower for kw in ["validation", "invalid input"]):
                        classification = IssueClassification.VALIDATION_ERROR
                        severity = SeverityLevel.MEDIUM
                    else:
                        classification = IssueClassification.UNKNOWN
                        severity = SeverityLevel.MEDIUM

                    return PydanticTriageClassification(
                        issue_id="",
                        classification=classification,
                        severity=severity,
                        issue_summary=response_text[:300] if response_text else "Unable to classify",
                        affected_components=[],
                        supporting_observations=[],
                        missing_information=["Unable to fully classify from model response"],
                        investigation_objective="Investigate the reported issue and identify root cause",
                        assigned_agent=AgentRole.INVESTIGATION,
                        reason_for_delegation="Manual fallback classification due to parsing error",
                    )
            except Exception as e:
                print(f"Gemini API error: {e}. Falling back to keyword fallback.")

        # Keyword-based fallback if no API key or Gemini fails
        text_lower = prompt.lower()
        classification = IssueClassification.UNKNOWN
        severity = SeverityLevel.MEDIUM

        # Simple keyword-based classification
        if any(kw in text_lower for kw in ["500", "internal server error", "crash", "unusable", "data breach", "security"]):
            classification = IssueClassification.BACKEND_ERROR
            severity = SeverityLevel.CRITICAL
        elif any(kw in text_lower for kw in ["button not working", "form submission", "ui not responding"]):
            classification = IssueClassification.UI_BUG
            severity = SeverityLevel.HIGH
        elif any(kw in text_lower for kw in ["api", "integration", "request failed"]):
            classification = IssueClassification.API_INTEGRATION_ERROR
            severity = SeverityLevel.HIGH
        elif any(kw in text_lower for kw in ["validation", "invalid input"]):
            classification = IssueClassification.VALIDATION_ERROR
            severity = SeverityLevel.MEDIUM
        else:
            classification = IssueClassification.UNKNOWN
            severity = SeverityLevel.MEDIUM

        return PydanticTriageClassification(
            issue_id="",
            classification=classification,
            severity=severity,
            issue_summary=(
                prompt.split('- Description: "', 1)[1].split('"', 1)[0][:300]
                if '- Description: "' in prompt
                else "Issue description not supplied"
            ),
            affected_components=[],
            supporting_observations=[],
            missing_information=["No Gemini API key available; using keyword fallback"],
            investigation_objective="Investigate the reported issue and identify root cause",
            assigned_agent=AgentRole.INVESTIGATION,
            reason_for_delegation="Keyword-based classification due to no Gemini API key",
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
        # In a real system, this would be persisted to the database