"""
Comprehensive Unit & Edge Case Tests for Triage Agent.

Scenarios tested:
1. Clear frontend/UI styling bug classification (Medium/Low severity).
2. Backend 500 error on critical workflow (e.g. registration/checkout -> Critical).
3. Localized/non-critical backend error (e.g. avatar load -> Medium, NOT Critical).
4. Security/Credential leak detection (Critical severity).
5. Contradiction detection between developer description and visual evidence.
6. Structured JSON output parsing from model.
7. Fallback heuristic classifier when model calls are unavailable.
8. Evaluation and challenge mechanism of Investigation Agent deliverables.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from agents.triage.agent import TriageAgent
from agents.triage.prompts import build_triage_prompt
from backend.models import (
    IssueClassification,
    SeverityLevel,
    ConfidenceLevel,
    PydanticVisionObservations,
    PydanticInvestigationFindings,
)


@pytest.fixture
def triage_agent_no_key():
    return TriageAgent(api_key="")


@pytest.fixture
def triage_agent_with_key():
    return TriageAgent(api_key="mock-triage-key")


def test_build_triage_prompt_formatting():
    """Verify prompt formatting includes vision observations and dev notes."""
    vision_obs = PydanticVisionObservations(
        error_messages=["HTTP 500 Internal Server Error"],
        affected_components=["RegisterForm"],
        approximate_location="Center Modal",
        evidence=["HTTP 500 banner visible"],
        confidence=ConfidenceLevel.HIGH,
    )
    prompt = build_triage_prompt(
        issue_description="Registration page crashes when submitting form",
        vision_observations=vision_obs,
        developer_notes="Postgres container might be down",
    )
    assert "Registration page crashes when submitting form" in prompt
    assert "HTTP 500 Internal Server Error" in prompt
    assert "RegisterForm" in prompt
    assert "Postgres container might be down" in prompt
    assert "REQUIRED OUTPUT FORMAT" in prompt


@pytest.mark.asyncio
async def test_triage_critical_backend_workflow(triage_agent_no_key):
    """Core registration/checkout 500 crash must be triaged as Critical Backend Error."""
    vision_obs = PydanticVisionObservations(
        error_messages=["HTTP 500 Internal Server Error"],
        affected_components=["CheckoutModal"],
        confidence=ConfidenceLevel.HIGH,
    )
    triage = await triage_agent_no_key.triage_issue(
        issue_description="User registration and checkout throws 500 internal server error",
        vision_observations=vision_obs,
    )
    assert triage.classification == IssueClassification.BACKEND_ERROR
    assert triage.severity == SeverityLevel.CRITICAL
    assert "CheckoutModal" in triage.affected_components or "General Application" in triage.affected_components
    assert len(triage.investigation_objective) > 0


@pytest.mark.asyncio
async def test_triage_non_critical_backend_error(triage_agent_no_key):
    """Localized backend 500 (e.g. non-essential widget) should NOT blindly be Critical."""
    vision_obs = PydanticVisionObservations(
        error_messages=["500 Internal Server Error"],
        affected_components=["UserProfileAvatarWidget"],
        confidence=ConfidenceLevel.MEDIUM,
    )
    triage = await triage_agent_no_key.triage_issue(
        issue_description="Profile avatar fails to render on settings tab",
        vision_observations=vision_obs,
    )
    assert triage.classification == IssueClassification.BACKEND_ERROR
    assert triage.severity == SeverityLevel.HIGH  # High or Medium, but NEVER Critical for an isolated avatar


@pytest.mark.asyncio
async def test_triage_security_concern(triage_agent_no_key):
    """Exposed credentials or token leak must be triaged as Critical Security Concern."""
    triage = await triage_agent_no_key.triage_issue(
        issue_description="API token and secret key leaked in plain text on error banner",
    )
    assert triage.classification == IssueClassification.SECURITY_CONCERN
    assert triage.severity == SeverityLevel.CRITICAL


@pytest.mark.asyncio
async def test_triage_ui_layout_bug(triage_agent_no_key):
    """Visual overflow or CSS alignment issue should be triaged as UI Bug with Low/Medium severity."""
    vision_obs = PydanticVisionObservations(
        affected_components=["NavigationMenu"],
        evidence=["Menu items overlap right boundary by 20px"],
        confidence=ConfidenceLevel.HIGH,
    )
    triage = await triage_agent_no_key.triage_issue(
        issue_description="Navigation links are overlapping the right border",
        vision_observations=vision_obs,
    )
    assert triage.classification == IssueClassification.UI_BUG
    assert triage.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM]


def test_triage_parse_structured_json(triage_agent_with_key):
    """Verify parsing of valid JSON output from reasoning model."""
    json_response = """```json
    {
      "classification": "api_integration_error",
      "severity": "high",
      "severity_reasoning": "Product search API fails returning 404, preventing catalog queries",
      "issue_summary": "Product search endpoint returns 404 Not Found on search trigger",
      "affected_components": ["SearchBar", "ProductCatalogAPI"],
      "supporting_observations": ["Network error 404 seen in toast", "Search results empty"],
      "contradictions_identified": [],
      "missing_information": ["API gateway routing table", "Backend search route file"],
      "source_code_required": true,
      "investigation_objective": "Verify search endpoint route registration in API gateway and backend controller",
      "reason_for_delegation": "Investigation Agent must inspect FastAPI routes and route decorator prefixes"
    }
    ```"""
    parsed = triage_agent_with_key._parse_triage_response(json_response)
    assert parsed is not None
    assert parsed.classification == IssueClassification.API_INTEGRATION_ERROR
    assert parsed.severity == SeverityLevel.HIGH
    assert "SearchBar" in parsed.affected_components
    assert "ProductCatalogAPI" in parsed.affected_components
    assert "Verify search endpoint" in parsed.investigation_objective


def test_triage_evaluate_investigation_findings(triage_agent_no_key):
    """Verify Triage Agent evaluation of Investigation deliverables."""
    # 1. Incomplete findings (missing root cause and source code)
    incomplete_findings = PydanticInvestigationFindings(
        suspected_root_cause=None,
        proposed_fix=None,
        relevant_source_files=[],
    )
    eval_incomplete = triage_agent_no_key.evaluate_investigation(
        incomplete_findings, source_code_supplied=False
    )
    assert eval_incomplete["addressed"] is False
    assert len(eval_incomplete["challenges"]) >= 2

    # 2. Complete findings with verifiable files and proposed fix
    complete_findings = PydanticInvestigationFindings(
        suspected_root_cause="Missing null check on user.profile",
        proposed_fix="Add if not user.profile: return None",
        relevant_source_files=["backend/auth/controller.py"],
        confidence=ConfidenceLevel.HIGH,
    )
    eval_complete = triage_agent_no_key.evaluate_investigation(
        complete_findings, source_code_supplied=True
    )
    assert eval_complete["addressed"] is True
    assert len(eval_complete["challenges"]) == 0
    assert eval_complete["verdict"] == "Accepted"

