"""Investigation Agent: produces an evidence-based root-cause report."""

from typing import Optional

from backend.agents.common import as_float, as_str, as_str_list
from backend.config import MAX_SOURCE_CHARS
from backend.models import (
    PydanticInvestigationFindings,
    PydanticTriageClassification,
    PydanticVisionObservations,
)
from backend.services import llm

SYSTEM_PROMPT = """You are the Investigation Agent in a software debugging team.
Using the issue description, Vision observations, Triage classification and (if supplied)
source code, find the most likely root cause.
Rules:
- Every item in "evidence" must point to something actually present in the inputs
  (a visible error message, a specific line/function in the supplied code, etc.).
- If no source code is supplied, say so in "limitations" and keep confidence low.
- Never invent file names, line numbers or code that were not provided.
Return a JSON object with keys:
  investigation_summary (string), suspected_root_cause (string), evidence (list of strings),
  affected_files (list of strings, only if visible in the input), suggested_fix (string),
  confidence (number 0-1), limitations (list of strings)."""


class InvestigationAgent:
    async def investigate(
        self,
        issue_id: str,
        issue_description: str,
        vision_observations: Optional[PydanticVisionObservations] = None,
        triage_classification: Optional[PydanticTriageClassification] = None,
        source_code: Optional[str] = None,
        repository_context: Optional[str] = None,
    ) -> PydanticInvestigationFindings:
        has_code = bool(source_code and source_code.strip())

        if not llm.model_configured():
            return PydanticInvestigationFindings(
                issue_id=issue_id,
                investigation_summary="Investigation not run: no model is configured (set GEMINI_API_KEY).",
                suspected_root_cause="",
                confidence=0.0,
                source_code_analyzed=False,
                limitations=["No model configured.", "Source code was supplied but not analyzed." if has_code else "No source code supplied."],
            )

        code = (source_code or "")[:MAX_SOURCE_CHARS]
        truncated = has_code and len(source_code) > MAX_SOURCE_CHARS
        prompt = (
            f"Issue description: {issue_description or '(none)'}\n"
            f"Vision observations: {vision_observations.model_dump_json() if vision_observations else '(none)'}\n"
            f"Triage: {triage_classification.model_dump_json() if triage_classification else '(none)'}\n"
            f"Repository context: {repository_context or '(none)'}\n"
            f"Source code:\n{code if has_code else '(none supplied)'}"
        )
        data = await llm.generate_json(SYSTEM_PROMPT, prompt)

        limitations = as_str_list(data.get("limitations"))
        if not has_code and not any("source" in l.lower() for l in limitations):
            limitations.append("No source code supplied; findings are inferred from the screenshot and description only.")
        if truncated:
            limitations.append(f"Source code was truncated to {MAX_SOURCE_CHARS} characters.")

        confidence = as_float(data.get("confidence"))
        if not has_code:
            confidence = min(confidence, 0.4)

        return PydanticInvestigationFindings(
            issue_id=issue_id,
            investigation_summary=as_str(data.get("investigation_summary")),
            suspected_root_cause=as_str(data.get("suspected_root_cause")),
            evidence=as_str_list(data.get("evidence")),
            affected_files=as_str_list(data.get("affected_files")),
            suggested_fix=as_str(data.get("suggested_fix")),
            confidence=confidence,
            source_code_analyzed=has_code,
            limitations=limitations,
            analyzed_by_model=True,
        )
