"""The vision -> triage -> investigation pipeline, coordinated through a SwitchRoom.

A failing agent never aborts the pipeline: its error is posted to the room, recorded in
`errors`, and the next agent runs with whatever is available.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from backend.integrations.switch.room import (
    KIND_CLASSIFICATION,
    KIND_ERROR,
    KIND_FINDINGS,
    KIND_OBSERVATIONS,
    KIND_TASK,
    SwitchRoom,
)
from backend.models import (
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


def _fail(room: SwitchRoom, result: PipelineResult, agent: str, exc: Exception, key: str) -> None:
    result.errors.append({"agent": agent, "error": str(exc)})
    room.post(
        sender=agent,
        recipient="room",
        kind=KIND_ERROR,
        summary=f"{agent} agent failed",
        content={"error": str(exc)},
        dedupe_key=f"{room.room_id}:{key}:error",
    )


async def run_pipeline(
    issue_id: str,
    issue_description: str,
    screenshot_base64: str,
    mime_type: str = "image/png",
    developer_notes: str = "",
    source_code: Optional[str] = None,
) -> PipelineResult:
    room = SwitchRoom(room_id=issue_id, allowed_participants=PARTICIPANTS)
    result = PipelineResult()

    # 1. Vision
    room.post(
        SYSTEM, VISION, KIND_TASK, "Analyze the submitted screenshot",
        {"issue_description": issue_description, "has_source_code": bool(source_code)},
        dedupe_key=f"{issue_id}:task:vision",
    )
    try:
        vision = await registry.get_vision_agent().analyze_screenshot(
            screenshot_base64=screenshot_base64, mime_type=mime_type, user_description=issue_description
        )
        vision.issue_id = issue_id
        result.vision_observations = vision
        room.post(
            VISION, TRIAGE, KIND_OBSERVATIONS, (vision.summary or "Observations ready")[:300],
            vision.model_dump(mode="json"), dedupe_key=f"{issue_id}:observations",
        )
    except Exception as exc:
        _fail(room, result, VISION, exc, "vision")

    # 2. Triage
    try:
        triage = await registry.get_triage_agent().triage_issue(
            issue_description=issue_description,
            vision_observations=result.vision_observations,
            developer_notes=developer_notes,
        )
        triage.issue_id = issue_id
        result.triage_classification = triage
        room.post(
            TRIAGE, INVESTIGATION, KIND_CLASSIFICATION,
            f"{triage.classification.value} / {triage.severity.value}: {triage.investigation_objective}"[:300],
            triage.model_dump(mode="json"), dedupe_key=f"{issue_id}:classification",
        )
    except Exception as exc:
        _fail(room, result, TRIAGE, exc, "triage")

    # 3. Investigation (runs even if earlier steps failed; it reports its own limitations)
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
        room.post(
            INVESTIGATION, TRIAGE, KIND_FINDINGS,
            (findings.suspected_root_cause or findings.investigation_summary or "Findings ready")[:300],
            findings.model_dump(mode="json"), dedupe_key=f"{issue_id}:findings",
        )
    except Exception as exc:
        _fail(room, result, INVESTIGATION, exc, "investigation")

    result.messages = room.transcript()
    return result
