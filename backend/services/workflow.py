"""Agent workflow: VISION -> TRIAGE -> INVESTIGATION, coordinated in a room.

Every message in the transcript is derived from the *actual* output of an
agent (or from an actual failure), never from a script. The room enforces
identity, ordering, dedupe and a message cap so a model glitch cannot start an
infinite agent-to-agent loop.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.config import AGENT_TIMEOUT_SECONDS
from backend.integrations.switch.room import (
    KIND_CHALLENGE,
    KIND_CLASSIFICATION,
    KIND_ERROR,
    KIND_FINDINGS,
    KIND_OBSERVATION,
    KIND_TASK,
    KIND_VERDICT,
    ROOM,
    SwitchRoom,
)
from backend.services import registry

VISION = "vision"
TRIAGE = "triage"
INVESTIGATION = "investigation"
PARTICIPANTS = {VISION, TRIAGE, INVESTIGATION}


@dataclass
class PipelineResult:
    issue_id: str
    vision_observations: Any = None
    triage_classification: Any = None
    investigation_findings: Any = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    stage_ms: Dict[str, int] = field(default_factory=dict)
    source_code_supplied: bool = False


def _truncate(text: str, limit: int = 300) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


async def _with_timeout(coro, seconds: int = AGENT_TIMEOUT_SECONDS):
    return await asyncio.wait_for(coro, timeout=seconds)


def _challenges(
    vision,
    triage,
    findings,
    source_code: Optional[str],
) -> List[str]:
    """Evidence-based disagreement checks over real agent outputs.

    These are deterministic rules over the actual payloads, not scripted prose:
    each one only fires when the data itself shows a conflict.
    """
    reasons: List[str] = []

    # 1. Model-reported disagreements are always surfaced.
    for item in getattr(findings, "challenges_previous_findings", None) or []:
        if item:
            reasons.append(str(item))

    classification = (getattr(triage, "classification", "") or "").lower()
    files = getattr(findings, "relevant_source_files", None) or []
    root_cause = (getattr(findings, "suspected_root_cause", "") or "").strip()

    # 2. Backend/API classified but the investigation found no code evidence.
    if classification in {"backend_error", "api_integration_error"}:
        if not source_code:
            reasons.append(
                "Triage classified this as a backend/API error, but no source code was "
                "supplied, so no code-level evidence supports that classification."
            )
        elif not files:
            reasons.append(
                "Source code was supplied but the investigation named no relevant files, "
                "so the backend classification is not yet supported by code evidence."
            )

    # 3. Investigation returned no usable root cause.
    if not _has_real_value(root_cause):
        reasons.append(
            "The investigation produced no suspected root cause, so the delegated "
            "investigation does not resolve the triage objective yet."
        )

    # 4. Vision was uncertain, yet severity is critical.
    vision_conf = (getattr(vision, "confidence", "") or "").lower() if vision else ""
    severity = (getattr(triage, "severity", "") or "").lower()
    if vision_conf in {"uncertain", "low"} and severity == "critical":
        reasons.append(
            f"Vision confidence is '{vision_conf}' while severity is 'critical'; the "
            "visible evidence alone may not justify that severity."
        )

    return reasons


_PLACEHOLDER_ANSWERS = {
    "",
    "unknown",
    "not determined",
    "n/a",
    "unable to determine root cause",
}


def _has_real_value(text: Optional[str]) -> bool:
    """True when a field carries an actual answer rather than a placeholder."""
    return bool(text) and text.strip().lower() not in _PLACEHOLDER_ANSWERS


def _evaluate(triage, findings, source_code: Optional[str]) -> Dict[str, Any]:
    """Triage's final evaluation of whether the investigation answered the task."""
    objective = (getattr(triage, "investigation_objective", "") or "").strip()
    root_cause = (getattr(findings, "suspected_root_cause", "") or "").strip()
    fix = (getattr(findings, "proposed_fix", "") or "").strip()
    confidence = (getattr(findings, "confidence", "") or "unknown")

    missing: List[str] = []
    if not _has_real_value(root_cause):
        missing.append("root cause")
    if not _has_real_value(fix):
        missing.append("proposed fix")
    if not source_code:
        missing.append("source code evidence")

    addressed = _has_real_value(root_cause) and (
        bool(source_code) or "code" not in objective.lower()
    )
    return {
        "objective": objective,
        "addressed": addressed,
        "confidence": confidence,
        "missing": missing,
    }


async def run_pipeline(
    *,
    issue_id: str,
    issue_description: str,
    screenshot_base64: str,
    mime_type: str,
    developer_notes: str = "",
    source_code: Optional[str] = None,
    repository_context: Optional[str] = None,
    room: Optional[SwitchRoom] = None,
) -> PipelineResult:
    """Run the full three-agent workflow and return everything it produced."""
    # "system" is the workflow coordinator, not a model-backed agent; it is
    # allowed only to open the room.
    room = room or SwitchRoom(
        room_id=issue_id,
        allowed_participants=PARTICIPANTS | {"system"},
        max_messages=40,
    )
    result = PipelineResult(issue_id=issue_id, source_code_supplied=bool(source_code))

    room.post(
        sender="system",
        recipient=ROOM,
        kind=KIND_OBSERVATION,
        summary="Analysis requested",
        content={
            "issue_id": issue_id,
            "has_description": bool(issue_description),
            "has_source_code": bool(source_code),
            "model_configured": registry.model_configured(),
        },
        dedupe_key=f"{issue_id}:start",
    )

    # ---------------------------------------------------------------- Vision
    started = time.perf_counter()
    try:
        vision = await _with_timeout(
            registry.get_vision_agent().analyze_screenshot(
                screenshot_base64=screenshot_base64,
                mime_type=mime_type,
                user_description=issue_description,
            )
        )
        result.vision_observations = vision
        room.post(
            sender=VISION,
            recipient=TRIAGE,
            kind=KIND_OBSERVATION,
            summary=_truncate(
                vision.raw_observation
                or f"{len(vision.error_messages)} error message(s) visible"
            ),
            content=vision.model_dump(mode="json"),
            dedupe_key=f"{issue_id}:vision",
        )
    except Exception as exc:  # includes timeout
        result.errors.append({"agent": VISION, "error": f"{type(exc).__name__}: {exc}"})
        room.post(
            sender=VISION,
            recipient=ROOM,
            kind=KIND_ERROR,
            summary=f"Vision Agent failed: {type(exc).__name__}",
            content={"error": str(exc)},
            dedupe_key=f"{issue_id}:vision:error",
        )
    result.stage_ms["vision"] = int((time.perf_counter() - started) * 1000)

    # ---------------------------------------------------------------- Triage
    started = time.perf_counter()
    try:
        triage = await _with_timeout(
            registry.get_triage_agent().triage_issue(
                issue_description=issue_description,
                vision_observations=result.vision_observations,
                developer_notes=developer_notes,
            )
        )
        result.triage_classification = triage
        room.post(
            sender=TRIAGE,
            recipient=ROOM,
            kind=KIND_CLASSIFICATION,
            summary=_truncate(
                f"{triage.classification} / {triage.severity}: {triage.issue_summary}"
            ),
            content=triage.model_dump(mode="json"),
            dedupe_key=f"{issue_id}:triage",
        )
        room.post(
            sender=TRIAGE,
            recipient=INVESTIGATION,
            kind=KIND_TASK,
            summary=_truncate(triage.investigation_objective or "Investigate the reported issue"),
            content={
                "objective": triage.investigation_objective,
                "classification": triage.classification,
                "severity": triage.severity,
                "affected_components": triage.affected_components,
                "missing_information": triage.missing_information,
                "source_code_supplied": bool(source_code),
            },
            dedupe_key=f"{issue_id}:task",
        )
    except Exception as exc:
        result.errors.append({"agent": TRIAGE, "error": f"{type(exc).__name__}: {exc}"})
        room.post(
            sender=TRIAGE,
            recipient=ROOM,
            kind=KIND_ERROR,
            summary=f"Triage Agent failed: {type(exc).__name__}",
            content={"error": str(exc)},
            dedupe_key=f"{issue_id}:triage:error",
        )
    result.stage_ms["triage"] = int((time.perf_counter() - started) * 1000)

    # --------------------------------------------------------- Investigation
    started = time.perf_counter()
    try:
        findings = await _with_timeout(
            registry.get_investigation_agent().investigate(
                issue_id=issue_id,
                issue_description=issue_description,
                vision_observations=result.vision_observations,
                triage_classification=result.triage_classification,
                source_code=source_code,
                repository_context=repository_context,
            )
        )
        result.investigation_findings = findings
        room.post(
            sender=INVESTIGATION,
            recipient=TRIAGE,
            kind=KIND_FINDINGS,
            summary=_truncate(
                findings.suspected_root_cause
                or findings.investigation_summary
                or "Investigation completed without a confirmed root cause"
            ),
            content=findings.model_dump(mode="json"),
            dedupe_key=f"{issue_id}:findings",
        )
    except Exception as exc:
        result.errors.append(
            {"agent": INVESTIGATION, "error": f"{type(exc).__name__}: {exc}"}
        )
        room.post(
            sender=INVESTIGATION,
            recipient=ROOM,
            kind=KIND_ERROR,
            summary=f"Investigation Agent failed: {type(exc).__name__}",
            content={"error": str(exc)},
            dedupe_key=f"{issue_id}:investigation:error",
        )
    result.stage_ms["investigation"] = int((time.perf_counter() - started) * 1000)

    # -------------------------- evidence-based challenges + triage verdict
    if result.investigation_findings is not None and result.triage_classification is not None:
        reasons = _challenges(
            result.vision_observations,
            result.triage_classification,
            result.investigation_findings,
            source_code,
        )
        if reasons:
            room.post(
                sender=INVESTIGATION,
                recipient=TRIAGE,
                kind=KIND_CHALLENGE,
                summary=_truncate(reasons[0], 200),
                content={"challenges": reasons},
                dedupe_key=f"{issue_id}:challenge",
            )

        verdict = _evaluate(
            result.triage_classification, result.investigation_findings, source_code
        )
        room.post(
            sender=TRIAGE,
            recipient=ROOM,
            kind=KIND_VERDICT,
            summary=(
                "Investigation addresses the objective"
                if verdict["addressed"]
                else "Investigation incomplete: " + ", ".join(verdict["missing"])
            ),
            content=verdict,
            dedupe_key=f"{issue_id}:verdict",
        )

    result.messages = room.transcript()
    return result
