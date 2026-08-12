"""What to ask next — and how to ask it.

The split is deliberate. WHICH field to ask about is decided by the gate
(`is_buildable` + `triggered_conditionals`): deterministic, reproducible, free,
and impossible for a model to talk its way past. Only the WORDING goes to the
relay, because a natural question in the user's own language is exactly the kind
of thing judgment is for.

Every question carries an example. Not as a hope in a prompt: the question is
returned as {question, example}, and if the model's answer is unusable the
field guide's own wording (from INTAKE-SCHEMA.md) is used instead. A question
without an example gets vague answers, and vague answers become assumptions.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel

from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from .conversation import Conversation
from .fields import guide_for
from .gate import BuildableResult
from .schema import CONDITIONAL_FIELDS, CORE_FIELDS, AppSpec, Contradiction

QUESTION_SYSTEM = """You are Scio's intake agent, asking one person about the app \
they want built. You are warm, brief and concrete, and you never sound like a form.

Answer with JSON only:

{"question": "the question itself", "example": "a short example answer"}

Rules:
- Ask about the ONE thing you are given. Nothing else, and never two questions at once.
- Write in the same language the person has been writing in.
- The example must be a plausible answer to your question, not a restatement of it.
- No preamble, no summary of what they already said, no JSON outside the object."""


class Question(BaseModel):
    """The next thing to ask, and what it is for."""

    field: str = ""  # the intake field it targets; empty for a contradiction
    text: str
    example: str = ""
    about: str = "field"  # "field" | "contradiction"
    written_by: str = "model"  # "model" | "guide" — where the wording came from

    def as_text(self) -> str:
        return f"{self.text} For example: {self.example}" if self.example else self.text


def next_target(spec: AppSpec, gate: BuildableResult) -> str | None:
    """The one field to ask about now, in the order docs/INTAKE-SCHEMA.md lists them.

    Core first (nothing else makes sense without it), then non-goals — the doc
    says it is always asked, and asking it early is what keeps the build from
    sprawling — then whichever conditional branches the answers have triggered.
    """
    if gate.buildable:
        return None
    for name in CORE_FIELDS:
        if name in gate.missing_core:
            return name
    if spec.non_goals is None:
        return "non_goals"
    for name in CONDITIONAL_FIELDS:
        if name in gate.unresolved_conditionals:
            return name
    return None


def _parse(text: str) -> tuple[str, str] | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        candidate = text[start : end + 1] if start != -1 and end > start else None
    if candidate is None:
        return None
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    question = str(data.get("question", "")).strip()
    example = str(data.get("example", "")).strip()
    return (question, example) if question else None


def fallback_question(field: str) -> Question:
    """The doc's own wording. Never worse than nothing, and always has an example."""
    guide = guide_for(field)
    return Question(
        field=field,
        text=guide.question,
        example=guide.example,
        written_by="guide",
    )


def fallback_contradiction_question(contradiction: Contradiction) -> Question:
    return Question(
        field="",
        text=f"{contradiction.description} Which should it be?",
        example="Pick one, or tell me how the two fit together.",
        about="contradiction",
        written_by="guide",
    )


def _field_prompt(conversation: Conversation, field: str) -> str:
    guide = guide_for(field)
    return (
        "## The conversation so far\n"
        f"{conversation.as_prompt() or '(nothing yet)'}\n\n"
        "## Ask about exactly this\n"
        f"field: {field}\n"
        f"what it means: {guide.question}\n"
        f"an example of an answer: {guide.example}\n\n"
        "Write this as your own question to them, in their language, with a short "
        "example of the kind of answer you mean."
    )


def _contradiction_prompt(conversation: Conversation, contradiction: Contradiction) -> str:
    return (
        "## The conversation so far\n"
        f"{conversation.as_prompt() or '(nothing yet)'}\n\n"
        "## Two answers that cannot both hold\n"
        f"fields: {', '.join(contradiction.fields)}\n"
        f"the conflict: {contradiction.description}\n\n"
        "Ask them which way to go. Do not decide for them, do not imply they made a "
        "mistake, and give a short example of an answer that would settle it."
    )


async def write_question(
    conversation: Conversation,
    *,
    registry: ProviderRegistry,
    field: str = "",
    contradiction: Contradiction | None = None,
    passes: int = 1,
) -> Question:
    """Put the chosen question into words. Falls back to the guide on any failure.

    One pass: a question is a sentence, and running the full relay on every turn
    of the wizard would multiply the cheapest part of the build.
    """
    fallback = (
        fallback_contradiction_question(contradiction)
        if contradiction is not None
        else fallback_question(field)
    )
    prompt = (
        _contradiction_prompt(conversation, contradiction)
        if contradiction is not None
        else _field_prompt(conversation, field)
    )

    try:
        result = await run_relay(
            "spec_extraction",
            prompt,
            registry=registry,
            options=RelayOptions(passes=passes, system=QUESTION_SYSTEM, temperature=0.4),
        )
    except Exception:
        return fallback

    parsed = _parse(result.final_text)
    if parsed is None:
        return fallback
    text, example = parsed
    return Question(
        field=fallback.field,
        text=text,
        example=example or fallback.example,
        about=fallback.about,
        written_by="model",
    )
