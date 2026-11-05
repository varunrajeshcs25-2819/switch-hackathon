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
  - Created `tests/test_vision_agent.py` covering:
    - Clear visible error parsing (HTTP 500)
    - Multi-issue UI layout defect parsing
    - Clean screenshot with no visible bugs (returns low confidence / honest assessment)
    - Fallback parser resilience on freeform text
    - Input sanity checks (empty base64 string handling)
    - Honest fallback when no API key is configured
    - Retry mechanism on transient network failure
  - All 7 Vision Agent tests passed.
  - All 14 existing system tests passed (Total: 21 passed).
- **Status**: STABLE & VERIFIED.

---

### Agent 2: Triage Agent
- **Status**: NEXT UP FOR AUDIT & REFINEMENT
- **Focus**:
  - Evidence-based severity classification (no inflation based on dramatic visuals).
  - Accurate missing-information identification.
  - Source-code requirement detection.
  - Formulation of focused, unambiguous investigation tasks for the Investigation Agent.

---

### Agent 3: Investigation Agent
- **Status**: PENDING
- **Focus**: Verifiable code grounding, unified diff accuracy, independent challenge generation against Vision/Triage findings.
