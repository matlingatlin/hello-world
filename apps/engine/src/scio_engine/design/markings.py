"""A batch of markings, resolved — one refusal at a time, never one for all.

The design window lets someone mark several things before pressing go: "this
button should say Reserve", "this list needs the date", "this heading is wrong".
That is one change with several targets, and it groups by package because a
package is what regeneration operates on.

The important property is per-marking honesty. If one marking lands on an
element with no `data-scio-id`, that marking is unaddressable — and the other
four are still perfectly good. Failing the whole batch would teach people to
mark one thing at a time; silently dropping it would apply a change they asked
for and never mention that one part was ignored. So each marking carries its own
outcome, and the batch reports both.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..core.instrumentation import Manifest
from ..core.resolver import ElementHit, MarkingResolutionError, resolve_marking


class Marking(BaseModel):
    """One thing the user pointed at, and what they said about it.

    The `hit` fields mirror what the bridge sends (builder/preview/bridge.js),
    including the ancestor — which exists so a refusal can name it, and for no
    other reason. Nothing here may be substituted for `scio_id`.
    """

    scio_id: str | None = None
    scio_package: str | None = None
    tag: str = ""
    text: str = ""
    ancestor_id: str | None = None
    ancestor_package: str | None = None
    ancestor_distance: int = 0
    note: str = Field(default="", description="What the user wants changed about this element")

    def as_hit(self) -> ElementHit:
        return ElementHit(
            scio_id=self.scio_id,
            scio_package=self.scio_package,
            tag=self.tag,
            text=self.text,
            ancestor_id=self.ancestor_id,
            ancestor_package=self.ancestor_package,
            ancestor_distance=self.ancestor_distance,
        )


class ChangeBatch(BaseModel):
    """Everything the user marked, plus whatever they typed for the whole change."""

    markings: list[Marking] = Field(default_factory=list)
    prompt: str = Field(default="", description="An instruction for the change as a whole")

    @property
    def is_empty(self) -> bool:
        return not self.markings and not self.prompt.strip()

    def described(self) -> str:
        """The batch as one instruction, for a prompt or a version description."""
        lines = [f"- {m.scio_id or 'an element'}: {m.note}" for m in self.markings if m.note]
        if self.prompt.strip():
            lines.insert(0, self.prompt.strip())
        return "\n".join(lines) or "no instruction given"


class MarkingOutcome(BaseModel):
    """One marking, and whether it could be addressed at all."""

    marking: Marking
    ok: bool
    package: str = ""
    file: str = ""
    line: int = 0
    error: str = ""


class ResolvedBatch(BaseModel):
    """The batch after the strict resolver has had it."""

    outcomes: list[MarkingOutcome] = Field(default_factory=list)
    prompt: str = ""

    @property
    def addressable(self) -> list[MarkingOutcome]:
        return [o for o in self.outcomes if o.ok]

    @property
    def unaddressable(self) -> list[MarkingOutcome]:
        return [o for o in self.outcomes if not o.ok]

    @property
    def packages(self) -> list[str]:
        """The affected packages, in a stable order — these and no others get rebuilt."""
        seen = {o.package for o in self.addressable}
        return sorted(seen)

    def by_package(self) -> dict[str, list[MarkingOutcome]]:
        grouped: dict[str, list[MarkingOutcome]] = {}
        for outcome in self.addressable:
            grouped.setdefault(outcome.package, []).append(outcome)
        return grouped

    def instruction_for(self, package: str) -> str:
        """What to tell the builder about this package, in the user's own words."""
        lines = [
            f"{o.marking.scio_id} ({o.file}:{o.line}): {o.marking.note or 'change this element'}"
            for o in self.by_package().get(package, [])
        ]
        if self.prompt.strip():
            lines.insert(0, self.prompt.strip())
        return "\n".join(lines)


def resolve_batch(batch: ChangeBatch, manifest: Manifest) -> ResolvedBatch:
    """Resolve every marking. One bad marking never spoils the others."""
    outcomes: list[MarkingOutcome] = []
    for marking in batch.markings:
        try:
            resolved = resolve_marking(marking.as_hit(), manifest)
        except MarkingResolutionError as exc:
            outcomes.append(MarkingOutcome(marking=marking, ok=False, error=str(exc)))
            continue
        outcomes.append(
            MarkingOutcome(
                marking=marking,
                ok=True,
                package=resolved.package,
                file=resolved.location.file,
                line=resolved.location.line,
            )
        )
    return ResolvedBatch(outcomes=outcomes, prompt=batch.prompt)
