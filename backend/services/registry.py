"""Single place that hands out agent instances (swap implementations here for tests)."""

from functools import lru_cache

from backend.agents.investigation import InvestigationAgent
from backend.agents.triage import TriageAgent
from backend.agents.vision import VisionAgent
from backend.services.llm import model_configured  # re-exported for main.py

__all__ = ["get_vision_agent", "get_triage_agent", "get_investigation_agent", "model_configured"]


@lru_cache(maxsize=1)
def get_vision_agent() -> VisionAgent:
    return VisionAgent()


@lru_cache(maxsize=1)
def get_triage_agent() -> TriageAgent:
    return TriageAgent()


@lru_cache(maxsize=1)
def get_investigation_agent() -> InvestigationAgent:
    return InvestigationAgent()
