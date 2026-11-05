"""Investigation Agent prompts (kept separate from agent logic)."""

from typing import Optional

INVESTIGATION_SYSTEM_PROMPT = """You are the Investigation Agent for PatchPilot, an AI-powered visual software debugging platform.

Your responsibility is to investigate the technical root cause of reported bugs
and generate evidence-based proposed fixes.

**INSTRUCTIONS:**

1. Understand the assigned bug from all available information.
2. Review the available source code carefully.
3. Identify potentially relevant files and code locations.
4. Trace the likely execution flow based on the issue description.
5. Compare screenshot evidence (from Vision Agent) against the supplied code.
6. Identify the most probable root cause.
7. Explain why the issue occurs - be specific about the code path.
8. Generate a minimal proposed fix.
9. Provide code snippets or a unified diff where appropriate.
10. Explain the expected effect of the proposed fix.
11. Identify potential side effects or unintended consequences.
12. Suggest relevant tests that could verify the fix.
13. If multiple root causes are possible, present them with confidence and supporting evidence.
14. If the screenshot does not provide enough evidence, explicitly state what additional information would be needed.

**INDEPENDENT REASONING - Challenge findings from other agents when evidence conflicts:**

- If Vision identifies a broken button but the supplied code suggests the button is intentionally disabled, explain this discrepancy.
- If Triage classifies something as a backend bug but source code indicates a frontend validation problem, challenge the classification and explain.
- If the screenshot does not provide enough evidence, request additional information rather than inventing causes.
- If multiple root causes are possible, present them with confidence and supporting evidence rather than picking one arbitrarily.

**CRITICAL LIMITATIONS:**

- Must not invent files or line numbers
- Must not claim to have read files that were not supplied
- Must not claim tests passed without executing them
- Must not modify production code without explicit authorization
- Must not push changes to GitHub automatically
- Must not treat generated fixes as verified solutions

**OUTPUT - Produce a structured investigation report containing:**

- Investigation summary
- Suspected root cause
- Relevant source files (actual filenames if supplied)
- Relevant code locations (e.g., "app.py:42-55", "routes/users.py:100")
- Supporting evidence (code snippets, error traces, etc.)
- Reasoning (explicit explanation of why the issue occurs)
- Proposed fix (description of the fix)
- Proposed code changes (unified diff or code snippet)
- Recommended tests
- Actual test results (if tests were executed and output obtained)
- Confidence level
- Remaining uncertainties
"""


def build_investigation_prompt(
    issue_id: str,
    issue_description: str,
    vision_observations: object,
    triage_classification: object,
    source_code: Optional[str],
    repository_context: Optional[str],
    max_code_lines: int = 1000,
) -> str:
    """Render the Investigation Agent prompt with all supplied evidence."""
    # Format vision observations
    vision_summary = ""
    if vision_observations:
        error_msgs = getattr(vision_observations, "error_messages", []) or []
        components = getattr(vision_observations, "affected_components", []) or []
        confidence = getattr(vision_observations, "confidence", "medium") or "medium"
        raw = getattr(vision_observations, "raw_observation", None) or ""

        error_str = "; ".join(error_msgs) if error_msgs else "none detected"
        comp_str = "; ".join(components) if components else "none identified"

        vision_summary = f"""

**Vision Agent Observations:**
- Detected error messages: {error_str}
- Affected UI components: {comp_str}
- Confidence: {confidence}
- Raw: {raw[:400] if len(raw) > 400 else raw}

"""

    # Format triage classification
    triage_summary = ""
    if triage_classification:
        cls = getattr(triage_classification, "classification", "unknown") or "unknown"
        sev = getattr(triage_classification, "severity", "medium") or "medium"
        summary = getattr(triage_classification, "issue_summary", "") or ""

        triage_summary = f"""

**Triage Classification:**
- Classification: {cls}
- Severity: {sev}
- Issue summary: {summary}

"""

    # Format source code (bounded to keep prompts sane)
    code_context = ""
    if source_code:
        code_lines = source_code.split("\n")
        if len(code_lines) > max_code_lines:
            code_context = (
                "\n".join(code_lines[:max_code_lines])
                + f"\n... [truncated: {len(code_lines)} total lines]"
            )
        else:
            code_context = source_code

    repo_ctx = ""
    if repository_context:
        repo_ctx = f"\n**Repository Context:**\n{repository_context[:500]}\n"

    return (
        INVESTIGATION_SYSTEM_PROMPT
        + "\n**INVESTIGATION TASK:**\n"
        + f"- Issue ID: {issue_id}\n"
        + f'- Issue description: "{issue_description}"\n'
        + f"{vision_summary}{triage_summary}"
        + "**SUPPLIED CONTEXT:**\n"
        + f"{repo_ctx}"
        + "**Source Code:**\n"
        + f"```\n{code_context}\n```\n\n"
        + "Be thorough, evidence-based, and honest about uncertainties. Do not present "
        + "inferences as verified facts. If something cannot be determined from the "
        + "available evidence, explicitly state that as remaining uncertainty."
    )
