
"""Switch-style agent room.

Transport-agnostic room for coordinating agents through structured messages.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field


# Message kinds
KIND_OBSERVATION = "observation"
KIND_OBSERVATIONS = "observations"
KIND_CLASSIFICATION = "classification"
KIND_TASK = "task"
KIND_FINDINGS = "findings"
KIND_CHALLENGE = "challenge"
KIND_VERDICT = "verdict"
KIND_ERROR = "error"
KIND_SYSTEM = "system"

VALID_KINDS = {
    KIND_OBSERVATION,
    KIND_OBSERVATIONS,
    KIND_CLASSIFICATION,
    KIND_TASK,
    KIND_FINDINGS,
    KIND_CHALLENGE,
    KIND_VERDICT,
    KIND_ERROR,
    KIND_SYSTEM,
}

ROOM = "room"


# Exceptions
class SwitchRoomError(RuntimeError):
    """Raised when a room invariant is violated."""


class DuplicateMessageError(SwitchRoomError):
    """Raised when a duplicate message is detected."""


class RoomLimitError(SwitchRoomError):
    """Raised when the room reaches its message limit."""


class UnknownParticipantError(SwitchRoomError):
    """Raised when an unknown participant tries to communicate."""


# Message model
class AgentMessage(BaseModel):
    """A single message in a Switch room."""

    message_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12]
    )
    room_id: str
    seq: int = 0
    sender: str
    recipient: str
    kind: str
    summary: str
    content: Dict[str, Any] = Field(default_factory=dict)
    reply_to: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __getitem__(self, key):
        """Allow dictionary-style access for compatibility."""
        return self.model_dump(mode="python")[key]


# Switch Room
class SwitchRoom:
    """Ordered, guard-railed conversation between agents."""

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
            set(allowed_participants)
            if allowed_participants
            else None
        )

        self._messages: List[AgentMessage] = []

        for index, message in enumerate(messages or [], start=1):
            message_data = dict(message)
            message_data.setdefault("seq", index)
            self._messages.append(
                AgentMessage.model_validate(message_data)
            )

        self._dedupe_keys: set[str] = set()

    # ---------------------------------------------------------
    # Core message publishing
    # ---------------------------------------------------------

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

        if kind not in VALID_KINDS:
            raise SwitchRoomError(
                f"unknown message kind: {kind!r}"
            )

        if sender == recipient:
            raise SwitchRoomError(
                "an agent cannot address itself"
            )

        if self.allowed_participants is not None:
            for who in (sender, recipient):
                if (
                    who != ROOM
                    and who not in self.allowed_participants
                ):
                    raise UnknownParticipantError(
                        f"unknown participant: {who!r}"
                    )

        if len(self._messages) >= self.max_messages:
            raise RoomLimitError(
                f"room {self.room_id} reached its message cap "
                f"({self.max_messages}); possible agent loop"
            )

        if dedupe_key is not None:
            if dedupe_key in self._dedupe_keys:
                raise DuplicateMessageError(
                    f"duplicate message suppressed: {dedupe_key}"
                )

        message = AgentMessage(
            room_id=self.room_id,
            seq=len(self._messages) + 1,
            sender=sender,
            recipient=recipient,
            kind=kind,
            summary=summary,
            content=content or {},
            reply_to=reply_to,
        )

        self._deliver(message)

        if dedupe_key is not None:
            self._dedupe_keys.add(dedupe_key)

        return message

    def _deliver(self, message: AgentMessage) -> None:
        """Store message in the ordered room transcript."""
        self._messages.append(message)

    # ---------------------------------------------------------
    # Accessors
    # ---------------------------------------------------------

    @property
    def messages(self) -> List[AgentMessage]:
        return list(self._messages)

    def transcript(self) -> List[Dict[str, Any]]:
        return [
            message.model_dump(mode="json")
            for message in self._messages
        ]

    def last_from(self, sender: str) -> Optional[AgentMessage]:
        for message in reversed(self._messages):
            if message.sender == sender:
                return message
        return None

    def for_agent(self, agent: str) -> List[AgentMessage]:
        """Return messages addressed to an agent or broadcast."""
        return [
            message
            for message in self._messages
            if message.recipient in (agent, ROOM)
        ]

    def summary_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}

        for message in self._messages:
            counts[message.sender] = (
                counts.get(message.sender, 0) + 1
            )

        return counts

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

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
