"""Markings that argue with the approved spec.

The spec is what the user signed off at gate 1. A note in the design window that
contradicts it is not an error and not an instruction — it is a *question*, and
the honest thing is to ask it.

Building it anyway would quietly overwrite a decision the user made deliberately
("no payments for now") on the strength of a sentence typed into a side panel.
Refusing outright would be worse: they may well have changed their mind. So a
conflict comes back as "you told me X, this asks for Y — which is it?", the
change is not applied, and the user decides.

Detection is deterministic and narrow on purpose. It reads the architecture the
spec produced — the non-goals it excluded, the security posture it derived, the
entities it owns — and matches on the user's own canonical vocabulary. It never
asks a model whether something is a contradiction, because a model that is
merely *usually* right here would sometimes block a legitimate change and
sometimes wave through the one thing the user asked us not to do.

What it deliberately does NOT try to catch: anything requiring judgment. A note
that quietly widens scope, or that is a bad idea, is not this function's
business — the build's own gates and the reveal's honest status carry that.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from ..layerb.architecture import Architecture, AuthMode
from ..layerb.vocabulary import canonical_name
from .markings import ChangeBatch, Marking

# Words that mean "make this happen", as opposed to describing something.
_WANTS = re.compile(
    r"\b(add|include|introduce|support|enable|build|put|make|let|allow|want|need"
    r"|should have|också|lägg till)\b",
    re.IGNORECASE,
)
_REMOVES = re.compile(
    r"\b(remove|delete|drop|get rid of|take out|without|no more|disable|turn off|ta bort)\b",
    re.IGNORECASE,
)

# The security decisions the spec derives rather than asks about (ADR-0001).
# Undoing one from the design window is exactly the kind of thing that must be
# a question — it is the product's wedge, and it is invisible on a screenshot.
_AUTH_WORDS = re.compile(
    r"\b(sign[- ]?in|login|log[- ]?in|auth|authentication|account|password|inloggning)\b",
    re.IGNORECASE,
)
_ACCESS_WORDS = re.compile(
    r"\b(public|anyone|everyone|open to all|no restrictions|alla|öppen)\b", re.IGNORECASE
)


class Conflict(BaseModel):
    """One contradiction between a marking and the approved spec."""

    kind: str  # "non_goal" | "auth" | "access"
    scio_id: str = ""
    note: str
    spec_says: str
    question: str

    def as_line(self) -> str:
        return f"{self.question} (you said: {self.spec_says})"


def _mentions(text: str, term: str) -> bool:
    """Whether a note is about this concept, in the project's own vocabulary.

    Canonicalised both sides, so "reservations" in a non-goal matches "booking"
    in a note — Layer B already collapsed those to one name, and a conflict
    check that only matched the literal string would miss the common case.
    """
    if not term.strip():
        return False
    words = {canonical_name(word) for word in re.findall(r"[A-Za-zÅÄÖåäö]+", text)}
    canonical = canonical_name(term)
    if canonical and canonical in words:
        return True
    # Multi-word non-goals ("mobile app", "no payments yet") match on any of
    # their own content words, canonicalised the same way.
    parts = [canonical_name(p) for p in re.findall(r"[A-Za-zÅÄÖåäö]{3,}", term)]
    meaningful = [p for p in parts if p and p not in _STOPWORDS]
    return bool(meaningful) and any(p in words for p in meaningful)


_STOPWORDS = {
    "no", "not", "for", "now", "yet", "the", "and", "any", "with", "without",
    "inga", "ingen", "inte", "just", "nu",
}


def _non_goal_conflicts(batch: ChangeBatch, arch: Architecture) -> list[Conflict]:
    """A note asking for something the spec deliberately left out."""
    found: list[Conflict] = []
    for marking, note in _notes(batch):
        if not _WANTS.search(note):
            continue
        for excluded in arch.scope_guard:
            if _mentions(note, excluded):
                found.append(
                    Conflict(
                        kind="non_goal",
                        scio_id=marking.scio_id or "",
                        note=note,
                        spec_says=excluded,
                        question=(
                            f"This asks to add something you deliberately left out: “{excluded}”. "
                            "Do you want it after all, or should I leave it out?"
                        ),
                    )
                )
                break
    return found


def _auth_conflicts(batch: ChangeBatch, arch: Architecture) -> list[Conflict]:
    """A note asking to take away sign-in the spec says the app needs."""
    if arch.auth_access.mode is AuthMode.none:
        return []
    found: list[Conflict] = []
    for marking, note in _notes(batch):
        if _REMOVES.search(note) and _AUTH_WORDS.search(note):
            found.append(
                Conflict(
                    kind="auth",
                    scio_id=marking.scio_id or "",
                    note=note,
                    spec_says=(
                        "sign-in via "
                        f"{arch.auth_access.provider or arch.auth_access.mode.value}"
                    ),
                    question=(
                        "This asks to remove sign-in, which the spec says this app needs — "
                        "without it the app cannot tell your users apart. Remove it anyway?"
                    ),
                )
            )
    return found


def _access_conflicts(batch: ChangeBatch, arch: Architecture) -> list[Conflict]:
    """A note asking to make sensitive data public."""
    posture = arch.security_posture
    if not (posture.sensitive or posture.row_level_security):
        return []
    found: list[Conflict] = []
    for marking, note in _notes(batch):
        if _ACCESS_WORDS.search(note) and (_WANTS.search(note) or _REMOVES.search(note)):
            kinds = ", ".join(posture.sensitive_kinds) or "personal"
            found.append(
                Conflict(
                    kind="access",
                    scio_id=marking.scio_id or "",
                    note=note,
                    spec_says=f"{kinds} data, with row-level security on",
                    question=(
                        "This asks to open up data the spec marked as sensitive. That would let "
                        "anyone read it. Is that really what you want?"
                    ),
                )
            )
    return found


def _notes(batch: ChangeBatch) -> list[tuple[Marking, str]]:
    """Every piece of text the user wrote, with the marking it belongs to.

    The batch-wide prompt counts too: "make it all public" typed into the box is
    the same request as writing it on one element.
    """
    pairs = [(m, m.note) for m in batch.markings if m.note.strip()]
    if batch.prompt.strip():
        pairs.append((Marking(), batch.prompt))
    return pairs


def detect_conflicts(batch: ChangeBatch, arch: Architecture) -> list[Conflict]:
    """Everything in this batch that argues with the spec. Empty means build it."""
    return [
        *_non_goal_conflicts(batch, arch),
        *_auth_conflicts(batch, arch),
        *_access_conflicts(batch, arch),
    ]
