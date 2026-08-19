"""Correcting a field the wizard filed wrongly — without redoing the wizard.

The defect this fixes is small and infuriating. The wizard extracts an answer
into a typed slot, and sometimes it puts it in the wrong one: "guests and staff"
lands in `entities` instead of `users_and_roles`. The review screen shows it —
that is what the review screen is for — and until now the only way to fix it was
to start over. People will not start over. They will approve a spec they know is
wrong, and every downstream layer will faithfully build the wrong thing.

Three rules make a correction trustworthy:

1. **A correction is authoritative.** It is recorded as `stated` with a
   provenance mark saying a person typed it here, and `extraction.apply_extraction`
   refuses to overwrite a field carrying that mark. The conversation still holds
   the sentence that was misfiled, so without this rule the very next wizard turn
   would quietly re-file it and the correction would evaporate.

2. **A correction is re-validated, not just stored.** It goes back through
   Layer A's own gate and trigger logic, because a correction can OPEN work: two
   roles where there was one triggers `role_permissions`, and sensitive data
   triggers `compliance`. What is now missing comes back with the result, so the
   review screen can ask for it inline instead of sending the user round again.

3. **A correction can settle a contradiction.** Detection is re-run, so fixing
   the answer that caused a conflict clears it — otherwise the gate would stay
   shut on a question the user has already answered by correcting it.

Nothing here writes a spec_version. This edits the working spec only; freezing
stays where it belongs, at approve.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .contradictions import detect, merge
from .fields import EXTRACTABLE_FIELDS, GUIDES
from .gate import BuildableResult, is_buildable, triggered_conditionals
from .schema import (
    CORRECTION_MARK,
    DEFAULTED_FIELDS,
    AppSpec,
    Confidence,
    DataSensitivity,
    FieldMeta,
    Source,
)

__all__ = [
    "CORRECTABLE_FIELDS",
    "CORRECTION_MARK",
    "CorrectionError",
    "CorrectionResult",
    "FieldCorrection",
    "coerce",
    "correct_field",
    "kind_of",
]

CORRECTABLE_FIELDS: tuple[str, ...] = (*EXTRACTABLE_FIELDS, *DEFAULTED_FIELDS)
"""Everything the review screen may edit.

Wider than `EXTRACTABLE_FIELDS` on purpose: the defaulted-and-flagged fields
(platform, look, scale, …) are assumptions shown as assumptions, and the point of
showing them is that the user can say "no, actually". Extraction still may not
touch them — an assumption may only be replaced by a person."""


class CorrectionError(ValueError):
    """The correction cannot be applied. Always says which field and why."""


class FieldCorrection(BaseModel):
    """One correction: put this value in this field, and empty these others."""

    field: str
    value: Any = None
    clear: list[str] = Field(
        default_factory=list,
        description="Fields to empty — how 'this answer belongs under another "
        "field' is expressed: set it on the right one, clear the wrong one.",
    )


class CorrectionResult(BaseModel):
    """The corrected spec, and what the correction changed about the gate."""

    updated_spec: AppSpec
    gate: BuildableResult
    triggered: list[str] = Field(default_factory=list)
    still_needed: list[str] = Field(default_factory=list)
    newly_required: list[str] = Field(
        default_factory=list,
        description="What this correction opened that was not open before — what "
        "the review screen asks for inline before the gate can close.",
    )
    changed: list[str] = Field(default_factory=list)
    cleared: list[str] = Field(default_factory=list)


def kind_of(field: str) -> str:
    """What shape a field holds. The defaulted fields are all one sentence."""
    guide = GUIDES.get(field)
    return guide.kind if guide else "text"


def _as_text(field: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return _refuse(field, "needs a sentence")
    return value.strip()


def _as_list(field: str, value: Any) -> list[str]:
    """A list, or one string treated as one item.

    Empty is allowed for `non_goals` and nowhere else: "nothing excluded" is a
    real answer, while "no entities" is a field that was never answered — and a
    silently emptied core field would close the gate on nothing.
    """
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, list):
        items = [str(part).strip() for part in value]
    else:
        return _refuse(field, "needs a list")
    items = [item for item in items if item]
    if not items and field != "non_goals":
        return _refuse(field, "needs at least one value")
    return items


def _as_sensitivity(field: str, value: Any) -> DataSensitivity:
    if not isinstance(value, dict):
        return _refuse(field, 'needs {"owner", "sensitive", "kinds"}')
    try:
        return DataSensitivity.model_validate(value)
    except ValueError as exc:
        return _refuse(field, str(exc))


def _refuse(field: str, why: str) -> Any:
    raise CorrectionError(f"'{field}' {why}")


def coerce(field: str, value: Any) -> Any:
    """The typed value for this field, or a refusal naming what was wrong.

    Refusing rather than best-guessing: a correction that silently became
    something else would be worse than the misfiling it was fixing.
    """
    kind = kind_of(field)
    if kind == "list":
        return _as_list(field, value)
    if kind == "sensitivity":
        return _as_sensitivity(field, value)
    return _as_text(field, value)


def _open_work(gate: BuildableResult) -> list[str]:
    return [*gate.missing_core, *gate.unresolved_conditionals]


def correct_field(spec: AppSpec, correction: FieldCorrection) -> CorrectionResult:
    """Apply one correction and re-run Layer A's gate over the result."""
    field = correction.field
    if field not in CORRECTABLE_FIELDS:
        raise CorrectionError(f"'{field}' is not a field on the spec")

    for name in correction.clear:
        if name not in EXTRACTABLE_FIELDS:
            # The defaulted fields always hold something — an assumption is
            # replaced, never emptied, or the review screen would show a blank
            # where it used to say what Scio decided on your behalf.
            raise CorrectionError(f"'{name}' cannot be emptied")

    value = coerce(field, correction.value)

    before = _open_work(is_buildable(spec))
    working = spec.model_copy(deep=True)

    for name in correction.clear:
        if name != field:
            setattr(working, name, None)

    setattr(
        working,
        field,
        FieldMeta(
            value=value,
            source=Source.stated,
            confidence=Confidence.high,
            provenance=[CORRECTION_MARK],
        ),
    )

    # A correction can settle the conflict it was the cause of. Detection is
    # deterministic and free, so it is re-run rather than remembered.
    working.contradictions = merge(working, detect(working))
    working = AppSpec.model_validate(working.model_dump())

    gate = is_buildable(working)
    after = _open_work(gate)

    return CorrectionResult(
        updated_spec=working,
        gate=gate,
        triggered=triggered_conditionals(working),
        still_needed=after,
        newly_required=[name for name in after if name not in before],
        changed=[field],
        cleared=[name for name in correction.clear if name != field],
    )
