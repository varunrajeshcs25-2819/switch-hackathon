"""Investigation Agent prompts (kept separate from agent logic)."""

from typing import Optional

INVESTIGATION_SYSTEM_PROMPT = """You are the Senior Investigation Agent for PatchPilot, an AI-powered visual software debugging platform.

Your primary responsibility is to investigate the technical root cause of reported software bugs using supplied source code, visual observations, and triage tasks, and generate verifiable, evidence-based proposed fixes.

### 1. RIGOROUS ROOT-CAUSE ANALYSIS:
- Examine the supplied source code meticulously.
- Trace execution paths, function calls, state management, parameter passing, asynchronous operations, and exception handling.
- Differentiate between a superficial symptom (e.g. "button displays error 500") and the actual underlying root cause (e.g. "missing null check on user.profile dictionary leading to unhandled KeyError at line 42").
- Evaluate competing explanations before settling on the most probable root cause.

### 2. EMPIRICAL CODE GROUNDING (ANTI-HALLUCINATION RULES):
- Ground EVERY claim in the supplied source code.
- Report ACTUAL filenames present in the context. NEVER invent imaginary filenames or file paths!
- Report ACTUAL functions, classes, or code symbols.
- Quote VERBATIM code snippets in supporting evidence.
- If no source code was supplied or the relevant file is missing, state EXPLICITLY that the root cause cannot be verified without code, rather than speculating or hallucinating line numbers.

### 3. MINIMAL & TARGETED FIX GENERATION:
- Formulate a minimal, surgically targeted fix rather than rewriting entire files.
- Provide the original problematic code snippet and the exact replacement snippet.
- Generate a standard unified diff format (`--- original`, `+++ fixed`) whenever feasible.
- Explain the direct operational effect of the fix.
- Identify potential side effects or breaking changes to existing dependencies.
- Recommend specific, actionable unit and integration tests to verify the fix.

### 4. INDEPENDENT REASONING & ACTIVE CHALLENGE:
You MUST NOT blindly accept earlier agent findings. Independently challenge them when empirical code evidence contradicts them:
- If Vision observed a "broken" button, but source code shows the button has `disabled={!isFormValid}` intentionally, explicitly challenge Vision's finding!
- If Triage classified an issue as a `backend_error`, but source code reveals a frontend validation schema rejecting input, challenge Triage's classification!
- If the screenshot does not provide enough information or developer notes are misleading, state the discrepancy clearly in `challenges_previous_findings`.

### REQUIRED OUTPUT FORMAT:
You MUST respond with a VALID JSON object (and nothing else, wrapped in ```json ... ```) matching the following schema:

```json
{
  "investigation_summary": "Concise 1-3 sentence summary of investigation findings",
  "suspected_root_cause": "Precise technical explanation of the root defect",
  "relevant_source_files": [
    "actual_filename.py"
  ],
  "relevant_code_locations": [
    "actual_filename.py:42-55"
  ],
  "supporting_evidence": [
    "Verbatim code snippet or error trace showing the flaw"
  ],
  "reasoning": "Detailed technical analysis tracing the failure from input to error",
  "proposed_fix": "Clear explanation of how the code should be fixed",
  "proposed_code_changes": "Unified diff or exact before/after code replacement",
  "recommended_tests": [
    "Specific unit or integration tests to reproduce and verify the fix"
  ],
  "actual_test_results": null,
  "confidence": "high | medium | low | uncertain",
  "remaining_uncertainties": [
    "Any unknowns or files that were not supplied"
  ],
  "challenges_previous_findings": [
    "Specific discrepancies or disagreements with Vision or Triage findings, if any"
  ]
}
```
"""


def build_investigation_prompt(
    issue_id: str,
    issue_description: str,
    vision_observations: Optional[object],
    triage_classification: Optional[object],
    source_code: Optional[str],
    repository_context: Optional[str] = None,
    max_code_lines: int = 1500,
) -> str:
    """Render the Investigation Agent prompt with all supplied evidence and code context."""
    # Format vision observations
    vision_section = []
    if vision_observations:
        error_msgs = getattr(vision_observations, "error_messages", []) or []
        components = getattr(vision_observations, "affected_components", []) or []
        evidence = getattr(vision_observations, "evidence", []) or []
        approx_loc = getattr(vision_observations, "approximate_location", "unspecified") or "unspecified"
        confidence = getattr(vision_observations, "confidence", "medium") or "medium"
        raw = getattr(vision_observations, "raw_observation", "") or ""

        vision_section.append("### VISION AGENT OBSERVATIONS:")
        vision_section.append(f"- Detected Error Messages: {'; '.join(error_msgs) if error_msgs else 'None'}")
        vision_section.append(f"- Affected Components: {'; '.join(components) if components else 'None'}")
        vision_section.append(f"- Location: {approx_loc}")
        vision_section.append(f"- Visual Evidence: {'; '.join(evidence) if evidence else 'None'}")
        vision_section.append(f"- Vision Confidence: {confidence}")
        if raw:
            vision_section.append(f"- Raw Observations: {raw[:300]}")
    else:
        vision_section.append("### VISION AGENT OBSERVATIONS:\n- No visual observations provided.")

    # Format triage classification
    triage_section = []
    if triage_classification:
        cls = getattr(triage_classification, "classification", "unknown") or "unknown"
        sev = getattr(triage_classification, "severity", "medium") or "medium"
        obj = getattr(triage_classification, "investigation_objective", "") or ""
        reason = getattr(triage_classification, "reason_for_delegation", "") or ""
        missing = getattr(triage_classification, "missing_information", []) or []

        triage_section.append("### TRIAGE AGENT TASK & CLASSIFICATION:")
        triage_section.append(f"- Classification: {cls}")
        triage_section.append(f"- Severity: {sev}")
        triage_section.append(f"- Investigation Objective: {obj or 'Identify root cause and propose fix'}")
        triage_section.append(f"- Reason for Delegation: {reason}")
        if missing:
            triage_section.append(f"- Missing Information Identified by Triage: {'; '.join(missing)}")
    else:
        triage_section.append("### TRIAGE AGENT TASK & CLASSIFICATION:\n- No triage task specified.")

    # Format source code
    code_section = []
    if source_code and source_code.strip():
        code_lines = source_code.split("\n")
        if len(code_lines) > max_code_lines:
            truncated = "\n".join(code_lines[:max_code_lines])
            code_section.append(f"```\n{truncated}\n... [TRUNCATED: {len(code_lines) - max_code_lines} lines omitted]\n```")
        else:
            code_section.append(f"```\n{source_code.strip()}\n```")
    else:
        code_section.append("NO SOURCE CODE SUPPLIED. Explicitly report what cannot be verified without code.")

    repo_ctx_str = f"\n### REPOSITORY CONTEXT:\n{repository_context[:500]}\n" if repository_context else ""

    return (
        f"{INVESTIGATION_SYSTEM_PROMPT}\n\n"
        f"### INCIDENT CONTEXT:\n"
        f"- Issue ID: {issue_id}\n"
        f'- Issue Description: "{issue_description.strip()}"\n\n'
        f"{chr(10).join(vision_section)}\n\n"
        f"{chr(10).join(triage_section)}\n"
        f"{repo_ctx_str}\n"
        f"### SUPPLIED SOURCE CODE:\n"
        f"{chr(10).join(code_section)}\n\n"
        f"Inspect the code, verify evidence, challenge previous agent assumptions if warranted, and respond with strictly valid JSON."
    )
