# PatchPilot AI Agent Memory & Fix Tracker

This file tracks the architecture, discovered defects, fixes, refinements, test results, and preserved design decisions across all three PatchPilot AI agents (`vision`, `triage`, `investigation`).

---

## 1. Preserved Architectural Decisions
- **Agent Independence**: Vision, Triage, and Investigation agents are strictly modular in `agents/` with separate `prompts.py` and `agent.py`.
- **Honesty First**: Never fabricate source files, never invent unseen errors, never claim test execution without running tests, and never present inferences as verified facts.
- **Switch Protocol Semantics**: Addressable messaging (`sender` -> `recipient`), strict message kinds (`observation`, `classification`, `task`, `findings`, `challenge`, `verdict`), loop guards, and complete message deduplication.
- **Robust Model Fallbacks**: If no API key is provided or the network call fails, agents must return honest, transparent fallbacks rather than hallucinating fake findings.

---

## 2. Refinement Log

### Agent 1: Vision Agent
- **Date**: 2026-11-05
- **Problems Discovered**:
  1. Weak regex/string parsing missed structured fields and dropped `approximate_location`.
  2. Freeform model responses did not clearly enforce the distinction between direct visual evidence and behavioral inferences.
  3. No retry mechanism for transient API or network failures.
  4. Deprecated `datetime.utcnow()` generated Python 3.14 deprecation warnings.
- **Improvements Implemented**:
  1. **Structured JSON Output Schema**: Rewrote `VISION_SYSTEM_PROMPT` in `agents/vision/prompts.py` to enforce a JSON schema with fine-grained multi-issue isolation (`issues`, `error_messages`, `affected_components`, `approximate_location`, `evidence`, `possible_behavioral_implications`, `confidence`, `uncertainties`).
  2. **Dual-Strategy Resilient Parser**: In `agents/vision/agent.py`, added JSON extraction with trailing-comma repair and fallback line-by-line heuristic parsing if models output free-form text.
  3. **Multi-Issue Support**: Added support for detecting and documenting multiple independent defects on a single screen without merging them into an ambiguous lump.
  4. **Exponential Backoff Retry**: Wrapped `_call_vision_model` in `_call_vision_model_with_retry` with exponential backoff on transient model failures.
  5. **Direct Evidence vs. Inference Grounding**: Explicit rules in prompt to prevent hallucinating unseen browser console errors, unseen API calls, or backend stack traces.
  6. **Datetime Modernization**: Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)` for agent activity logging.
- **Tests Executed & Actual Results**:
  - Created `tests/test_vision_agent.py` covering clear errors, multi-issue layouts, clean screens, text fallback, empty inputs, and retries.
  - All 7 Vision Agent tests passed.
- **Status**: STABLE & VERIFIED.

---

### Agent 2: Triage Agent
- **Date**: 2026-11-05
- **Problems Discovered**:
  1. Over-simplified string matching in heuristic fallback caused classification bleed (e.g. prompt keywords falsely triggered security concern).
  2. Prompt lacked explicit rules preventing automatic escalation of all HTTP 500s to Critical regardless of context.
  3. No evaluation and challenge mechanism implemented directly within `TriageAgent` to challenge incomplete or unverified Investigation Agent findings.
  4. Missing contradiction detection between human reports and visual evidence.
- **Improvements Implemented**:
  1. **Evidence-Based Severity Engine**: Defined explicit rules: `critical` reserved for blocked core workflows (login, checkout, total crash) or data-integrity/security risks; non-critical backend 500s (e.g. avatar fail) classified as `high` or `medium`.
  2. **Intelligent Multi-Category Classification**: Added comprehensive prompt and parsing mapping for `ui_bug`, `functional_bug`, `backend_error`, `api_integration_error`, `validation_error`, `performance_issue`, `security_concern`, and `unknown`.
  3. **Contradiction Detection**: Explicitly compares developer descriptions against Vision Agent visual evidence, highlighting discrepancies in supporting observations.
  4. **Actionable Task Delegation**: Formulates structured deliverables and determines if source code is required rather than issuing vague commands.
  5. **Evaluation & Challenge Engine (`evaluate_investigation`)**: Added evaluation method in `TriageAgent` to review Investigation Agent outputs and issue challenges if root causes are speculative or code evidence is missing.
  6. **Dual-Strategy Parser**: Enforced structured JSON output from reasoning models with comma repair and targeted heuristic fallback.
  7. **Modernized Timestamps**: Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`.
- **Tests Executed & Actual Results**:
  - Created `tests/test_triage_agent.py` covering critical backend crashes, localized errors, security leaks, layout bugs, JSON parsing, and deliverable evaluation.
  - All 7 Triage Agent tests passed.
- **Status**: STABLE & VERIFIED.

---

### Agent 3: Investigation Agent
- **Date**: 2026-11-05
- **Problems Discovered**:
  1. Loose parsing relied on ad-hoc regex without guarding against hallucinated files when source code was not supplied.
  2. No automated mechanism for generating unified diffs or verifying code locations in static code fallback mode.
  3. Missing independent challenge generation (e.g. when code shows a disabled button is by design, or when code contradicts triage classification).
  4. Deprecated `datetime.utcnow()` used in activity logging.
- **Improvements Implemented**:
  1. **Empirical Code Grounding & Anti-Hallucination**: Rewrote prompt in `agents/investigation/prompts.py` enforcing that every file, symbol, and location must exist in the supplied code context. When code is missing, the agent explicitly reports inability to verify rather than fabricating code causes.
  2. **Independent Reasoning & Challenge Engine**: Implemented `challenges_previous_findings` generation to challenge Vision (e.g. `disabled={!isValid}` is by design) and Triage (e.g. frontend validation schema vs backend error).
  3. **Unified Diff & Minimal Fix Generation**: Enforces standard unified diff patches (`--- original`, `+++ fixed`) targeting specific functions instead of rewrites.
  4. **Deterministic Static Code Heuristic Scanner**: In `_heuristic_investigation_fallback`, added syntax scanning for runtime exceptions (ZeroDivision, KeyError, null dereferences), regex extraction of real filenames (`# file: ...`), and line-level code location pointers.
  5. **Dual-Strategy Resilient Parser**: Structured JSON extraction with comma repair and heuristic fallback.
  6. **Modernized Timestamps**: Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`.
- **Tests Executed & Actual Results**:
  - Created `tests/test_investigation_agent.py` covering:
    - Code inspection identifying real root causes and generating unified diff patches
    - Honest limitations when source code is absent (no hallucinated files, low confidence)
    - Active challenge generation when button is disabled by design
    - Structured JSON parsing from reasoning models
    - Prompt formatting with visual observations, triage task, and code context
  - All 5 Investigation Agent tests passed.
  - All 33 total tests in the project test suite passed (100% passing).
- **Status**: STABLE & VERIFIED.
