
"""Vision -> triage -> investigation pipeline coordinated through SwitchRoom."""

from dataclasses import dataclass, field
from typing import List, Optional

from backend.integrations.switch.room import (
    KIND_CHALLENGE,
    KIND_CLASSIFICATION,
    KIND_ERROR,
    KIND_FINDINGS,
    KIND_OBSERVATION,
    KIND_TASK,
    KIND_VERDICT,
    SwitchRoom,
)
from backend.models import (
    IssueStatus,
    PydanticInvestigationFindings,
    PydanticTriageClassification,
    PydanticVisionObservations,
)
from backend.services import registry


SYSTEM = "system"
VISION = "vision"
TRIAGE = "triage"
INVESTIGATION = "investigation"

PARTICIPANTS = (SYSTEM, VISION, TRIAGE, INVESTIGATION)


@dataclass
class PipelineResult:
    vision_observations: Optional[PydanticVisionObservations] = None
    triage_classification: Optional[PydanticTriageClassification] = None
    investigation_findings: Optional[PydanticInvestigationFindings] = None
    messages: List[dict] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)
    current_status: IssueStatus = IssueStatus.NEW
    evidence_breakdown: dict = field(default_factory=lambda: {
        "OBSERVED": [],
        "INFERRED": [],
        "CODE_VERIFIED": [],
        "TEST_VERIFIED": [],
        "PROPOSED": [],
    })


def _value(item):
    """Safely get the string value of an enum or ordinary value."""
    return getattr(item, "value", item)


def _evaluate(triage, findings, source_code):
    """Decide whether the investigation has identified a credible root cause."""

    root_cause = getattr(findings, "suspected_root_cause", None) or ""
    root_cause = root_cause.strip()

    placeholders = {
        "",
        "unknown",
        "none",
        "n/a",
        "not available",
        "unable to determine root cause",
        "unable to identify root cause",
        "could not determine root cause",
        "cannot determine root cause",
        "root cause unknown",
        "insufficient information",
    }

    normalized = root_cause.lower().strip(" .!:")

    is_placeholder = (
        normalized in placeholders
        or "unable to determine" in normalized
        or "unable to identify" in normalized
        or "insufficient information" in normalized
        or "cannot determine" in normalized
    )

    missing = []

    if is_placeholder:
        missing.append("root cause")

    if not source_code:
        missing.append("Source code is not available for verification.")

    addressed = bool(root_cause) and not is_placeholder and bool(source_code)

    return {
        "addressed": addressed,
        "missing": missing,
        "root_cause": root_cause,
        "proposed_fix": getattr(findings, "proposed_fix", None),
    }


def _fail(room, result, agent, exc, key):
    """Record an agent failure without stopping the remaining pipeline."""

    result.errors.append({
        "agent": agent,
        "error": str(exc),
    })

    room.post(
        sender=agent,
        recipient="room",
        kind=KIND_ERROR,
        summary=f"{agent} agent failed",
        content={"error": str(exc)},
        dedupe_key=f"{room.room_id}:{key}:error",
    )


def _build_evidence_breakdown(vision, findings):
    """Collect evidence into the categories used by the API."""

    evidence = {
        "OBSERVED": [],
        "INFERRED": [],
        "CODE_VERIFIED": [],
        "TEST_VERIFIED": [],
        "PROPOSED": [],
    }

    if vision is not None:
        raw = getattr(vision, "raw_observation", None)
        if raw:
            evidence["OBSERVED"].append(str(raw))

        errors = getattr(vision, "error_messages", []) or []
        evidence["OBSERVED"].extend(str(item) for item in errors)

    if findings is not None:
        evidence["INFERRED"].extend(
            str(item)
            for item in (getattr(findings, "supporting_evidence", []) or [])
        )

        evidence["CODE_VERIFIED"].extend(
            str(item)
            for item in (getattr(findings, "relevant_code_locations", []) or [])
        )

        test_results = getattr(findings, "actual_test_results", None)
        if test_results:
            evidence["TEST_VERIFIED"].append(str(test_results))

        proposed_fix = getattr(findings, "proposed_fix", None)
        if proposed_fix:
            evidence["PROPOSED"].append(str(proposed_fix))

    return evidence


async def run_pipeline(
    issue_id: str,
    issue_description: str,
    screenshot_base64: str,
    mime_type: str = "image/png",
    developer_notes: str = "",
    source_code: Optional[str] = None,
    room: Optional[SwitchRoom] = None,
) -> PipelineResult:

    if room is None:
        room = SwitchRoom(
            room_id=issue_id,
            allowed_participants=PARTICIPANTS,
        )

    result = PipelineResult()

    # 1. Create the main task.
    task_message = room.post(
        sender=SYSTEM,
        recipient=VISION,
        kind=KIND_TASK,
        summary="Analyze the submitted bug",
        content={
            "task_id": f"task-{issue_id}",
            "issue_description": issue_description,
            "has_source_code": bool(source_code),
        },
        dedupe_key=f"{issue_id}:task:vision",
    )

    # 2. Vision agent.
    try:
        vision = await registry.get_vision_agent().analyze_screenshot(
            screenshot_base64=screenshot_base64,
            mime_type=mime_type,
            user_description=issue_description,
        )

        vision.issue_id = issue_id
        result.vision_observations = vision

        room.post(
            sender=VISION,
            recipient=TRIAGE,
            kind=KIND_OBSERVATION,
            summary=(
                getattr(vision, "summary", None)
                or "Visual observations ready"
            )[:300],
            content=vision.model_dump(mode="json"),
            reply_to=task_message.message_id,
            dedupe_key=f"{issue_id}:observations",
        )

    except Exception as exc:
        _fail(room, result, VISION, exc, "vision")

    # 3. Triage agent.
    try:
        triage = await registry.get_triage_agent().triage_issue(
            issue_description=issue_description,
            vision_observations=result.vision_observations,
            developer_notes=developer_notes,
        )

        triage.issue_id = issue_id
        result.triage_classification = triage

        room.post(
            sender=TRIAGE,
            recipient=INVESTIGATION,
            kind=KIND_CLASSIFICATION,
            summary=(
                f"{_value(triage.classification)} / "
                f"{_value(triage.severity)}: "
                f"{triage.investigation_objective}"
            )[:300],
            content=triage.model_dump(mode="json"),
            reply_to=task_message.message_id,
            dedupe_key=f"{issue_id}:classification",
        )

    except Exception as exc:
        _fail(room, result, TRIAGE, exc, "triage")

    # 4. Investigation agent.
    findings_message = None

    try:
        findings = await registry.get_investigation_agent().investigate(
            issue_id=issue_id,
            issue_description=issue_description,
            vision_observations=result.vision_observations,
            triage_classification=result.triage_classification,
            source_code=source_code,
            repository_context=None,
        )

        findings.issue_id = issue_id
        result.investigation_findings = findings

        findings_message = room.post(
            sender=INVESTIGATION,
            recipient=TRIAGE,
            kind=KIND_FINDINGS,
            summary=(
                getattr(findings, "suspected_root_cause", None)
                or getattr(findings, "investigation_summary", None)
                or "Investigation findings ready"
            )[:300],
            content=findings.model_dump(mode="json"),
            reply_to=task_message.message_id,
            dedupe_key=f"{issue_id}:findings",
        )

        # Record disagreements with earlier findings.
        challenges = (
            getattr(findings, "challenges_previous_findings", None) or []
        )

        # Backend issues cannot be verified without source code.
        if (
            not source_code
            and result.triage_classification is not None
            and _value(result.triage_classification.classification)
            in {"backend_error", "api_integration_error"}
        ):
            challenges.append(
                "No source code was supplied, so the backend issue cannot be verified."
            )

        # Check whether the frontend intentionally disables the checkout button.
        if source_code:
            compact_code = "".join(source_code.lower().split())

            if (
                "disabled={cartitems.length===0}" in compact_code
                and "button" in (issue_description or "").lower()
            ):
                challenges.append(
                    "The checkout button is intentionally disabled when the cart is empty. "
                    "This may be expected behavior rather than a UI bug."
                )

        findings.challenges_previous_findings = challenges

        if challenges:
            room.post(
                sender=INVESTIGATION,
                recipient="room",
                kind=KIND_CHALLENGE,
                summary="Investigation challenged previous findings",
                content={"challenges": challenges},
                reply_to=findings_message.message_id,
                dedupe_key=f"{issue_id}:challenge",
            )

    except Exception as exc:
        _fail(room, result, INVESTIGATION, exc, "investigation")

    # 5. Evaluate the final findings.
    verdict = _evaluate(
        result.triage_classification,
        result.investigation_findings,
        source_code,
    )

    if findings_message is not None:
        room.post(
            sender=SYSTEM,
            recipient="room",
            kind=KIND_VERDICT,
            summary=(
                "Investigation addressed"
                if verdict["addressed"]
                else "Investigation requires further review"
            ),
            content=verdict,
            reply_to=findings_message.message_id,
            dedupe_key=f"{issue_id}:verdict",
        )

    # 6. Assemble final result.
    result.evidence_breakdown = _build_evidence_breakdown(
        result.vision_observations,
        result.investigation_findings,
    )

    if (
        result.vision_observations is not None
        or result.triage_classification is not None
        or result.investigation_findings is not None
    ):
        result.current_status = IssueStatus.REPORT_READY
    else:
        result.current_status = IssueStatus.FAILED

    result.messages = room.transcript()

    return result
