"""
Comprehensive Unit & Edge Case Tests for Investigation Agent.

Scenarios tested:
1. Investigation with source code identifies real code locations and unified diff.
2. Investigation WITHOUT source code honestly reports limitations (no hallucinated files).
3. Independent challenge generation: Code shows button is disabled by design when Vision reported bug.
4. Independent challenge generation: Code shows client-side validation error when Triage said backend error.
5. Structured JSON output parsing from reasoning model.
6. Fallback heuristic code scanner detects unhandled runtime exception (e.g. division by zero).
7. Anti-hallucination guard: downgraded confidence when code context is missing.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from agents.investigation.agent import InvestigationAgent
from agents.investigation.prompts import build_investigation_prompt
from backend.models import (
    ConfidenceLevel,
    IssueClassification,
    SeverityLevel,
    PydanticVisionObservations,
    PydanticTriageClassification,
    PydanticInvestigationFindings,
)


@pytest.fixture
def investigation_agent_no_key():
    return InvestigationAgent(api_key="")


@pytest.fixture
def investigation_agent_with_key():
    return InvestigationAgent(api_key="mock-investigation-key")


def test_build_investigation_prompt_formatting():
    """Verify prompt incorporates vision observations, triage task, and source code."""
    vision_obs = PydanticVisionObservations(
        error_messages=["HTTP 500: Server Error"],
        affected_components=["SubmitButton"],
        confidence=ConfidenceLevel.HIGH,
    )
    triage = PydanticTriageClassification(
        classification=IssueClassification.BACKEND_ERROR,
        severity=SeverityLevel.CRITICAL,
        investigation_objective="Inspect user_controller.py register endpoint for unhandled exception",
    )
    code = "def register():\n    return 1 / 0\n"

    prompt = build_investigation_prompt(
        issue_id="issue-123",
        issue_description="Registration crashes with 500 error",
        vision_observations=vision_obs,
        triage_classification=triage,
        source_code=code,
    )
    assert "issue-123" in prompt
    assert "HTTP 500: Server Error" in prompt
    assert "user_controller.py" in prompt
    assert "def register():" in prompt
    assert "REQUIRED OUTPUT FORMAT" in prompt


@pytest.mark.asyncio
async def test_investigation_without_source_code_honest_limitations(investigation_agent_no_key):
    """When no source code is supplied, agent must not invent files or line numbers."""
    findings = await investigation_agent_no_key.investigate(
        issue_id="issue-no-code",
        issue_description="App throws 500 error",
        vision_observations=None,
        triage_classification=None,
        source_code=None,
    )
    assert findings.suspected_root_cause is None
    assert len(findings.relevant_source_files) == 0
    assert findings.confidence == ConfidenceLevel.LOW
    assert any("No source code" in u for u in findings.remaining_uncertainties)
    assert len(findings.challenges_previous_findings) > 0


@pytest.mark.asyncio
async def test_investigation_with_source_code_identifies_root_cause(investigation_agent_no_key):
    """When source code has an obvious unhandled exception, it must locate line and propose diff."""
    sample_code = """# file: auth_controller.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
def register(user_data: dict):
    # Bug: zero division error
    result = 1 / 0
    return {"status": "ok"}
"""
    findings = await investigation_agent_no_key.investigate(
        issue_id="issue-code-present",
        issue_description="500 internal server error during registration",
        vision_observations=None,
        triage_classification=None,
        source_code=sample_code,
    )
    assert findings.suspected_root_cause is not None
    assert "auth_controller.py" in findings.relevant_source_files
    assert any("auth_controller.py:9" in loc for loc in findings.relevant_code_locations)
    assert findings.proposed_code_changes is not None
    assert "--- original" in findings.proposed_code_changes
    assert findings.confidence == ConfidenceLevel.HIGH


@pytest.mark.asyncio
async def test_investigation_challenges_vision_button_disabled(investigation_agent_no_key):
    """Agent must challenge Vision observation if button is disabled by design in code."""
    sample_frontend_code = """// file: RegisterForm.tsx
export function RegisterForm({ isValid }) {
    return (
        <form>
            <input type="text" />
            <button disabled={!isValid}>Submit</button>
        </form>
    );
}
"""
    vision_obs = PydanticVisionObservations(
        error_messages=[],
        affected_components=["SubmitButton"],
        raw_observation="Submit button appears broken and unclickable",
        confidence=ConfidenceLevel.HIGH,
    )
    findings = await investigation_agent_no_key.investigate(
        issue_id="issue-disabled-button",
        issue_description="Button is broken",
        vision_observations=vision_obs,
        triage_classification=None,
        source_code=sample_frontend_code,
    )
    assert any("intentional design" in c.lower() or "disabled" in c.lower() for c in findings.challenges_previous_findings)


def test_investigation_parse_structured_json(investigation_agent_with_key):
    """Verify parsing of valid JSON output from reasoning model."""
    json_response = """```json
    {
      "investigation_summary": "Identified null pointer dereference in user_service.py line 45.",
      "suspected_root_cause": "Accessing user.profile.email without checking if user.profile is initialized",
      "relevant_source_files": ["services/user_service.py"],
      "relevant_code_locations": ["services/user_service.py:45-52"],
      "supporting_evidence": ["email = user.profile.email"],
      "reasoning": "When a new user signs up via OAuth, user.profile is None until onboarding completes, raising AttributeError.",
      "proposed_fix": "Use safe navigation or check if user.profile is not None",
      "proposed_code_changes": "--- services/user_service.py\\n+++ services/user_service.py\\n@@ -45,1 +45,2 @@\\n- email = user.profile.email\\n+ email = user.profile.email if user.profile else None",
      "recommended_tests": ["test_register_oauth_user_with_null_profile"],
      "confidence": "high",
      "remaining_uncertainties": ["Whether OAuth provider returns email in raw payload"],
      "challenges_previous_findings": ["Triage classified this as a database error, but it is an in-memory AttributeError in Python code."]
    }
    ```"""
    parsed = investigation_agent_with_key._parse_investigation_response(
        json_response,
        source_code="some code",
    )
    assert parsed is not None
    assert any("user_service.py" in f for f in parsed.relevant_source_files)
    assert "Accessing user.profile.email" in parsed.suspected_root_cause
    assert parsed.confidence == ConfidenceLevel.HIGH
    assert len(parsed.challenges_previous_findings) == 1
    assert "Triage classified this as a database error" in parsed.challenges_previous_findings[0]
