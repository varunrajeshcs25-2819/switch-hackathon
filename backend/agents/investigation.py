
"""Investigation Agent: produces an evidence-based root-cause report."""

import re
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
Using the issue description, Vision observations, Triage classification and source code,
find the most likely root cause.

Rules:
- Every item in evidence must point to something actually present in the inputs.
- If no source code is supplied, say so in limitations and keep confidence low.
- Never invent file names, line numbers or code that were not provided.

Return a JSON object with keys:
  investigation_summary, suspected_root_cause, evidence, affected_files,
  suggested_fix, confidence, limitations."""


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

        code = (source_code or "")[:MAX_SOURCE_CHARS]

        # Extract filenames explicitly supplied in source-code comments.
        source_files = re.findall(
            r"(?im)^\s*(?:#|//)\s*file:\s*([^\r\n]+)",
            code,
        )
        source_files = [name.strip() for name in source_files if name.strip()]

        # Honest fallback when Gemini is not configured.
        if not llm.model_configured():

            limitations = ["No model configured."]

            if not has_code:
                limitations.append("No source code supplied.")
                return PydanticInvestigationFindings(
                    issue_id=issue_id,
                    investigation_summary=(
                        "Investigation could not verify the issue because "
                        "no source code or AI model was available."
                    ),
                    suspected_root_cause="",
                    confidence=0.0,
                    source_code_analyzed=False,
                    limitations=limitations,
                )

            limitations.append(
                "Source code was inspected using basic rules, not an AI model."
            )

            # Look for an obvious division-by-zero expression.
            division_match = re.search(
                r"(?m)^\s*(.+?=\s*.+?/\s*0\s*)$",
                code,
            )

            if division_match:
                buggy_line = division_match.group(1).strip()

                root_cause = (
                    "A division-by-zero expression causes an unhandled "
                    "ZeroDivisionError, which can produce an HTTP 500 response."
                )

                proposed_fix = (
                    "Remove the division-by-zero expression or replace it "
                    "with a division operation that validates the denominator "
                    "before performing the calculation."
                )

                proposed_changes = (
                    f"--- original/{source_files[0] if source_files else 'source.py'}\n"
                    f"+++ proposed/{source_files[0] if source_files else 'source.py'}\n"
                    "@@ -1 +1 @@\n"
                    f"-{buggy_line}\n"
                    f"+{buggy_line.split('=')[0].rstrip()} = 0  "
                    "# TODO: replace with a calculation using a validated, non-zero denominator\n"
)

                evidence = [
                    f"The supplied source code contains: {buggy_line}"
                ]

                summary = (
                    "A possible division-by-zero cause was identified "
                    "through basic source-code inspection."
                )

            else:
                root_cause = (
                    "The supplied source code could not be matched to "
                    "a known error pattern by the basic inspection rules."
                )

                proposed_fix = (
                    "Review the supplied source code and reproduce the "
                    "reported error to identify the failing operation."
                )

                proposed_changes = (
                    "No automatic code change was generated. "
                    "Further investigation is required."
                )

                evidence = [
                    "Source code was supplied, but no supported error pattern was detected."
                ]

                summary = (
                    "Source code was supplied, but the basic inspection "
                    "rules could not identify a definite root cause."
                )

            return PydanticInvestigationFindings(
                issue_id=issue_id,
                investigation_summary=summary,
                suspected_root_cause=root_cause,
                relevant_source_files=source_files,
                affected_files=source_files,
                relevant_code_locations=evidence,
                supporting_evidence=evidence,
                evidence=evidence,
                reasoning=(
                    "This is a rule-based finding, not an AI-generated "
                    "or independently verified diagnosis."
                ),
                proposed_fix=proposed_fix,
                proposed_code_changes=proposed_changes,
                confidence=0.2,
                source_code_analyzed=True,
                analyzed_by_model=False,
                limitations=limitations,
            )

        # Normal Gemini-powered investigation.
        truncated = len(source_code) > MAX_SOURCE_CHARS

        prompt = (
            f"Issue description: {issue_description or '(none)'}\n"
            f"Vision observations: "
            f"{vision_observations.model_dump_json() if vision_observations else '(none)'}\n"
            f"Triage: "
            f"{triage_classification.model_dump_json() if triage_classification else '(none)'}\n"
            f"Repository context: {repository_context or '(none)'}\n"
            f"Source code:\n{code if has_code else '(none supplied)'}"
        )

        data = await llm.generate_json(SYSTEM_PROMPT, prompt)

        limitations = as_str_list(data.get("limitations"))

        if not has_code and not any(
            "source" in item.lower() for item in limitations
        ):
            limitations.append(
                "No source code supplied; findings are inferred from the screenshot and description only."
            )

        if truncated:
            limitations.append(
                f"Source code was truncated to {MAX_SOURCE_CHARS} characters."
            )

        confidence = as_float(data.get("confidence"))

        if not has_code:
            confidence = min(confidence, 0.4)

        affected_files = as_str_list(data.get("affected_files"))

        for filename in source_files:
            if filename not in affected_files:
                affected_files.append(filename)

        return PydanticInvestigationFindings(
            issue_id=issue_id,
            investigation_summary=as_str(
                data.get("investigation_summary")
            ),
            suspected_root_cause=as_str(
                data.get("suspected_root_cause")
            ),
            relevant_source_files=affected_files,
            affected_files=affected_files,
            evidence=as_str_list(data.get("evidence")),
            suggested_fix=as_str(data.get("suggested_fix")),
            confidence=confidence,
            source_code_analyzed=has_code,
            limitations=limitations,
            analyzed_by_model=True,
        )
