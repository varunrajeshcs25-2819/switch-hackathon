"""Switch-style agent room.

IMPORTANT / HONESTY NOTE
------------------------
The official Switch agent SDK is *not* available in this environment: no
`switch` distribution is installed in site-packages, and no Switch
documentation/endpoints are reachable from this sandbox. Inventing
undocumented endpoints would be worse than not having them, so this module
implements the closest supported alternative with the same protocol
semantics as a Switch room:

  * participants with unique identities (agent names)
  * explicit addressing (sender -> recipient)
  * an ordered, persisted transcript per issue room
  * structured message kinds (observation / classification / task / findings /
    challenge / verdict / error)
  * guards against runaway conversations (message cap + duplicate suppression)
  * full traceability (ids, timestamps, reply_to links)

Swapping in the real Switch transport later only requires replacing
`SwitchRoom._deliver` with the SDK's publish call: the message contract,
persistence and REST surface stay identical.

This module is intentionally transport-agnostic and has no model or network
dependency, so it can be unit tested in isolation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

# Message kinds understood by the room.
KIND_OBSERVATION = "observation"
KIND_CLASSIFICATION = "classification"
KIND_TASK = "task"
KIND_FINDINGS = "findings"
KIND_CHALLENGE = "challenge"
KIND_VERDICT = "verdict"
KIND_ERROR = "error"
KIND_SYSTEM = "system"

VALID_KINDS = {
    KIND_OBSERVATION,
    KIND_CLASSIFICATION,
    KIND_TASK,
    KIND_FINDINGS,
    KIND_CHALLENGE,
    KIND_VERDICT,
    KIND_ERROR,
    KIND_SYSTEM,
}

ROOM = "room"  # broadcast recipient


class AgentMessage(BaseModel):
    """A single message in a Switch room."""

    message_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    room_id: str
    sender: str
    recipient: str
    kind: str
    summary: str
    content: Dict[str, Any] = Field(default_factory=dict)
    reply_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SwitchRoomError(RuntimeError):
    """Raised when a room invariant is violated."""


class SwitchRoom:
    """Ordered, persisted, guard-railed conversation between agents."""

    def __init__(
        self,
        room_id: str,
        messages: Optional[Iterable[Dict[str, Any]]] = None,
        max_messages: int = 40,
        allowed_participants: Optional[Iterable[str]] = None,
    ) -> None:
        self.room_id = room_id
        self.max_messages = max_messages
        self.allowed_participants = (
            set(allowed_participants) if allowed_participants else None
        )
        self._messages: List[AgentMessage] = [
            AgentMessage.model_validate(m) for m in (messages or [])
        ]
        self._dedupe_keys: set[str] = set()

    # ------------------------------------------------------------------ core
    def post(
        self,
        sender: str,
        recipient: str,
        kind: str,
        summary: str,
        content: Optional[Dict[str, Any]] = None,
        reply_to: Optional[str] = None,
        dedupe_key: Optional[str] = None,
    ) -> AgentMessage:
        """Publish a message. Returns the stored message.

        Enforces: valid kind, no self-addressing, known participants, duplicate
        suppression, and a hard message cap so a bug cannot create an infinite
        agent ping-pong.
        """
        if kind not in VALID_KINDS:
            raise SwitchRoomError(f"unknown message kind: {kind!r}")
        if sender == recipient:
            raise SwitchRoomError("an agent cannot address itself")
        if self.allowed_participants is not None:
            for who in (sender, recipient):
                if who != ROOM and who not in self.allowed_participants:
                    raise SwitchRoomError(f"unknown participant: {who!r}")
        if len(self._messages) >= self.max_messages:
            raise SwitchRoomError(
                f"room {self.room_id} reached its message cap "
                f"({self.max_messages}); possible agent loop"
            )
        if dedupe_key is not None:
            if dedupe_key in self._dedupe_keys:
                raise SwitchRoomError(f"duplicate message suppressed: {dedupe_key}")
            self._dedupe_keys.add(dedupe_key)

        message = AgentMessage(
            room_id=self.room_id,
            sender=sender,
            recipient=recipient,
            kind=kind,
            summary=summary,
            content=content or {},
            reply_to=reply_to,
        )
        self._deliver(message)
        return message

    def _deliver(self, message: AgentMessage) -> None:
        """Hand the message to the transport.

        Local implementation: append to the in-memory ordered transcript.
        Replace this method with a Switch SDK publish when available.
        """
        self._messages.append(message)

    # -------------------------------------------------------------- accessors
    @property
    def messages(self) -> List[AgentMessage]:
        return list(self._messages)

    def transcript(self) -> List[Dict[str, Any]]:
        return [m.model_dump(mode="json") for m in self._messages]

    def last_from(self, sender: str) -> Optional[AgentMessage]:
        for message in reversed(self._messages):
            if message.sender == sender:
                return message
        return None

    def for_agent(self, agent: str) -> List[AgentMessage]:
        """Messages addressed to an agent (plus broadcasts)."""
        return [m for m in self._messages if m.recipient in (agent, ROOM)]

    def summary_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for message in self._messages:
            counts[message.sender] = counts.get(message.sender, 0) + 1
        return counts

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "max_messages": self.max_messages,
            "messages": self.transcript(),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SwitchRoom":
        return cls(
            room_id=payload.get("room_id", "room"),
            messages=payload.get("messages", []),
            max_messages=payload.get("max_messages", 40),
        )
