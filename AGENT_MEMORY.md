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
  - Created `tests/test_triage_agent.py` covering:
    - Critical backend crash on essential workflows (e.g. checkout 500 -> Critical)
    - Localized backend 500 handling (e.g. avatar load -> High/Medium, not Critical)
    - Security credential leak handling (Critical Security Concern)
    - Visual layout bugs (Low/Medium UI Bug)
    - Structured JSON parsing from reasoning models
    - Evaluation & challenge engine for incomplete vs. complete investigation deliverables
  - All 7 Triage Agent tests passed.
  - All 28 total tests in test suite passed (100% passing).
- **Status**: STABLE & VERIFIED.

---

### Agent 3: Investigation Agent
- **Status**: NEXT UP FOR AUDIT & REFINEMENT
- **Focus**: Verifiable code grounding, AST/symbol checking, unified diff validity, independent counter-challenge generation against Vision/Triage findings.
