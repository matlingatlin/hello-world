"""The conversation gate 1 runs on.

Messages carry ids because provenance does: every extracted value points back at
the message it came from, which is what makes the spec gate's "you said this"
true rather than decorative — and what lets the extractor be caught inventing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntakeMessage(BaseModel):
    """One turn of the wizard conversation."""

    id: str = ""
    role: str = "user"  # "user" | "assistant"
    text: str = ""

    @property
    def is_user(self) -> bool:
        return self.role == "user"


def with_ids(messages: list[IntakeMessage]) -> list[IntakeMessage]:
    """Give every message a stable id (m1, m2, ...) without disturbing supplied ones.

    Ids are positional so a caller that never sets them still gets provenance
    that survives a round trip through the API.
    """
    out: list[IntakeMessage] = []
    for index, message in enumerate(messages, start=1):
        out.append(message if message.id else message.model_copy(update={"id": f"m{index}"}))
    return out


def user_message_ids(messages: list[IntakeMessage]) -> set[str]:
    """The ids extraction may cite as evidence.

    Only the user's own turns count: a value 'sourced' from our own question is
    the model quoting itself, which is exactly the invention we refuse.
    """
    return {m.id for m in messages if m.is_user and m.text.strip()}


def transcript(messages: list[IntakeMessage]) -> str:
    speakers = {"user": "USER", "assistant": "SCIO"}
    return "\n".join(
        f"[{m.id}] {speakers.get(m.role, m.role.upper())}: {m.text}" for m in messages
    )


def latest_user_text(messages: list[IntakeMessage]) -> str:
    return next((m.text for m in reversed(messages) if m.is_user), "")


class Conversation(BaseModel):
    """Messages plus the derived bits every step needs."""

    messages: list[IntakeMessage] = Field(default_factory=list)

    @classmethod
    def of(cls, messages: list[IntakeMessage]) -> Conversation:
        return cls(messages=with_ids(messages))

    @property
    def evidence_ids(self) -> set[str]:
        return user_message_ids(self.messages)

    def as_prompt(self) -> str:
        return transcript(self.messages)
