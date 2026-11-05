"""
PatchPilot Investigation Agent

Primary responsibility: Investigate the technical root cause of reported
bugs and generate evidence-based proposed fixes.

The Investigation Agent receives:
- Triage Agent investigation task
- Vision Agent observations
- Original issue description
- Supplied source-code files or repository context
- Relevant findings from other agents

Responsibilities:
1. Understand the assigned bug
2. Review the available source code
3. Identify potentially relevant files
4. Examine relevant functions, classes, components, and dependencies
5. Trace the likely execution flow
6. Compare screenshot evidence against the supplied code
7. Identify the most probable root cause
8. Explain why the issue occurs
9. Generate a minimal proposed fix
10. Provide code snippets or a unified diff where appropriate
11. Explain the expected effect of the proposed fix
12. Identify potential side effects
13. Suggest relevant tests
14. If a controlled test environment is available, execute permitted tests
    and report actual output

Independent reasoning:
The Investigation Agent must be able to challenge findings from the other agents.

Examples:
- If Vision identifies a broken button but the supplied code suggests the
  button is intentionally disabled, explain the discrepancy.
- If Triage classifies something as a backend bug but source code indicates
  a frontend validation problem, challenge the classification.
- If the screenshot does not provide enough evidence, request additional information.
- If multiple root causes are possible, present them with confidence and
  supporting evidence.

The agent should not automatically agree with other agents.

Important limitations:
- Must not invent files or line numbers
- Must not claim to have read files that were not supplied
- Must not claim tests passed without executing them
- Must not modify production code without explicit authorization
- Must not push changes to GitHub automatically
- Must not treat generated fixes as verified solutions

Expected output:
- Investigation summary
- Suspected root cause
- Relevant source files
- Relevant code locations
- Supporting evidence
- Reasoning
- Proposed fix
- Proposed code changes
- Recommended tests
- Actual test results, if executed
- Confidence level
- Remaining uncertainties
"""

import asyncio
import json
import re
from typing import List, Optional, Dict, Any

from backend.config import GEMINI_MODEL

from agents.investigation.prompts import build_investigation_prompt
from backend.models import (
    ConfidenceLevel,
    AgentRole,
    PydanticInvestigationFindings,
    PydanticAgentActivity,
    IssueClassification,
    SeverityLevel,
)


class InvestigationAgent:
    """Investigation Agent that examines source code and identifies root causes."""

    def __init__(self, client: object, api_key: str):
        self.client = client
        self.api_key = api_key
        self.role = AgentRole.INVESTIGATION
        self.activity_log: List[PydanticAgentActivity] = []
        self.source_code_context: Optional[str] = None
        self.issue_description: Optional[str] = None
        self.vision_observations: Optional[object] = None
        self.triage_classification: Optional[object] = None

    async def investigate(
        self,
        issue_id: str,
        issue_description: str,
        vision_observations: object,
        triage_classification: object,
        source_code: Optional[str] = None,
        repository_context: Optional[str] = None,
    ) -> PydanticInvestigationFindings:
        """
        Investigate a bug report and identify the root cause.

        Args:
            issue_id: Unique identifier for the issue
            issue_description: Developer's description of the issue
            vision_observations: Structured observations from Vision Agent
            triage_classification: Classification from Triage Agent
            source_code: Supplied source-code files (as text)
            repository_context: Optional repository metadata

        Returns:
            PydanticInvestigationFindings with root cause analysis and proposed fix
        """
        # Store context for the investigation
        self.issue_description = issue_description
        self.vision_observations = vision_observations
        self.triage_classification = triage_classification

        # Log the start of investigation
        self._log_action(
            action="starting_investigation",
            details=f"Investigating issue {issue_id}: {issue_description[:80]}...",
        )

        # Build the investigation prompt
        investigation_prompt = self._build_investigation_prompt(
            issue_id=issue_id,
            issue_description=issue_description,
            vision_observations=vision_observations,
            triage_classification=triage_classification,
            source_code=source_code,
            repository_context=repository_context,
        )

        # Run the investigation
        findings = await self._call_investigation_model(investigation_prompt)

        # Log completion
        self._log_action(
            action="investigation_complete",
            details=f"Root cause: {findings.suspected_root_cause[:100] if findings.suspected_root_cause else 'N/A'}",
        )

        return findings

    def _build_investigation_prompt(
        self,
        issue_id: str,
        issue_description: str,
        vision_observations: object,
        triage_classification: object,
        source_code: Optional[str],
        repository_context: Optional[str],
    ) -> str:
        """Build the prompt for the Investigation Agent (text lives in prompts.py)."""
        return build_investigation_prompt(
            issue_id=issue_id,
            issue_description=issue_description,
            vision_observations=vision_observations,
            triage_classification=triage_classification,
            source_code=source_code,
            repository_context=repository_context,
        )
    async def _call_investigation_model(
        self, prompt: str, max_tokens: int = 3000
    ) -> PydanticInvestigationFindings:
        """Call the reasoning model for investigation analysis."""

        # No API key: skip the model call and let the parse fallback return an honest, incomplete report
        if not self.api_key:
            response_text = ""
        else:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=max_tokens,
                ),
            )
            response_text = response.text or ""

        # Try to parse the structured response
        try:
            start = response_text.index("{")
            end = response_text.rindex("}") + 1
            json_str = response_text[start:end]
            parsed = json.loads(json_str)

            # Extract key fields
            root_cause = parsed.get("suspected_root_cause", "")
            proposed_fix = parsed.get("proposed_fix", "")
            proposed_code_changes = parsed.get("proposed_code_changes", "")
            confidence_str = parsed.get("confidence", "medium")

            # Map confidence
            try:
                confidence = ConfidenceLevel(confidence_str.lower())
            except ValueError:
                confidence = ConfidenceLevel.MEDIUM

            # Get remaining uncertainties
            uncertainties = parsed.get("remaining_uncertainties", [])
            if isinstance(uncertainties, str):
                uncertainties = [uncertainties]

            # Get recommended tests
            recommended_tests = parsed.get("recommended_tests", [])
            if isinstance(recommended_tests, str):
                recommended_tests = [recommended_tests]

            # Get relevant source files
            relevant_files = parsed.get("relevant_source_files", [])
            if isinstance(relevant_files, str):
                relevant_files = [relevant_files]

            # Get relevant code locations
            code_locations = parsed.get("relevant_code_locations", [])
            if isinstance(code_locations, str):
                code_locations = [code_locations]

            return PydanticInvestigationFindings(
                issue_id="",  # will be set by the caller
                investigation_summary=parsed.get("investigation_summary", ""),
                suspected_root_cause=root_cause if root_cause else None,
                relevant_source_files=relevant_files or [],
                relevant_code_locations=code_locations or [],
                supporting_evidence=parsed.get("supporting_evidence", []) or [],
                reasoning=parsed.get("reasoning", ""),
                proposed_fix=proposed_fix if proposed_fix else None,
                proposed_code_changes=proposed_code_changes if proposed_code_changes else None,
                recommended_tests=recommended_tests or [],
                actual_test_results=parsed.get("actual_test_results"),
                confidence=confidence,
                remaining_uncertainties=uncertainties or [],
                challenges_previous_findings=parsed.get("challenges_previous_findings"),
            )
        except (ValueError, IndexError, KeyError) as e:
            # Fallback: manual parsing if JSON extraction fails
            print(f"Failed to parse investigation JSON: {e}. Falling back to manual parsing.")

            # Manual extraction of key information from the response text
            text = response_text

            # Simple extraction patterns
            suspected_root_cause = ""
            proposed_fix = ""
            confidence = ConfidenceLevel.MEDIUM

            # Look for root cause mentions
            for line in text.split("\n"):
                lower = line.lower().strip()
                if "root cause" in lower and not suspected_root_cause:
                    suspected_root_cause = line.strip()
                if "proposed fix" in lower and not proposed_fix:
                    proposed_fix = line.strip()

            # If we couldn't find specific lines, use summary text
            if not suspected_root_cause:
                suspected_root_cause = text[:300] if text else "Unable to determine root cause"
            if not proposed_fix:
                proposed_fix = "Investigate and implement appropriate fix based on root cause analysis"

            # Extract code locations if mentioned
            code_locations = []
            location_patterns = re.findall(r"\b\w+\.\w+:\d+", text)
            code_locations = list(set(location_patterns))[:5]

            return PydanticInvestigationFindings(
                issue_id="",
                investigation_summary=text[:500] if text else "Investigation completed",
                suspected_root_cause=suspected_root_cause if suspected_root_cause else None,
                relevant_source_files=[],  # Will be populated if code was supplied
                relevant_code_locations=code_locations,
                supporting_evidence=[],
                reasoning=text[:1000] if text else "",
                proposed_fix=proposed_fix if proposed_fix else None,
                proposed_code_changes=None,
                recommended_tests=[],
                actual_test_results=None,
                confidence=confidence,
                remaining_uncertainties=[
                    "Could not fully parse model response; see raw investigation text for details"
                ],
                challenges_previous_findings=None,
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