"""Gate 1 without a model — so the free path can actually finish.

The first local click-through found this: on fake providers the wizard asked
"What does the app do?", the person answered, and it asked again. Forever. The
FakeProvider returns a digest, extraction cannot parse a digest, nothing is ever
recorded, and the gate never opens — so nobody without an API key could reach
the review screen, let alone a build. The builder already had a stand-in for
exactly this reason (builder/standin.py); intake did not.

What it does is deliberately modest, and it is *not* pretending to understand:
it files the answer under the question that was asked. Scio asks about
`key_actions`; whatever the person types next becomes `key_actions`, cited to
the message they typed it in. That is the same contract the guide's canned
questions already imply — one question, one field — and it produces a spec whose
provenance is true, because the value really did come from that message.

Two properties keep it honest:

- **It never invents.** Every value is the person's own words, and every value
  cites a real user message. A turn with nothing in it records nothing.
- **It is visibly a stand-in.** `source` is "stated" because the person did
  state it, but the reveal still marks the whole build as stand-in output, and
  the whole at the spec gate is the deterministic one (registry.is_fake).

A real model reads a paragraph and fills six fields at once. This fills one per
turn. That is a worse spec, not a fake one — and it is the difference between a
product a person can try for free and a product nobody can open.
"""

from __future__ import annotations

import json
import re

from ..execution.provider import (
    Completion,
    Message,
    ModelProvider,
    ProviderRegistry,
    Vendor,
)
from .fields import EXTRACTABLE_FIELDS, guide_for
from .schema import CONDITIONAL_FIELDS, CORE_FIELDS

TRANSCRIPT_LINE = re.compile(r"^\[(?P<id>[^\]]+)\]\s+(?P<who>USER|SCIO):\s*(?P<text>.*)$")
RECORDED_LINE = re.compile(r"^-\s+(?P<field>\w+)\s+=")

# Enough to trigger the conditional branches the gate asks about, from the words
# people actually use. A keyword is not comprehension; it is a signal, which is
# all the schema claims it is.
SIGNAL_WORDS: dict[str, tuple[str, ...]] = {
    "charges_money": ("pay", "payment", "deposit", "fee", "charge", "stripe", "subscription"),
    "mentions_notifications": ("email", "sms", "notify", "notification", "reminder", "push"),
    "external_integrations": ("calendar", "integrat", "crm", "maps", "api", "google sheet"),
    "uploads_media": ("upload", "photo", "image", "video", "file"),
    "sensitive_data": ("health", "medical", "personal data", "gdpr", "sensitive", "phone"),
    "scheduling_logic": ("book", "booking", "slot", "schedule", "appointment", "reservation"),
    "public_content": ("public", "seo", "landing page", "blog"),
    "multi_language": ("language", "translat", "multilingual", "svenska"),
}

# The order the wizard asks in — questions.next_target's order, so the stand-in
# files an answer under the field that was actually just asked about.
ASK_ORDER: tuple[str, ...] = (*CORE_FIELDS, "non_goals", *CONDITIONAL_FIELDS)

_SPLIT = re.compile(r"[;,]| and |\band\b|\n")


def _turns(prompt: str) -> list[tuple[str, str, str]]:
    """(id, who, text) for every line of the transcript inside a prompt."""
    turns = []
    for line in prompt.splitlines():
        match = TRANSCRIPT_LINE.match(line.strip())
        if match:
            turns.append((match["id"], match["who"], match["text"].strip()))
    return turns


def _recorded(prompt: str) -> set[str]:
    """Fields the prompt says are already filled — do not ask them again."""
    return {
        match["field"]
        for line in prompt.splitlines()
        if (match := RECORDED_LINE.match(line.strip()))
    }


def _asked_field(last_question: str) -> str:
    """Which field the last question was about, by its wording.

    Matched against the guide's own question text, which is what the fake path
    always asks: write_question falls back to the guide whenever the model
    cannot answer, and on this path it never can.
    """
    for name in EXTRACTABLE_FIELDS:
        if guide_for(name).question.lower() in last_question.lower():
            return name
    return ""


def _as_list(text: str) -> list[str]:
    items = [part.strip(" .") for part in _SPLIT.split(text)]
    return [item for item in items if len(item) > 1][:8]


def _as_sensitivity(text: str) -> dict:
    lowered = text.lower()
    kinds = [
        kind
        for kind, words in (
            ("payment", ("payment", "card", "stripe", "deposit")),
            ("personal", ("personal", "phone", "email", "address", "name")),
            ("health", ("health", "medical", "patient")),
        )
        if any(word in lowered for word in words)
    ]
    # "I own it" is the overwhelmingly common answer and the product's default;
    # anything else is left to the user's own words at the review screen.
    return {"owner": "you", "sensitive": bool(kinds), "kinds": kinds}


def _value_for(field: str, text: str):
    kind = guide_for(field).kind
    if kind == "list":
        return _as_list(text)
    if kind == "sensitivity":
        return _as_sensitivity(text)
    return text


def answer_extraction(prompt: str) -> str:
    """The extractor's reply: this turn's answer, filed under this turn's question."""
    turns = _turns(prompt)
    recorded = _recorded(prompt)

    last_user = next(((i, t) for i, who, t in reversed(turns) if who == "USER" and t), None)
    if last_user is None:
        return json.dumps({"fields": {}, "signals": {}})
    user_id, user_text = last_user

    last_question = next((t for _, who, t in reversed(turns) if who == "SCIO"), "")
    field = _asked_field(last_question)
    if not field:
        # No question yet — the opening turn. Fall to the next slot the wizard
        # would ask about anyway.
        field = next((name for name in ASK_ORDER if name not in recorded), "")
    # A field already recorded is NOT skipped: when the wizard comes back to one
    # it is because the answers contradict each other, and the whole point of
    # that turn is to replace what is there.
    if not field:
        return json.dumps({"fields": {}, "signals": _signals(turns)})

    return json.dumps(
        {
            "fields": {
                field: {
                    "value": _value_for(field, user_text),
                    "source": "stated",
                    "confidence": "medium",
                    "provenance": [user_id],
                }
            },
            "signals": _signals(turns),
        }
    )


_NEGATED = re.compile(r"\b(no|not|without|never|skip|drop)\b[^.;,]{0,24}$")


def _mentioned(said: str, word: str) -> bool:
    """The word is there, and not being ruled out.

    "no payment data" is the single most common sentence in a booking intake,
    and reading it as "this app takes payments" walks the person through a whole
    branch about Stripe. A signal is not comprehension, but it can at least
    notice the word "no" in front of it.
    """
    for match in re.finditer(re.escape(word), said):
        if not _NEGATED.search(said[: match.start()]):
            return True
    return False


def _signals(turns: list[tuple[str, str, str]]) -> dict[str, bool]:
    said = " ".join(text for _, who, text in turns if who == "USER").lower()
    return {
        name: True
        for name, words in SIGNAL_WORDS.items()
        if any(_mentioned(said, word) for word in words)
    }


def is_extraction_prompt(messages: list[Message]) -> bool:
    """Whether this relay call is intake extraction rather than something else."""
    return any("Scio's intake extractor" in (m.content or "") for m in messages)


class StandInIntakeProvider(ModelProvider):
    """Answers gate 1's prompts deterministically, without a model."""

    vendor = Vendor.fake

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Message]]] = []

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        self.calls.append((model, messages))
        joined = "\n".join(m.content for m in messages)

        # Only extraction is answered. The question writer already falls back to
        # the guide's own wording on an unusable reply, and the guide's question
        # is exactly what the next turn matches the answer against — so an empty
        # reply here is the honest one, not a gap.
        text = answer_extraction(joined) if is_extraction_prompt(messages) else ""

        return Completion(
            text=text,
            model=model,
            vendor=Vendor.fake,
            input_tokens=len(joined.split()),
            output_tokens=len(text.split()),
            stop_reason="end_turn",
        )


def intake_standin_registry() -> ProviderRegistry:
    """A registry that can complete gate 1 with no keys at all."""
    shared = StandInIntakeProvider()
    return ProviderRegistry(
        providers={
            Vendor.anthropic: shared,
            Vendor.openai: shared,
            Vendor.google: shared,
            Vendor.fake: shared,
        }
    )
