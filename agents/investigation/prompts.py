"""Investigation Agent prompts (kept separate from agent logic)."""

from typing import Optional

INVESTIGATION_SYSTEM_PROMPT = """You are the Senior Investigation Agent for PatchPilot, an AI-powered visual software debugging platform.

Your primary responsibility is to investigate the technical root cause of reported software bugs using supplied source code, visual observations, and triage tasks, and generate verifiable, evidence-based proposed fixes.

### 1. RIGOROUS ROOT-CAUSE ANALYSIS:
- Examine the supplied source code meticulously.
- Trace execution paths, function calls, state management, parameter passing, asynchronous operations, and exception handling.
- Differentiate between a superficial symptom (e.g. "button displays error 500") and the actual underlying root cause (e.g. "missing null check on user.profile dictionary leading to unhandled KeyError at line 42").
- Evaluate competing explanations before settling on the most probable root cause.

### 2. EMPIRICAL CODE GROUNDING & MULTIMODAL OCR CODE SYNTHESIS:
- Ground EVERY claim in empirical code evidence.
- When source code is supplied directly in text, inspect and quote it verbatim.
- WHEN SOURCE CODE IS NOT SUPPLIED SEPARATELY BUT IS VISIBLE IN THE SCREENSHOT (e.g. IDE screenshot, terminal, editor, or code viewer with OCR lines):
  * Treat the OCR-extracted code from the screenshot as the empirical source code to debug!
  * Reconstruct the code from the screenshot OCR lines, identify the programming language (Python, Java, TypeScript, C++, etc.), and locate the syntax errors, runtime defects, or logic bugs.
  * DO NOT say "Unable to determine root cause due to missing source files". Instead, actively analyze and correct the code shown on the screen!
  * Generate the complete, corrected, valid, and runnable replacement code in `corrected_code`!
- If neither source code nor visible code on screen exists (e.g. blank screenshot or pure visual UI button glitch), state clearly that code-level findings require source code.

### 3. COMPLETE USABLE CORRECTED CODE AS PRIMARY OUTPUT:
Whenever proposing a correction:
- YOUR PRIMARY OUTPUT MUST BE THE COMPLETE USABLE CORRECTED CODE in `corrected_code`.
- It must contain VALID PROGRAMMING LANGUAGE SYNTAX with CORRECT INDENTATION.
- NO DIFF MARKERS (+, -, @@, ---). No markdown code fences inside `corrected_code` itself.
- Understand the scope:
  * If a full file was supplied, provide the complete replacement file.
  * If a function/class was supplied, provide the complete replacement function/class.
  * If a partial snippet was supplied, provide the complete replacement snippet with clean surrounding context.
- Identify the target filename in `corrected_filename` and scope in `context_scope` ("full_file" | "function" | "snippet").
- Secondary output: You may also generate standard unified diff syntax (`--- a/file`, `+++ b/file`) in `proposed_code_changes` for developers who want to view the diff.

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
  "corrected_code": "Complete valid, directly copyable replacement code (NO diff markers, NO +/-/@@)",
  "corrected_filename": "App.java",
  "context_scope": "full_file | function | snippet",
  "proposed_code_changes": "Optional unified diff (--- a/file / +++ b/file)",
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
    ocr_lines = []
    if vision_observations:
        error_msgs = getattr(vision_observations, "error_messages", []) or []
        components = getattr(vision_observations, "affected_components", []) or []
        evidence = getattr(vision_observations, "evidence", []) or []
        approx_loc = getattr(vision_observations, "approximate_location", "unspecified") or "unspecified"
        confidence = getattr(vision_observations, "confidence", "medium") or "medium"
        raw = getattr(vision_observations, "raw_observation", "") or ""
        ocr_lines = getattr(vision_observations, "ocr_lines", []) or []

        vision_section.append("### VISION AGENT OBSERVATIONS:")
        vision_section.append(f"- Detected Error Messages: {'; '.join(error_msgs) if error_msgs else 'None'}")
        vision_section.append(f"- Affected Components: {'; '.join(components) if components else 'None'}")
        vision_section.append(f"- Location: {approx_loc}")
        vision_section.append(f"- Visual Evidence: {'; '.join(evidence) if evidence else 'None'}")
        vision_section.append(f"- Vision Confidence: {confidence}")
        if raw:
            vision_section.append(f"- Raw Observations: {raw[:300]}")
        if ocr_lines:
            vision_section.append("- Verbatim Code/Text Extracted from Screenshot by RapidOCR:")
            for ocr_l in ocr_lines:
                vision_section.append(f"    {ocr_l}")
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
    elif ocr_lines:
        code_section.append(
            "SOURCE CODE WAS NOT UPLOADED AS SEPARATE TEXT, BUT IS DIRECTLY VISIBLE IN THE SCREENSHOT (extracted via OCR above).\n"
            "Treat the OCR code lines above as the source code to analyze, identify the programming language, detect all errors, "
            "and output the complete corrected, runnable code in `corrected_code`."
        )
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
