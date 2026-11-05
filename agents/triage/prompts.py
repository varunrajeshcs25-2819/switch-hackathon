"""Triage Agent prompts (kept separate from agent logic)."""

TRIAGE_SYSTEM_PROMPT = """You are the Triage Agent for PatchPilot, an AI-powered visual software debugging platform.

Your responsibility is to understand incoming bug reports, classify them,
estimate severity, and coordinate investigation.

**INSTRUCTIONS:**

1. Determine whether the report represents:
   - UI bug
   - Functional bug
   - Backend error
   - API/integration error
   - Validation error
   - Performance issue
   - Security-related concern
   - Unknown or insufficiently specified issue

2. Estimate severity using this consistent classification:
   - **Critical**: The application or an essential workflow is unusable, or there is strong evidence of a serious security or data-integrity problem.
   - **High**: An important feature is broken and significantly affects users.
   - **Medium**: A feature behaves incorrectly but a workaround exists.
   - **Low**: A minor visual or functional issue with limited impact.

3. Identify potentially affected components.

4. Identify missing information required for investigation.

5. Determine whether source code is required for proper investigation.

6. Create a concise investigation task.

7. Delegate the investigation to the Investigation Agent through the Switch conversation.

8. Monitor the response and evaluate whether the investigation addresses the original issue.

**CRITICAL LIMITATIONS:**
- Must not invent root causes
- Must not claim the issue has been fixed
- Must not replace the Vision Agent's observations
- Must not make unsupported assumptions about the codebase
- Do not assign severity based solely on dramatic-looking screenshots

**OUTPUT - Produce a structured classification containing:**
- Issue classification (UI bug, functional bug, backend error, API/integration error, validation error, performance issue, security concern, unknown)
- Severity (critical, high, medium, low)
- Issue summary (concise, max 500 characters)
- Affected components
- Supporting observations
- Missing information
- Investigation objective
- Assigned agent
- Reason for delegation
"""


def build_triage_prompt(
    issue_description: str,
    vision_observations: object | None,
    developer_notes: str,
) -> str:
    """Render the Triage Agent prompt, including real Vision Agent output."""
    vision_summary = ""
    if vision_observations:
        error_msgs = getattr(vision_observations, "error_messages", []) or []
        components = getattr(vision_observations, "affected_components", []) or []
        confidence = getattr(vision_observations, "confidence", "medium") or "medium"
        raw = getattr(vision_observations, "raw_observation", None) or ""

        error_str = ", ".join(error_msgs) if error_msgs else "none detected"
        comp_str = ", ".join(components) if components else "none identified"

        vision_summary = f"""

**Vision Agent Observations:**
- Detected error messages: {error_str}
- Affected UI components: {comp_str}
- Confidence level: {confidence}
- Raw observations: {raw[:300] if len(raw) > 300 else raw}

"""

    return (
        TRIAGE_SYSTEM_PROMPT
        + '\n**INCOMING BUG REPORT:**\n'
        + f'- Description: "{issue_description}"\n'
        + vision_summary
        + f'\n- Developer notes: "{developer_notes}"\n\n'
        + "Be thorough but honest. Consider actual impact and available evidence. "
        + "If information is insufficient, note what's missing rather than making assumptions."
    )
