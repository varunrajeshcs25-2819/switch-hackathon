"""
Comprehensive Unit & Edge Case Tests for Vision Agent.

Scenarios tested:
1. Clear visible error screenshot JSON response parsing.
2. Multiple UI defects on a single screen.
3. Clean screen / no visible bugs (correct uncertainty / confidence handling).
4. Fallback parser when model returns free-form text instead of JSON.
5. Incomplete, malformed, or empty input handling.
6. Honest fallback behavior when no API key is provided.
7. Retry logic and error handling on model API failure.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from agents.vision.agent import VisionAgent
from agents.vision.prompts import build_vision_prompt
from backend.models import ConfidenceLevel, PydanticVisionObservations


@pytest.fixture
def vision_agent_no_key():
    return VisionAgent(api_key="")


@pytest.fixture
def vision_agent_with_key():
    return VisionAgent(api_key="mock-key-for-testing")


def test_build_vision_prompt_formatting():
    """Verify prompt correctly integrates user description and app context."""
    prompt = build_vision_prompt(
        user_description="Login button is not responding and page is blank",
        application_context="React 18 customer portal",
    )
    assert "Login button is not responding" in prompt
    assert "React 18 customer portal" in prompt
    assert "REQUIRED OUTPUT FORMAT" in prompt
    assert "```json" in prompt


@pytest.mark.asyncio
async def test_empty_screenshot_input(vision_agent_no_key):
    """Empty or whitespace screenshot input must return honest uncertainty without crashing."""
    res = await vision_agent_no_key.analyze_screenshot("")
    assert res.confidence == ConfidenceLevel.UNCERTAIN
    assert "No screenshot" in res.error_messages[0]
    assert len(res.uncertainties) > 0


@pytest.mark.asyncio
async def test_no_api_key_honest_fallback(vision_agent_no_key):
    """When no API key is set, the agent must never hallucinate findings."""
    res = await vision_agent_no_key.analyze_screenshot("fakebase64string==")
    assert res.confidence in [ConfidenceLevel.UNCERTAIN, ConfidenceLevel.LOW]
    assert len(res.uncertainties) > 0


def test_parse_structured_json_with_multiple_issues(vision_agent_with_key):
    """Verify parsing when model returns structured JSON with multiple issues."""
    model_response = """```json
    {
      "summary": "Registration form displays an HTTP 500 internal server error with misaligned fields.",
      "issues": [
        {
          "id": "obs-1",
          "description": "500 Internal Server Error banner displayed upon form submission",
          "affected_component": "Registration Form Banner",
          "approximate_location": "Top center of form card",
          "visual_evidence": "HTTP 500: Internal Server Error",
          "defect_type": "visible_error",
          "confidence": "high",
          "uncertainty": "Underlying server trace is not visible on screen"
        },
        {
          "id": "obs-2",
          "description": "Password confirmation input field overflows container boundary",
          "affected_component": "Password Confirmation Input",
          "approximate_location": "Middle right of form",
          "visual_evidence": "Input border overlaps with right card margin by ~15px",
          "defect_type": "layout_anomaly",
          "confidence": "high",
          "uncertainty": "Could be responsive viewport glitch"
        }
      ],
      "error_messages": [
        "HTTP 500: Internal Server Error"
      ],
      "affected_components": [
        "Registration Form Banner",
        "Password Confirmation Input"
      ],
      "approximate_location": "Top center and middle right of form",
      "evidence": [
        "HTTP 500: Internal Server Error",
        "Input border overlaps right card margin"
      ],
      "possible_behavioral_implications": [
        "User registration is completely blocked",
        "Form submission endpoint is failing"
      ],
      "confidence": "high",
      "uncertainties": [
        "Underlying server stack trace not visible"
      ]
    }
    ```"""

    obs = vision_agent_with_key._parse_vision_response(model_response)
    assert isinstance(obs, PydanticVisionObservations)
    assert obs.confidence == ConfidenceLevel.HIGH
    assert len(obs.error_messages) == 1
    assert "HTTP 500: Internal Server Error" in obs.error_messages[0]
    assert "Registration Form Banner" in obs.affected_components
    assert "Password Confirmation Input" in obs.affected_components
    assert obs.approximate_location == "Top center and middle right of form"
    assert len(obs.evidence) == 2
    assert len(obs.possible_behavioral_implications) == 2


def test_parse_clean_screenshot_no_visible_defects(vision_agent_with_key):
    """Verify behavior when screenshot has no visible errors or defects."""
    model_response = """```json
    {
      "summary": "Dashboard UI rendered with standard layout and no visible error messages or broken elements.",
      "issues": [],
      "error_messages": [],
      "affected_components": [],
      "approximate_location": "Full screen",
      "evidence": [
        "All navigation links and status cards render without visual glitches",
        "No alert badges, toasts, or error text visible"
      ],
      "possible_behavioral_implications": [],
      "confidence": "low",
      "uncertainties": [
        "Static screenshot cannot reveal silent click or state handler bugs"
      ]
    }
    ```"""

    obs = vision_agent_with_key._parse_vision_response(model_response)
    assert obs.confidence == ConfidenceLevel.LOW
    assert len(obs.error_messages) == 0
    assert len(obs.affected_components) == 0
    assert len(obs.uncertainties) > 0


def test_parse_fallback_freeform_text(vision_agent_with_key):
    """Verify fallback parser handles unstructured text gracefully."""
    raw_text = """
    Observation Summary: The profile settings page displays an uncaught error.

    Detected Errors:
    - Error: Failed to fetch user profile data (404 Not Found)

    Affected Components:
    - UserProfileCard
    - AvatarImagePlaceholder

    Approximate Location:
    - Center content area

    Evidence:
    - Screenshot displays red notification box reading 'Failed to fetch user profile data'

    Uncertainties:
    - Cannot see network tab to verify if request was sent or timed out
    """

    obs = vision_agent_with_key._parse_vision_response(raw_text)
    assert isinstance(obs, PydanticVisionObservations)
    assert len(obs.error_messages) > 0
    assert any("404" in e or "Failed to fetch" in e for e in obs.error_messages)
    assert len(obs.affected_components) >= 2
    assert obs.approximate_location is not None


@pytest.mark.asyncio
async def test_retry_on_transient_failure():
    """Verify retry logic handles transient errors and succeeds on retry."""
    agent = VisionAgent(api_key="valid-test-key", max_retries=2)

    # Mock the internal _call_vision_model to fail once then succeed
    mock_obs = PydanticVisionObservations(
        error_messages=["Fatal Error"],
        affected_components=["Header"],
        confidence=ConfidenceLevel.HIGH,
    )

    with patch.object(
        agent,
        "_call_vision_model",
        side_effect=[Exception("503 Service Unavailable"), mock_obs],
    ) as mock_call:
        res = await agent.analyze_screenshot("validbase64==")
        assert mock_call.call_count == 2
        assert res.confidence == ConfidenceLevel.HIGH
        assert "Fatal Error" in res.error_messages[0]
