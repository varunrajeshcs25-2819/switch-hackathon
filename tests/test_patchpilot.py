"""PatchPilot test suite.

Runs against the real FastAPI app, real agents (in honest no-key fallback mode)
and a temporary SQLite database, so nothing is mocked or pre-canned.
"""

import base64
import os
import tempfile

import pytest

TMP_DIR = tempfile.mkdtemp(prefix="patchpilot-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DIR}/test.db"
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from backend.api import main as api  # noqa: E402
from backend.database.serialization import deserialize_issue, serialize_issue  # noqa: E402
from backend.database.store import IssueStore  # noqa: E402
from backend.integrations.switch.room import (  # noqa: E402
    KIND_OBSERVATION,
    KIND_TASK,
    SwitchRoom,
    SwitchRoomError,
)
from backend.models import (  # noqa: E402
    PydanticInvestigationFindings,
    PydanticIssueBase,
    PydanticTriageClassification,
    PydanticVisionObservations,
)

client = TestClient(api.app)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _create_issue(description="Checkout button shows HTTP 500 error", source_code=""):
    response = client.post(
        "/issues/",
        files={"file": ("bug.png", PNG_BYTES, "image/png")},
        data={"issue_description": description, "source_code": source_code},
    )
    assert response.status_code == 200, response.text
    return response.json()["issue_id"]


# --------------------------------------------------------------- Switch room


def test_room_enforces_identity_and_ordering():
    room = SwitchRoom("room-1", allowed_participants={"vision", "triage"})
    message = room.post(
        "vision", "triage", KIND_OBSERVATION, "found a 500", {"errors": ["500"]}
    )
    assert room.messages[0].message_id == message.message_id
    assert room.messages[0].recipient == "triage"
    assert room.for_agent("triage")[0].sender == "vision"


def test_room_rejects_self_talk_duplicates_and_unknown_participants():
    room = SwitchRoom("room-2", allowed_participants={"vision", "triage"})
    room.post("vision", "triage", KIND_TASK, "task", dedupe_key="k1")

    with pytest.raises(SwitchRoomError):
        room.post("triage", "triage", KIND_TASK, "self")
    with pytest.raises(SwitchRoomError):
        room.post("vision", "triage", KIND_TASK, "dup", dedupe_key="k1")
    with pytest.raises(SwitchRoomError):
        room.post("vision", "ghost", KIND_TASK, "unknown")


def test_room_message_cap_prevents_infinite_loops():
    room = SwitchRoom("room-3", max_messages=2)
    room.post("vision", "triage", KIND_TASK, "one")
    room.post("triage", "investigation", KIND_TASK, "two")
    with pytest.raises(SwitchRoomError):
        room.post("investigation", "triage", KIND_TASK, "three")


def test_room_serialization_round_trip():
    room = SwitchRoom("room-4")
    room.post("vision", "triage", KIND_OBSERVATION, "hello")
    restored = SwitchRoom.from_dict(room.to_dict())
    assert len(restored.messages) == 1
    assert restored.messages[0].summary == "hello"


# ------------------------------------------------------------ persistence


def test_store_persists_and_reloads_issue():
    store = IssueStore(f"{TMP_DIR}/store.db")
    issue = PydanticIssueBase(id="abc", description="broken checkout")
    payload = serialize_issue(
        {
            "issue": issue,
            "vision_observations": PydanticVisionObservations(
                error_messages=["HTTP 500"], confidence="high"
            ),
            "triage_classification": PydanticTriageClassification(
                classification="backend_error", severity="critical"
            ),
            "investigation_findings": PydanticInvestigationFindings(
                suspected_root_cause="unhandled exception"
            ),
            "activity_history": [],
            "messages": [{"sender": "vision", "kind": "observation"}],
        }
    )
    store.save("abc", payload)
    assert store.count() == 1

    reloaded = IssueStore(f"{TMP_DIR}/store.db").load_all()
    data = deserialize_issue(reloaded["abc"])
    assert data["issue"].id == "abc"
    assert data["vision_observations"].error_messages == ["HTTP 500"]
    # Enum fields use use_enum_values, so they deserialize to plain strings.
    assert data["triage_classification"].severity == "critical"
    assert data["investigation_findings"].suspected_root_cause == "unhandled exception"
    assert data["messages"][0]["sender"] == "vision"


# --------------------------------------------------------------- API tests


def test_upload_rejects_non_image():
    response = client.post(
        "/issues/",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"issue_description": "nope"},
    )
    assert response.status_code == 400


def test_create_issue_runs_all_three_agents_and_records_room():
    issue_id = _create_issue()

    detail = client.get(f"/issues/{issue_id}")
    assert detail.status_code == 200
    assert detail.json()["issue_id"] == issue_id

    messages = client.get(f"/issues/{issue_id}/messages").json()
    senders = {m["sender"] for m in messages["messages"]}
    kinds = {m["kind"] for m in messages["messages"]}
    assert {"vision", "triage", "investigation"} <= senders
    assert {"observation", "classification", "task", "findings"} <= kinds
    # No API key in CI: the fallback must be honest about low confidence.
    assert "verdict" in kinds or "error" in kinds


def test_report_contains_real_agent_output():
    issue_id = _create_issue("Registration form returns 500 on submit")
    report = client.get(f"/reports/{issue_id}").json()["report"]

    assert report["issue_id"] == issue_id
    assert report["vision_observations"]["confidence"] in {
        "uncertain",
        "low",
        "medium",
        "high",
    }
    assert report["triage_classification"]["classification"]
    assert isinstance(report["agent_activity_history"], list)


def test_create_issue_persists_description_and_source_code():
    """Multipart form fields must actually reach the agents (regression guard)."""
    description = "Registration form returns 500 after submit"
    issue_id = _create_issue(description, source_code="def register():\n    return 1 / 0\n")

    report = client.get(f"/reports/{issue_id}").json()["report"]
    assert report["original_description"] == description

    messages = client.get(f"/issues/{issue_id}/messages").json()
    assert messages["source_code_supplied"] is True
    triage_msg = next(m for m in messages["messages"] if m["kind"] == "classification")
    assert "Triage Agent for PatchPilot" not in triage_msg["summary"]


class _Finding:
    """Minimal stand-in used to exercise the verdict rules directly."""

    def __init__(self, root_cause, fix=None, confidence="low"):
        self.suspected_root_cause = root_cause
        self.proposed_fix = fix
        self.confidence = confidence
        self.relevant_source_files = []
        self.challenges_previous_findings = []


class _Triage:
    def __init__(self, objective="Identify the root cause"):
        self.investigation_objective = objective
        self.classification = "backend_error"
        self.severity = "critical"


def test_verdict_does_not_accept_placeholder_root_cause():
    from backend.services.workflow import _evaluate

    verdict = _evaluate(_Triage(), _Finding("Unable to determine root cause"), None)
    assert verdict["addressed"] is False
    assert "root cause" in verdict["missing"]

    good = _evaluate(_Triage(), _Finding("ZeroDivisionError in register()", "guard"), "code")
    assert good["addressed"] is True


def test_stats_reflects_created_issues():
    _create_issue("Dashboard stats smoke test")
    stats = client.get("/stats").json()
    assert stats["total_issues"] >= 1
    assert "critical_issues" in stats
    assert stats["model_configured"] in (True, False)
    assert isinstance(stats["recent_activity"], list)


def test_investigate_with_source_code_updates_findings():
    issue_id = _create_issue("Registration returns 500")
    before = client.get(f"/issues/{issue_id}/messages").json()["messages"]

    response = client.post(
        f"/issues/{issue_id}/investigate",
        json={
            "source_code": "@app.post('/register')\ndef register():\n"
            "    return 1 / 0\n",
            "repository_context": "Flask demo app",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["findings"]["issue_id"] == issue_id

    after = client.get(f"/issues/{issue_id}/messages").json()["messages"]
    assert len(after) > len(before)
    assert any(m["kind"] == "task" for m in after[-2:])
    assert client.get(f"/issues/{issue_id}/messages").json()["source_code_supplied"] is True


def test_messages_404_for_unknown_issue():
    assert client.get("/issues/does-not-exist/messages").status_code == 404
    assert client.get("/reports/does-not-exist").status_code == 404


def test_issue_models_allow_missing_issue_id():
    assert PydanticVisionObservations(error_messages=["x"]).issue_id is None
    assert (
        PydanticTriageClassification(
            classification="backend_error", severity="high"
        ).issue_id
        is None
    )
    assert PydanticInvestigationFindings(suspected_root_cause="y").issue_id is None
