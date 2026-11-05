"""Conversion between live issue objects and JSON stored in SQLite."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict

from backend.models import (
    PydanticFinalReport,
    PydanticInvestigationFindings,
    PydanticIssueBase,
    PydanticTriageClassification,
    PydanticVisionObservations,
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def serialize_issue(data: Dict[str, Any]) -> Dict[str, Any]:
    """Turn an in-memory issue entry into a JSON-safe payload."""
    payload: Dict[str, Any] = {}

    issue = data.get("issue")
    if isinstance(issue, PydanticIssueBase):
        payload["issue"] = issue.model_dump(mode="json")
    elif isinstance(issue, dict):
        payload["issue"] = _jsonable(issue)

    for key in (
        "vision_observations",
        "triage_classification",
        "investigation_findings",
    ):
        value = data.get(key)
        if hasattr(value, "model_dump"):
            payload[key] = value.model_dump(mode="json")
        else:
            payload[key] = None

    payload["activity_history"] = _jsonable(data.get("activity_history") or [])
    payload["messages"] = _jsonable(data.get("messages") or [])
    payload["source_code_supplied"] = bool(data.get("source_code_supplied"))
    payload["created_at"] = _jsonable(issue.created_at) if isinstance(issue, PydanticIssueBase) else None
    payload["updated_at"] = (
        _jsonable(issue.updated_at) if isinstance(issue, PydanticIssueBase) else None
    )
    return payload


def deserialize_issue(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild live objects from a stored payload."""
    data: Dict[str, Any] = {
        "activity_history": payload.get("activity_history") or [],
        "messages": payload.get("messages") or [],
        "source_code_supplied": payload.get("source_code_supplied", False),
    }

    if payload.get("issue"):
        data["issue"] = PydanticIssueBase.model_validate(payload["issue"])

    vision = payload.get("vision_observations")
    data["vision_observations"] = (
        PydanticVisionObservations.model_validate(vision) if vision else None
    )

    triage = payload.get("triage_classification")
    data["triage_classification"] = (
        PydanticTriageClassification.model_validate(triage) if triage else None
    )

    findings = payload.get("investigation_findings")
    data["investigation_findings"] = (
        PydanticInvestigationFindings.model_validate(findings) if findings else None
    )
    return data


def build_report_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize the final report object for API responses."""
    report: PydanticFinalReport = data["report"]
    return report.model_dump(mode="json")
