# PatchPilot AI Agent Memory & Fix Tracker

This file tracks the architecture, discovered defects, fixes, refinements, test results, and preserved design decisions across all three PatchPilot AI agents (`vision`, `triage`, `investigation`) and their multi-agent collaboration room.

---

## 1. Preserved Architectural Decisions
- **Agent Independence**: Vision, Triage, and Investigation agents are strictly modular in `agents/` with separate `prompts.py` and `agent.py`.
- **Honesty First**: Never fabricate source files, never invent unseen errors, never claim test execution without running tests, and never present inferences as verified facts.
- **Switch Protocol Semantics**: Addressable messaging (`sender` -> `recipient`), strict message kinds (`observation`, `classification`, `task`, `findings`, `challenge`, `verdict`), loop guards, duplicate suppression, and explicit `reply_to` linkage.
- **Robust Model Fallbacks**: If no API key is provided or the network call fails, agents must return honest, transparent fallbacks rather than hallucinating fake findings.

---

## 2. Refinement Log

### Agent 1: Vision Agent
- **Date**: 2026-11-05
- **Improvements Implemented**:
  1. **Structured JSON Output Schema**: Enforced JSON schema with fine-grained multi-issue isolation (`issues`, `error_messages`, `affected_components`, `approximate_location`, `evidence`, `possible_behavioral_implications`, `confidence`, `uncertainties`).
  2. **Dual-Strategy Resilient Parser**: Structured JSON extraction with trailing-comma repair and fallback line-by-line heuristic parsing.
  3. **Multi-Issue Support**: Distinct bugs on single screen isolated independently.
  4. **Exponential Backoff Retry**: Wrapped in `_call_vision_model_with_retry`.
  5. **Direct Evidence vs. Inference Grounding**: Explicit rules preventing hallucinating unseen console logs or backend traces.
  6. **Datetime Modernization**: Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`.
- **Status**: STABLE & VERIFIED (7/7 tests passed).

---

### Agent 2: Triage Agent
- **Date**: 2026-11-05
- **Improvements Implemented**:
  1. **Evidence-Based Severity Engine**: Core workflows (login/register/checkout crashes) -> `critical`; isolated widgets -> `high`/`medium`.
  2. **Multi-Category Classification**: Added mapping for `ui_bug`, `functional_bug`, `backend_error`, `api_integration_error`, `validation_error`, `performance_issue`, `security_concern`, `unknown`.
  3. **Contradiction Detection**: Explicitly cross-references developer descriptions against Vision Agent observations.
  4. **Intelligent Task Delegation**: Specifies focused deliverables and determines source code requirements.
  5. **Evaluation & Challenge Engine**: Evaluates Investigation Agent outputs for completeness and evidence.
  6. **Dual-Strategy Parser**: Enforced structured JSON output with fallback.
- **Status**: STABLE & VERIFIED (7/7 tests passed).

---

### Agent 3: Investigation Agent
- **Date**: 2026-11-05
- **Improvements Implemented**:
  1. **Empirical Code Grounding & Anti-Hallucination**: Cites only files and symbols that exist in supplied code context.
  2. **Independent Reasoning & Challenge Engine**: Automatically detects when visual bug reports contradict code logic (e.g. `disabled={!isValid}` is by design).
  3. **Unified Diff & Minimal Fix Generation**: Enforces standard unified diff patches (`--- original`, `+++ fixed`).
  4. **Deterministic Static Code Heuristic Scanner**: Scans for runtime exception patterns (ZeroDivision, KeyError, null references), parses file headers, and reports verified lines.
  5. **Dual-Strategy Resilient Parser**: Structured JSON extraction with comma repair.
- **Status**: STABLE & VERIFIED (5/5 tests passed).

---

### Multi-Agent Integration & Collaboration Layer
- **Date**: 2026-11-05
- **Problems Discovered**:
  1. Lack of explicit `reply_to` links between task delegation, findings, and review verdict in the Switch room message stream.
  2. Missing unified verification of the full feedback loop (`VISION -> TRIAGE -> INVESTIGATION -> TRIAGE REVIEW -> FINAL REPORT`).
- **Improvements Implemented**:
  1. **Room Traceability & Reply-To Chains**: Added explicit message `reply_to` threading linking `observation` -> `classification` -> `task` -> `findings` -> `challenge` -> `verdict`.
  2. **Task ID Tracking**: Injected unique, traceable `task_id` (`task-{issue_id}`) into the delegation payload.
  3. **Automated Feedback Loop Review**: Connected Triage Agent review directly to the room transcript, issuing `challenge` and `verdict` messages based on empirical evidence and code presence.
  4. **End-to-End Test Suite**: Created `tests/test_multiagent_integration.py` covering visual bug workflow, backend 500 error with source code diffs, missing source code challenges, contradictory findings (disabled button by design), and room traceability.
- **Tests Executed & Actual Results**:
  - All 5 integration tests in `tests/test_multiagent_integration.py` passed.
  - Full test suite: **38/38 tests passing (100% pass rate)**.
- **Status**: STABLE & VERIFIED.

---

### Complete Product Quality & Multi-Agent Intelligence Overhaul
- **Date**: 2026-11-06
- **Problems Discovered**:
  1. Frontend UI had basic styling without the visual cues and information hierarchy of modern engineering platforms.
  2. Investigation reports lacked distinction between directly observed facts, inferred causes, and proposed fixes.
  3. Screenshots containing IDEs, terminals, or compiler errors (such as unclosed Java parenthesis) required on-device OCR extraction to prevent visual misses.
  4. Workflow state machine needed explicit states for tracking pipeline execution.
- **Improvements Implemented**:
  1. **5-Tier Epistemological Evidence Taxonomy**: Integrated `[OBSERVED]`, `[INFERRED]`, `[CODE VERIFIED]`, `[TEST VERIFIED]`, and `[PROPOSED]` classifications into backend models, reports, and frontend UI.
  2. **On-Device RapidOCR Engine**: Integrated `rapidocr-onnxruntime` into Vision Agent, reading syntax errors, compiler tracebacks, and terminal logs from uploaded screenshots without external API calls.
  3. **Multi-Agent State Machine**: Expanded `IssueStatus` enum with granular pipeline states (`VALIDATING_INPUT`, `VISION_RUNNING`, `TRIAGE_RUNNING`, `INVESTIGATION_RUNNING`, `AWAITING_REVIEW`, `REPORT_READY`).
  4. **Engineering Workspace Redesign**:
     - **Screen 1 (Command Center)**: High-density dark engineering console with real-time stats from SQLite, bug callset table, and live agent room stream.
     - **Screen 2 (New Bug Analysis)**: Full-featured submission workspace with drag-and-drop file upload, thumbnail preview, "+ Add New Bug" reset flow, and code snippet inputs.
     - **Screen 3 (Live Agent Workspace)**: Visual 4-stage pipeline topology (`VISION` -> `TRIAGE` -> `INVESTIGATION` -> `REVIEW`), real-time Switch room transcript stream, and expandable JSON payload inspector.
     - **Screen 4 (Investigation Reports)**: Comprehensive post-mortem layout with 5-tier evidence badges, copyable unified diffs, root-cause explanation, and copy actions.
- **Tests Executed & Actual Results**:
  - Executed Java compilation error end-to-end test (`System.out.println("Hello World (`) with dark-theme IDE screenshot.
  - Vision successfully extracted OCR text and identified syntax error.
  - Triage classified as `functional_bug`/`backend_error` with `medium` severity.
  - Investigation identified missing quote and parenthesis and generated valid unified diff (`--- a/App.java` -> `+++ b/App.java`).
  - Frontend compiled cleanly with zero build errors (`dist/assets/index-B47A4K9H.js`).
- **Status**: PRODUCTION READY & VERIFIED.
