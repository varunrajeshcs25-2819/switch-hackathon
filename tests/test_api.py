"""End-to-end API test. Runs with no GEMINI_API_KEY, so it exercises the honest fallbacks."""

import os
import tempfile

os.environ.pop("GEMINI_API_KEY", None)
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

client = TestClient(app)
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create(description="Checkout button crashes with a 500 error"):
    return client.post(
        "/issues/",
        files={"file": ("shot.png", PNG, "image/png")},
        data={"issue_description": description},
    )


def test_rejects_non_image():
    r = client.post("/issues/", files={"file": ("a.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_full_workflow_and_report():
    r = _create()
    assert r.status_code == 200
    issue_id = r.json()["issue_id"]

    msgs = client.get(f"/issues/{issue_id}/messages").json()
    assert [m["sender"] for m in msgs["messages"]][:2] == ["system", "vision"]
    assert msgs["counts"]["investigation"] >= 1

    issue = client.get(f"/issues/{issue_id}").json()
    assert issue["classification"] == "functional_bug"

    report = client.get(f"/reports/{issue_id}").json()["report"]
    assert report["issue_id"] == issue_id
    assert len(report["agent_activity_history"]) >= 3


def test_investigate_requires_source_and_404s():
    issue_id = _create().json()["issue_id"]
    assert client.post(f"/issues/{issue_id}/investigate", json={"source_code": "  "}).status_code == 400
    assert client.post("/issues/nope/investigate", json={"source_code": "x"}).status_code == 404


def test_stats_and_listing():
    _create()
    stats = client.get("/stats").json()
    assert stats["total_issues"] >= 1 and stats["model_configured"] is False
    assert len(client.get("/issues/").json()) >= 1
