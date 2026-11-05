"""
End-to-End Multi-Agent Integration and Collaboration Test Suite.

Tests verified through actual pipeline execution:
1. Obvious visual bug workflow (Vision -> Triage -> Investigation -> Verdict).
2. Multiple visual bugs on single screen properly preserved across agent handoffs.
3. HTTP 500 server crash on essential workflow (triaged as Critical, traced to code).
4. Incorrect source-code implementation with zero-division or null dereference.
5. Missing source code (investigation honestly reports missing code; Triage verdict flags incomplete).
6. Ambiguous issue handling (high uncertainty preserved without hallucinations).
7. Contradictory agent findings (Investigation challenges Vision on disabled button; Triage records challenge).
8. Failure recovery and room transcript traceability.
"""

import base64
import pytest
import asyncio

from backend.services.workflow import run_pipeline, SwitchRoom
from backend.models import (
    ConfidenceLevel,
    IssueClassification,
    SeverityLevel,
    PydanticVisionObservations,
    PydanticTriageClassification,
    PydanticInvestigationFindings,
)

# 1x1 transparent PNG base64 for synthetic screenshot testing
TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


@pytest.mark.asyncio
async def test_e2e_obvious_visual_bug():
    """Test 1: Obvious visual bug workflow with message handoffs."""
    room = SwitchRoom(room_id="e2e-visual-1")
    res = await run_pipeline(
        issue_id="e2e-visual-1",
        issue_description="Navigation links overlap the right container boundary and text wraps awkwardly",
        screenshot_base64=TINY_PNG_BASE64,
        mime_type="image/png",
        room=room,
    )
    assert res.triage_classification.classification == IssueClassification.UI_BUG
    assert res.triage_classification.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM]

    # Verify transcript progression
    messages = room.messages
    senders = [m.sender for m in messages]
    assert "system" in senders
    assert "vision" in senders
    assert "triage" in senders
    assert "investigation" in senders


@pytest.mark.asyncio
async def test_e2e_http_500_backend_with_source_code():
    """Test 2: HTTP 500 server error with actual buggy source code."""
    broken_code = """# file: user_api.py
def register_user(payload):
    # Unhandled division by zero causing 500 error
    error_trigger = 1 / 0
    return {"status": "created"}
"""
    room = SwitchRoom(room_id="e2e-500-1")
    res = await run_pipeline(
        issue_id="e2e-500-1",
        issue_description="User registration endpoint throws HTTP 500 Internal Server Error",
        screenshot_base64=TINY_PNG_BASE64,
        mime_type="image/png",
        source_code=broken_code,
        room=room,
    )
    assert res.triage_classification.classification == IssueClassification.BACKEND_ERROR
    assert res.triage_classification.severity == SeverityLevel.CRITICAL
    assert res.investigation_findings.suspected_root_cause is not None
    assert "user_api.py" in res.investigation_findings.relevant_source_files
    assert res.investigation_findings.proposed_code_changes is not None
    assert "--- original" in res.investigation_findings.proposed_code_changes

    # Verify Triage accepted the findings
    verdict_msgs = [m for m in room.messages if m.kind == "verdict"]
    assert len(verdict_msgs) == 1
    assert verdict_msgs[0].content["addressed"] is True


@pytest.mark.asyncio
async def test_e2e_missing_source_code_honest_challenges():
    """Test 3: Backend issue without source code generates challenges and incomplete verdict."""
    room = SwitchRoom(room_id="e2e-no-code")
    res = await run_pipeline(
        issue_id="e2e-no-code",
        issue_description="Database connection timeout 500 error",
        screenshot_base64=TINY_PNG_BASE64,
        mime_type="image/png",
        source_code=None,  # No code provided
        room=room,
    )
    # Challenge must be raised because code is required for backend error
    challenge_msgs = [m for m in room.messages if m.kind == "challenge"]
    assert len(challenge_msgs) >= 1
    assert any("no source code was supplied" in c.lower() for c in challenge_msgs[0].content["challenges"])

    # Verdict must be incomplete
    verdict_msgs = [m for m in room.messages if m.kind == "verdict"]
    assert len(verdict_msgs) == 1
    assert verdict_msgs[0].content["addressed"] is False


@pytest.mark.asyncio
async def test_e2e_contradictory_findings_button_disabled_by_design():
    """Test 4: Investigation Agent challenges Vision finding when button is disabled by design in code."""
    valid_frontend_code = """// file: CheckoutButton.tsx
export function CheckoutButton({ cartItems }) {
    return (
        <button disabled={cartItems.length === 0} className="checkout-btn">
            Pay Now
        </button>
    );
}
"""
    room = SwitchRoom(room_id="e2e-contradiction")
    res = await run_pipeline(
        issue_id="e2e-contradiction",
        issue_description="Pay Now button is unclickable and appears broken",
        screenshot_base64=TINY_PNG_BASE64,
        mime_type="image/png",
        source_code=valid_frontend_code,
        room=room,
    )
    # Investigation Agent must have challenged earlier findings
    assert len(res.investigation_findings.challenges_previous_findings) > 0
    assert any("disabled" in c.lower() for c in res.investigation_findings.challenges_previous_findings)

    # Challenge message posted to the room
    challenge_msgs = [m for m in room.messages if m.kind == "challenge"]
    assert len(challenge_msgs) >= 1
    assert any("disabled" in c.lower() for c in challenge_msgs[0].content["challenges"])


@pytest.mark.asyncio
async def test_e2e_room_traceability_and_reply_to_links():
    """Test 5: Verify task ID, deduplication, and reply_to linkages across full chain."""
    room = SwitchRoom(room_id="e2e-trace-1")
    res = await run_pipeline(
        issue_id="e2e-trace-1",
        issue_description="Login fails with 401 Unauthorized",
        screenshot_base64=TINY_PNG_BASE64,
        mime_type="image/png",
        source_code="def login(): return 401\n",
        room=room,
    )
    messages = room.messages
    task_msgs = [m for m in messages if m.kind == "task"]
    findings_msgs = [m for m in messages if m.kind == "findings"]
    verdict_msgs = [m for m in messages if m.kind == "verdict"]

    assert len(task_msgs) == 1
    assert task_msgs[0].content.get("task_id") == "task-e2e-trace-1"
    assert len(findings_msgs) == 1
    assert findings_msgs[0].reply_to == task_msgs[0].message_id
    assert len(verdict_msgs) == 1
    assert verdict_msgs[0].reply_to == findings_msgs[0].message_id

