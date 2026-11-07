
"""Triage Agent: classifies the issue, rates severity and sets the investigation objective."""

import re
from typing import Optional

from backend.agents.common import as_float, as_str, coerce_enum
from backend.models import (
    IssueClassification,
    PydanticTriageClassification,
    PydanticVisionObservations,
    SeverityLevel,
)
from backend.services import llm

SYSTEM_PROMPT = """You are the Triage Agent in a software debugging team.
Given a bug description and (optionally) the Vision Agent's observations, classify the issue.
Return a JSON object with keys:
  classification: one of ui_bug, functional_bug, performance, data_issue, configuration, security, unknown
  severity: one of low, medium, high, critical
  reasoning (string), suspected_area (string: component/module/layer, or "" if unknown),
  investigation_objective (string: one concrete question the Investigation Agent should answer),
  confidence (number 0-1).
Do not invent facts that are not in the input."""

_KEYWORDS = [
    (IssueClassification.SECURITY, SeverityLevel.CRITICAL,
     ("xss", "sql injection", "csrf", "api key exposed", "password exposed", "token exposed")),
    (IssueClassification.DATA_ISSUE, SeverityLevel.HIGH,
     ("data loss", "wrong data", "missing data", "duplicate", "corrupt")),
    (IssueClassification.FUNCTIONAL_BUG, SeverityLevel.HIGH,
     ("crash", "exception", "traceback", "fails", "404", "error")),
    (IssueClassification.PERFORMANCE, SeverityLevel.MEDIUM,
     ("slow", "lag", "timeout", "freeze", "memory leak", "performance")),
    (IssueClassification.UI_BUG, SeverityLevel.LOW,
     ("overlap", "misalign", "layout", "css", "style", "cut off", "responsive", "button")),
    (IssueClassification.CONFIGURATION, SeverityLevel.MEDIUM,
     ("config", "environment variable", ".env", "settings")),
]


class TriageAgent:
    async def triage_issue(
        self,
        issue_description: str,
        vision_observations: Optional[PydanticVisionObservations] = None,
        developer_notes: str = "",
    ) -> PydanticTriageClassification:

        if not llm.model_configured():
            return self._heuristic(
                issue_description,
                vision_observations,
                developer_notes,
            )

        vision_json = (
            vision_observations.model_dump_json()
            if vision_observations else "(none)"
        )

        prompt = (
            f"Issue description: {issue_description or '(none)'}\n"
            f"Developer notes: {developer_notes or '(none)'}\n"
            f"Vision observations: {vision_json}"
        )

        data = await llm.generate_json(SYSTEM_PROMPT, prompt)

        return PydanticTriageClassification(
            classification=coerce_enum(
                IssueClassification,
                data.get("classification"),
                IssueClassification.UNKNOWN,
            ),
            severity=coerce_enum(
                SeverityLevel,
                data.get("severity"),
                SeverityLevel.MEDIUM,
            ),
            reasoning=as_str(data.get("reasoning")),
            suspected_area=as_str(data.get("suspected_area")),
            investigation_objective=(
                as_str(data.get("investigation_objective"))
                or "Identify the most likely root cause of the reported issue."
            ),
            confidence=as_float(data.get("confidence")),
            analyzed_by_model=True,
        )

    @staticmethod
    def _heuristic(description, vision, notes):
        description_text = " ".join([
            description or "",
            notes or "",
        ]).lower()

        # Only classify as a backend error when the description explicitly
        # identifies a backend-related component or service.
        has_backend_context = bool(
            re.search(
                r"\b(api|backend|server|endpoint|database)\b",
                description_text,
            )
        )

        if "500" in description_text and has_backend_context:
            return PydanticTriageClassification(
                classification=IssueClassification.BACKEND_ERROR,
                severity=SeverityLevel.HIGH,
                reasoning="A backend-related HTTP 500 error was detected by the keyword heuristic.",
                investigation_objective="Identify the backend cause of the HTTP 500 error.",
                confidence=0.2,
                analyzed_by_model=False,
            )

        text = " ".join([
            description_text,
            vision.summary if vision else "",
            " ".join(vision.visible_error_messages) if vision else "",
        ]).lower()

        for classification, severity, words in _KEYWORDS:
            hit = next((word for word in words if word in text), None)

            if hit:
                return PydanticTriageClassification(
                    classification=classification,
                    severity=severity,
                    reasoning=(
                        f"Keyword heuristic matched '{hit}'. "
                        "No model configured, so this is a rough guess."
                    ),
                    investigation_objective=(
                        "Identify the most likely root cause of the reported issue."
                    ),
                    confidence=0.2,
                    analyzed_by_model=False,
                )

        return PydanticTriageClassification(
            classification=IssueClassification.UNKNOWN,
            severity=SeverityLevel.MEDIUM,
            reasoning="No model configured and no keywords matched.",
            investigation_objective=(
                "Identify the most likely root cause of the reported issue."
            ),
            confidence=0.0,
            analyzed_by_model=False,
        )
