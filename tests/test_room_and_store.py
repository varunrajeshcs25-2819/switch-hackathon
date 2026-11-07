import pytest

from backend.database.store import IssueStore
from backend.integrations.switch.room import (
    DuplicateMessageError,
    RoomLimitError,
    SwitchRoom,
    UnknownParticipantError,
)


def make_room(**kw):
    return SwitchRoom("r1", allowed_participants=("system", "vision", "triage"), **kw)


def test_post_and_transcript_are_independent_copies():
    room = make_room()
    room.post("system", "vision", "task", "go", {"a": 1}, dedupe_key="k1")
    snap = room.transcript()
    snap[0]["content"]["a"] = 99
    assert room.messages[0]["content"]["a"] == 1
    assert room.messages[0]["seq"] == 1


def test_duplicate_unknown_and_cap_are_rejected():
    room = make_room(max_messages=2)
    room.post("system", "vision", "task", "go", dedupe_key="k1")
    with pytest.raises(DuplicateMessageError):
        room.post("system", "vision", "task", "go", dedupe_key="k1")
    with pytest.raises(UnknownParticipantError):
        room.post("hacker", "vision", "task", "x")
    room.post("vision", "triage", "observations", "ok")
    with pytest.raises(RoomLimitError):
        room.post("triage", "vision", "task", "too many")


def test_store_roundtrip_and_upsert(tmp_path):
    store = IssueStore(str(tmp_path / "t.db"))
    store.save("a", {"x": 1})
    store.save("a", {"x": 2})
    store.save("b", {"y": [1, 2]})
    assert store.load_all() == {"a": {"x": 2}, "b": {"y": [1, 2]}}
    assert IssueStore(str(tmp_path / "t.db")).load("a") == {"x": 2}  # survives restart
