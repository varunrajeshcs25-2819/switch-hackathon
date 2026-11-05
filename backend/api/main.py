"""
PatchPilot Backend API

FastAPI application that serves the PatchPilot platform:

- Screenshot upload and validation
- Three-agent workflow coordinated through a Switch-style room
  (vision -> triage -> investigation)
- Issue persistence in SQLite
- Full agent transcript exposed to the frontend

Endpoints:
- POST /issues/                    Create issue + run the agent workflow
- GET  /issues/                    List issues
- GET  /issues/{id}                Issue detail
- GET  /issues/{id}/messages       Real agent-to-agent transcript (Switch room)
- POST /issues/{id}/investigate    Re-investigate with supplied source code
- GET  /stats                      Dashboard counters + recent activity
- POST /agents/vision/analyze      Vision Agent only
- POST /agents/triage/classify     Triage Agent only
- POST /agents/investigate         Investigation Agent only
- GET  /reports/{id}               Final evidence-based report
"""

import base64
import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure the project root is importable when uvicorn is started from anywhere.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import ALLOWED_ORIGINS, DATABASE_URL
from backend.database.serialization import deserialize_issue, serialize_issue
from backend.database.store import IssueStore
from backend.integrations.switch.room import (
    KIND_FINDINGS,
    KIND_TASK,
    SwitchRoom,
)
from backend.models import (
    AgentRole,
    IssueClassification,
    IssueStatus,
    PydanticFinalReport,
    PydanticInvestigationFindings,
    PydanticIssueBase,
    PydanticTriageClassification,
    PydanticVisionObservations,
    SeverityLevel,
)
from backend.services import registry
from backend.services.workflow import (
    INVESTIGATION,
    PARTICIPANTS,
    TRIAGE,
    run_pipeline,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _sqlite_path(database_url: str) -> str:
    """Accept sqlite:///abs/path, sqlite:///./rel.db, or a plain path."""
    if database_url.startswith("sqlite:///"):
        path = database_url[len("sqlite:///") :]
    elif database_url.startswith("sqlite://"):
        path = database_url[len("sqlite://") :]
    else:
        path = database_url
    if path.startswith("/") and not os.path.isabs(path):
        path = path.lstrip("/")
    return os.path.abspath(path) if not os.path.isabs(path) else path


app = FastAPI(
    title="PatchPilot API",
    description="AI-powered visual software debugging and investigation platform",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = _sqlite_path(DATABASE_URL)
store = IssueStore(DB_PATH)

# Hot cache; every mutation is mirrored to SQLite so restarts are lossless.
issues_db: dict = {issue_id: deserialize_issue(payload) for issue_id, payload in store.load_all().items()}


# ---- Request / response models ----


class IssueResponse(BaseModel):
    issue_id: str
    status: str
    message: str


class IssueDetailResponse(BaseModel):
    issue_id: str
    description: str
    status: str
    classification: Optional[str] = None
    severity: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TriageClassificationRequest(BaseModel):
    issue_description: str
    vision_observations_json: str = ""


class InvestigationRequest(BaseModel):
    source_code: str = ""
    repository_context: Optional[str] = None


# ---- Persistence helpers ----


def _persist(issue_id: str) -> None:
    data = issues_db.get(issue_id)
    if data is not None:
        store.save(issue_id, serialize_issue(data))


def _activity_from_messages(issue_id: str, messages: List[dict]) -> List[dict]:
    """Turn the real transcript into traceable activity entries."""
    roles = {
        "vision": AgentRole.VISION.value,
        "triage": AgentRole.TRIAGE.value,
        "investigation": AgentRole.INVESTIGATION.value,
    }
    history = []
    for message in messages:
        role = roles.get(message.get("sender"))
        if role is None:  # system message
            continue
        history.append(
            {
                "timestamp": message.get("created_at") or datetime.utcnow().isoformat(),
                "agent_role": role,
                "action": message.get("kind", "message"),
                "details": message.get("summary", ""),
                "success": message.get("kind") != "error",
                "error_message": (
                    (message.get("content") or {}).get("error")
                    if message.get("kind") == "error"
                    else None
                ),
            }
        )
    return history


def _normalize_activity_history(entries):
    """Coerce stored activity dicts into valid PydanticAgentActivity payloads."""
    history = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        role = entry.get("agent_role") or AgentRole.VISION.value
        try:
            role_enum = AgentRole(role)
        except ValueError:
            role_enum = AgentRole.VISION
        history.append(
            {
                "timestamp": entry.get("timestamp") or datetime.utcnow(),
                "agent_role": role_enum,
                "action": entry.get("action", "unknown"),
                "details": entry.get("details"),
                "success": entry.get("success", True),
                "error_message": entry.get("error_message"),
            }
        )
    return history


async def _log_agent_activity(
    issue_id: str,
    action: str,
    details: str,
    agent_role: AgentRole = AgentRole.VISION,
    success: bool = True,
):
    """Append an activity entry and persist it."""
    data = issues_db.get(issue_id)
    if data is None:
        return
    data.setdefault("activity_history", []).append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_role": agent_role.value if isinstance(agent_role, AgentRole) else str(agent_role),
            "action": action,
            "details": details,
            "success": success,
        }
    )
    _persist(issue_id)


# ---- API endpoints ----


@app.post("/issues/", response_model=IssueResponse)
async def create_issue(
    file: Optional[UploadFile] = File(None),
    issue_description: str = Form(""),
    developer_notes: str = Form(""),
    source_code: str = Form(""),
    background_tasks: BackgroundTasks = None,
):
    """Create an issue with (image + code) OR (issue description + code) OR (image + description)."""
    screenshot_b64 = ""
    mime_type = "image/png"

    if file and file.filename:
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        screenshot_bytes = await file.read()
        if len(screenshot_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="Screenshot must be under 10MB")
        if screenshot_bytes:
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            mime_type = file.content_type or "image/png"

    if not screenshot_b64 and not (issue_description and issue_description.strip()):
        raise HTTPException(
            status_code=400,
            detail="Please provide at least a screenshot or an issue description to begin analysis."
        )

    issue_id = str(uuid.uuid4())
    result = await run_pipeline(
        issue_id=issue_id,
        issue_description=issue_description,
        screenshot_base64=screenshot_b64,
        mime_type=mime_type,
        developer_notes=developer_notes,
        source_code=source_code or None,
    )

    vision, triage, findings = (
        result.vision_observations,
        result.triage_classification,
        result.investigation_findings,
    )
    if vision is not None:
        vision.issue_id = issue_id
    if triage is not None:
        triage.issue_id = issue_id
    if findings is not None:
        findings.issue_id = issue_id

    status = result.current_status

    issue = PydanticIssueBase(
        id=issue_id,
        description=issue_description or "(no description supplied)",
        screenshot_reference=f"screenshot-{issue_id}.png",
        original_description=issue_description,
        status=status,
        classification=(
            triage.classification if triage else IssueClassification.UNKNOWN
        ),
        severity=triage.severity if triage else SeverityLevel.MEDIUM,
    )

    issues_db[issue_id] = {
        "issue": issue,
        "vision_observations": vision,
        "triage_classification": triage,
        "investigation_findings": findings,
        "activity_history": _activity_from_messages(issue_id, result.messages),
        "messages": result.messages,
        "source_code_supplied": bool(source_code),
        "evidence_breakdown": result.evidence_breakdown,
    }
    _persist(issue_id)

    detail = (
        "Workflow completed."
        if not result.errors
        else "Workflow completed with agent errors: "
        + "; ".join(f"{e['agent']}: {e['error']}" for e in result.errors)
    )
    if not registry.model_configured():
        detail += " No GROQ_API_KEY configured, so agents used offline AST fallbacks."

    return IssueResponse(issue_id=issue_id, status=status.value, message=detail)


@app.get("/issues/", response_model=List[IssueDetailResponse])
async def list_issues():
    """List all issues, newest first."""
    result = []
    for data in issues_db.values():
        issue = data["issue"]
        result.append(
            IssueDetailResponse(
                issue_id=issue.id,
                description=issue.description,
                status=issue.status.value,
                classification=issue.classification.value if issue.classification else None,
                severity=issue.severity.value if issue.severity else None,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
            )
        )
    result.sort(key=lambda item: item.created_at, reverse=True)
    return result


@app.get("/issues/{issue_id}", response_model=IssueDetailResponse)
async def get_issue(issue_id: str):
    if issue_id not in issues_db:
        raise HTTPException(status_code=404, detail="Issue not found")
    issue = issues_db[issue_id]["issue"]
    return IssueDetailResponse(
        issue_id=issue.id,
        description=issue.description,
        status=issue.status.value,
        classification=issue.classification.value if issue.classification else None,
        severity=issue.severity.value if issue.severity else None,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@app.get("/issues/{issue_id}/messages")
async def get_issue_messages(issue_id: str):
    """The real agent-to-agent transcript for this issue's room."""
    data = issues_db.get(issue_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    messages = data.get("messages") or []
    counts: dict = {}
    for message in messages:
        counts[message["sender"]] = counts.get(message["sender"], 0) + 1
    return {
        "issue_id": issue_id,
        "messages": messages,
        "counts": counts,
        "source_code_supplied": data.get("source_code_supplied", False),
    }


@app.post("/issues/{issue_id}/investigate")
async def investigate_with_code(issue_id: str, request: InvestigationRequest):
    """Re-run the Investigation Agent with developer-supplied source code."""
    data = issues_db.get(issue_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not request.source_code.strip():
        raise HTTPException(status_code=400, detail="source_code must not be empty")

    issue = data["issue"]
    room = SwitchRoom(
        room_id=issue_id,
        messages=data.get("messages") or [],
        allowed_participants=PARTICIPANTS,
    )
    try:
        room.post(
            sender=TRIAGE,
            recipient=INVESTIGATION,
            kind=KIND_TASK,
            summary="Re-investigate with developer-supplied source code",
            content={
                "source_code_chars": len(request.source_code),
                "objective": (
                    data["triage_classification"].investigation_objective
                    if data.get("triage_classification")
                    else None
                ),
            },
            dedupe_key=f"{issue_id}:task:code:{len(data.get('messages') or [])}",
        )
    except Exception as exc:  # message cap / duplicate guard
        raise HTTPException(status_code=409, detail=f"Room rejected task: {exc}")

    try:
        findings = await registry.get_investigation_agent().investigate(
            issue_id=issue_id,
            issue_description=issue.description,
            vision_observations=data.get("vision_observations"),
            triage_classification=data.get("triage_classification"),
            source_code=request.source_code,
            repository_context=request.repository_context,
        )
    except Exception as exc:
        room.post(
            sender=INVESTIGATION,
            recipient="room",
            kind="error",
            summary="Investigation failed",
            content={"error": str(exc)},
            dedupe_key=f"{issue_id}:investigation:error:{len(room.messages)}",
        )
        data["messages"] = room.transcript()
        _persist(issue_id)
        raise HTTPException(status_code=500, detail=f"Investigation failed: {exc}")

    findings.issue_id = issue_id
    room.post(
        sender=INVESTIGATION,
        recipient=TRIAGE,
        kind=KIND_FINDINGS,
        summary=(findings.suspected_root_cause or findings.investigation_summary or "Findings updated")[:300],
        content=findings.model_dump(mode="json"),
        dedupe_key=f"{issue_id}:findings:code:{len(room.messages)}",
    )

    data["investigation_findings"] = findings
    data["source_code_supplied"] = True
    data["messages"] = room.transcript()
    data["activity_history"] = _activity_from_messages(issue_id, data["messages"])
    issue.status = IssueStatus.COMPLETED
    issue.updated_at = datetime.utcnow()
    _persist(issue_id)

    return {"status": "success", "findings": findings.model_dump(mode="json")}


@app.get("/stats")
async def get_stats():
    """Dashboard counters computed from live issues."""
    total = len(issues_db)
    open_investigations = 0
    critical = 0
    high = 0
    awaiting_attention = 0
    activity: List[dict] = []

    for issue_id, data in issues_db.items():
        issue = data["issue"]
        if issue.status != IssueStatus.COMPLETED:
            open_investigations += 1
        if issue.severity == SeverityLevel.CRITICAL:
            critical += 1
        if issue.severity == SeverityLevel.HIGH:
            high += 1
        if (
            issue.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
            and issue.status != IssueStatus.COMPLETED
        ):
            awaiting_attention += 1
        for entry in (data.get("activity_history") or [])[-3:]:
            activity.append({**entry, "issue_id": issue_id})

    activity.sort(key=lambda item: str(item.get("timestamp", "")), reverse=True)
    return {
        "total_issues": total,
        "open_investigations": open_investigations,
        "critical_issues": critical,
        "high_issues": high,
        "awaiting_attention": awaiting_attention,
        "recent_activity": activity[:10],
        "model_configured": registry.model_configured(),
        "database": DB_PATH,
    }


@app.post("/agents/vision/analyze")
async def analyze_screenshot(
    file: UploadFile = File(...),
    user_description: str = Form(""),
):
    """Run the Vision Agent on a screenshot only."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    screenshot_bytes = await file.read()
    if len(screenshot_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Screenshot must be under 10MB")

    try:
        observations = await registry.get_vision_agent().analyze_screenshot(
            screenshot_base64=base64.b64encode(screenshot_bytes).decode("utf-8"),
            mime_type=file.content_type or "image/png",
            user_description=user_description,
        )
        return {"status": "success", "observations": observations.model_dump(mode="json")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {exc}")


@app.post("/agents/triage/classify")
async def classify_issue(request: TriageClassificationRequest):
    """Run the Triage Agent on a description plus optional vision JSON."""
    try:
        vision_obs = None
        if request.vision_observations_json:
            vision_obs = PydanticVisionObservations.model_validate_json(
                request.vision_observations_json
            )
        triage_cls = await registry.get_triage_agent().triage_issue(
            issue_description=request.issue_description,
            vision_observations=vision_obs,
            developer_notes="",
        )
        return {"status": "success", "classification": triage_cls.model_dump(mode="json")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Triage classification failed: {exc}")


@app.post("/agents/investigate")
async def investigate_issue(issue_id: str, source_code: Optional[str] = None):
    """Run the Investigation Agent for an existing issue."""
    if issue_id not in issues_db:
        raise HTTPException(status_code=404, detail="Issue not found")

    data = issues_db[issue_id]
    try:
        findings = await registry.get_investigation_agent().investigate(
            issue_id=issue_id,
            issue_description=data["issue"].description,
            vision_observations=data.get("vision_observations"),
            triage_classification=data.get("triage_classification"),
            source_code=source_code,
            repository_context=None,
        )
        findings.issue_id = issue_id
        data["investigation_findings"] = findings
        data["issue"].status = IssueStatus.INVESTIGATING
        _persist(issue_id)
        return {"status": "success", "findings": findings.model_dump(mode="json")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {exc}")


@app.get("/reports/{issue_id}")
async def get_report(issue_id: str):
    """Final report: observations, classification, root cause, fix, evidence."""
    if issue_id not in issues_db:
        raise HTTPException(status_code=404, detail="Issue not found")

    data = issues_db[issue_id]
    issue = data["issue"]
    report = PydanticFinalReport(
        issue_id=issue.id,
        original_description=issue.description,
        screenshot_reference=issue.screenshot_reference,
        vision_observations=data.get("vision_observations"),
        triage_classification=data.get("triage_classification"),
        investigation_findings=data.get("investigation_findings"),
        status=issue.status,
        created_at=issue.created_at,
        agent_activity_history=_normalize_activity_history(
            data.get("activity_history", [])
        ),
        evidence_breakdown=data.get("evidence_breakdown") or {
            "OBSERVED": [],
            "INFERRED": [],
            "CODE_VERIFIED": [],
            "TEST_VERIFIED": [],
            "PROPOSED": [],
        },
    )
    return {"status": "success", "report": report.model_dump(mode="json")}
