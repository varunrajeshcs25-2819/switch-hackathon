"""Single place where the three agents are constructed.

Keeping this out of the API module avoids circular imports and lets the
workflow service, REST endpoints and tests share one agent configuration.
"""

from __future__ import annotations

from typing import Optional

from backend.config import ANTHROPIC_API_KEY, GEMINI_API_KEY
from agents.investigation.agent import InvestigationAgent
from agents.triage.agent import TriageAgent
from agents.vision.agent import VisionAgent

# Gemini is the primary provider; the Anthropic key is accepted as a legacy
# fallback only for wrappers that still pass it through.
API_KEY = GEMINI_API_KEY or ANTHROPIC_API_KEY or ""

_vision_agent: Optional[VisionAgent] = None
_triage_agent: Optional[TriageAgent] = None
_investigation_agent: Optional[InvestigationAgent] = None


def get_vision_agent() -> VisionAgent:
    global _vision_agent
    if _vision_agent is None:
        _vision_agent = VisionAgent(client=None, api_key=API_KEY)
    return _vision_agent


def get_triage_agent() -> TriageAgent:
    global _triage_agent
    if _triage_agent is None:
        _triage_agent = TriageAgent(api_key=API_KEY)
    return _triage_agent


def get_investigation_agent() -> InvestigationAgent:
    global _investigation_agent
    if _investigation_agent is None:
        _investigation_agent = InvestigationAgent(client=None, api_key=API_KEY)
    return _investigation_agent


def reset_agents() -> None:
    """Drop cached agents (used by tests to pick up config changes)."""
    global _vision_agent, _triage_agent, _investigation_agent
    _vision_agent = _triage_agent = _investigation_agent = None


def model_configured() -> bool:
    return bool(API_KEY)
