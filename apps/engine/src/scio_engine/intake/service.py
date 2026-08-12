"""One turn of gate 1: what they said in, the updated spec and the next question out.

    extract -> detect contradictions -> ask the gate -> ask the next question

Order matters. Extraction runs first because the gate can only judge what has
been recorded; contradictions are checked before the gate because an unresolved
conflict must hold it shut; and the question is written last, once we know
exactly what is missing.

The refined confirmation the user sees at the spec gate — "the whole" — is Layer
B's job and is deliberately not built here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from .contradictions import detect, merge
from .conversation import Conversation, IntakeMessage
from .extraction import ExtractionReport, extract
from .gate import BuildableResult, is_buildable, triggered_conditionals
from .questions import Question, next_target, write_question
from .schema import AppSpec, Confidence, Contradiction, FieldMeta, Source


class IntakeStep(BaseModel):
    """What the wizard needs after one exchange."""

    updated_spec: AppSpec
    buildable: bool
    next_question: Question | None = None
    contradictions: list[Contradiction] = Field(default_factory=list)
    gate: BuildableResult
    triggered: list[str] = Field(default_factory=list)
    extraction: ExtractionReport = Field(default_factory=ExtractionReport)

    @property
    def done(self) -> bool:
        return self.buildable and self.next_question is None


def _assume_no_non_goals(spec: AppSpec) -> None:
    """Nothing excluded, said out loud rather than left blank.

    docs/INTAKE-SCHEMA.md asks for non-goals always; the gate does not block on
    them. Rather than hold a finished wizard open for a field the gate ignores,
    the answer becomes an explicit flagged default — so the review screen shows
    "nothing excluded (assumed)" and the user can correct it in one edit. Silence
    would have meant the same thing without ever showing it.
    """
    if spec.non_goals is None:
        spec.non_goals = FieldMeta(
            value=[], source=Source.default, confidence=Confidence.low
        )


async def run_intake_step(
    messages: list[IntakeMessage],
    spec: AppSpec | None = None,
    *,
    registry: ProviderRegistry,
    extraction_passes: int = 2,
    question_passes: int = 1,
) -> IntakeStep:
    """Advance the wizard by one turn."""
    conversation = Conversation.of(messages)
    working = (spec or AppSpec()).model_copy(deep=True)

    working, report = await extract(
        conversation, working, registry=registry, passes=extraction_passes
    )
    working.contradictions = merge(working, detect(working))

    gate = is_buildable(working)
    open_conflicts = [c for c in working.contradictions if not c.resolved]

    question: Question | None = None
    if open_conflicts:
        # Ask, never resolve: the gate stays shut until the user decides.
        question = await write_question(
            conversation,
            registry=registry,
            contradiction=open_conflicts[0],
            passes=question_passes,
        )
    else:
        target = next_target(working, gate)
        if target is not None:
            question = await write_question(
                conversation, registry=registry, field=target, passes=question_passes
            )

    if gate.buildable and question is None:
        _assume_no_non_goals(working)

    return IntakeStep(
        updated_spec=working,
        buildable=gate.buildable,
        next_question=question,
        contradictions=open_conflicts,
        gate=gate,
        triggered=triggered_conditionals(working),
        extraction=report,
    )
