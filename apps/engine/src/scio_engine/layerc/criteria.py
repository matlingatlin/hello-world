""""Done when" — as a contract, not a wish list.

The first real run failed `pkg_foundation` on three criteria it could never have
met: "the test runner executes on an empty suite", "secrets come from environment
variables only", "secure headers are configured". The critique was right — no
evidence showed any of them — and the contract was wrong: the package's file plan
produces no test config and no middleware, and the vision loop's evidence is a
rendered page, a console log and an element list. Nothing could ever have proved
them.

So a criterion now declares two things about itself:

- **produced_by** — which of the package's planned files would make it true. A
  criterion nothing in the file plan produces is a contract bug, caught by
  `validate.py` before a single token is generated.
- **observed_by** — which channel can actually check it. Only `render` criteria
  reach the critique; `validation` criteria belong to the deterministic agents
  that already check them; `unsupported` ones are recorded and judged by nobody.

An unsupported criterion is kept rather than deleted, because deleting it would
lose the intent — a headers check IS wanted, it just needs an evidence channel
that does not exist yet. What it must never do is fail a build.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Observability(StrEnum):
    render = "render"
    """The vision loop can see it: the rendered page, its console, its elements."""

    validation = "validation"
    """A deterministic agent already checks it (validation.py). Asking the
    critique to re-judge it from a screenshot only invents a false failure."""

    unsupported = "unsupported"
    """Nothing observes it yet. Recorded so the intent survives; never fails a
    build, because a build must not fail for something nobody looked at."""


UI_SUFFIXES = (".tsx", ".jsx", ".html")
"""What the vision loop can actually see. Its evidence is a rendered page, its
console, its element ids and a screenshot *path* — so a package that produces no
markup produces nothing observable, whatever its criteria claim. A migration, a
db helper and a stylesheet are all judged by reading them, not by looking."""


class Criterion(BaseModel):
    """One "done when", with the two things that make it checkable."""

    text: str
    observed_by: Observability = Observability.render
    produced_by: list[str] = Field(
        default_factory=list,
        description="Path fragments of the planned files that would make this true. "
        "Empty means it is about the app as a whole, not a particular file.",
    )

    @field_validator("text")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a criterion needs text")
        return value

    def __str__(self) -> str:  # so existing f-strings and prompts keep working
        return self.text

    def __contains__(self, fragment: str) -> bool:
        """`"renders" in criterion` reads the text, not the model's fields.

        A criterion is still, to everyone reading it, the sentence it carries.
        Without this, `in` silently falls through to Pydantic's field iterator
        and answers False for text that is plainly there.
        """
        return fragment in self.text

    def produced_by_plan(self, planned_files: list[str]) -> bool:
        if not self.produced_by:
            return True
        return any(
            fragment in path for fragment in self.produced_by for path in planned_files
        )

    @property
    def judged_by_critique(self) -> bool:
        return self.observed_by is Observability.render

    def observable_in(self, planned_files: list[str]) -> bool:
        """Whether the evidence could settle this at all.

        A render criterion needs the package to produce markup. Classifying one
        by hand is easy to get wrong — the second real run failed the design
        tokens package on "the palette is applied", which no screenshot *path*
        can show — so the structural half is checked rather than trusted.
        """
        if self.observed_by is Observability.unsupported:
            return False
        if self.observed_by is Observability.validation:
            return True
        return any(path.endswith(UI_SUFFIXES) for path in planned_files)


def coerce(value: object) -> Criterion:
    """Accept a plain string as a render criterion.

    Keeps every caller that writes `acceptance_criteria=["works"]` working — the
    common case is a rendered-behaviour criterion with no file requirement.
    """
    if isinstance(value, Criterion):
        return value
    if isinstance(value, str):
        return Criterion(text=value)
    if isinstance(value, dict):
        return Criterion(**value)
    raise TypeError(f"cannot read {value!r} as an acceptance criterion")


def renders(text: str, *produced_by: str) -> Criterion:
    return Criterion(text=text, observed_by=Observability.render, produced_by=list(produced_by))


def checked(text: str, *produced_by: str) -> Criterion:
    """Covered by a deterministic validation agent, not by judgment."""
    return Criterion(
        text=text, observed_by=Observability.validation, produced_by=list(produced_by)
    )


def unobservable(text: str, *produced_by: str) -> Criterion:
    return Criterion(
        text=text, observed_by=Observability.unsupported, produced_by=list(produced_by)
    )


class Coverage(BaseModel):
    """Whether one criterion is both producible and observable."""

    criterion: str
    produced: bool
    observable: bool
    observed_by: Observability

    @property
    def judgeable(self) -> bool:
        return self.produced and self.observable and self.observed_by is Observability.render

    @property
    def reason(self) -> str:
        if not self.produced:
            return "nothing in the package's file plan would produce it"
        if self.observed_by is Observability.unsupported:
            return "no evidence channel can observe it"
        if self.observed_by is Observability.validation:
            return "a deterministic validation agent checks it instead"
        if not self.observable:
            return "the package renders nothing, so no evidence could show it"
        return "judged by the critique"


def cover(criteria: list[Criterion], planned_files: list[str]) -> list[Coverage]:
    return [
        Coverage(
            criterion=c.text,
            produced=c.produced_by_plan(planned_files),
            observable=c.observable_in(planned_files),
            observed_by=c.observed_by,
        )
        for c in criteria
    ]


def judgeable(criteria: list[Criterion], planned_files: list[str]) -> list[Criterion]:
    """The criteria the critique may actually be asked about.

    Everything else is either someone else's job or nobody's — and asking for a
    verdict on it produces exactly the spurious failure this module exists to
    stop. A misclassified criterion is dropped here too: a mistake in the
    contract must never become a failed build.
    """
    return [
        c
        for c in criteria
        if c.judged_by_critique
        and c.produced_by_plan(planned_files)
        and c.observable_in(planned_files)
    ]


def scoped_out(criteria: list[Criterion], planned_files: list[str]) -> list[str]:
    """What was NOT judged, and why — for the build's honest record."""
    return [
        f"{c.criterion} — {c.reason}"
        for c in cover(criteria, planned_files)
        if not c.judgeable
    ]
