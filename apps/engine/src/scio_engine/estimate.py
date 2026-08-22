"""What this build will cost and how long it will take — before it runs.

Deterministic and free. Pricing a build must never cost a model call: most specs
are priced far more often than they are built (every wizard finish, every
revisit), and a build that never happens would still have been paid for.

The number is a **range**, always, and always for the **base build without
changes**. A single figure would be a promise the build cannot keep — a package
that needs a repair round costs about twice one that passes first time, and
whether it does is not knowable in advance. Saying "$0.42" would be false
precision; saying "$0.35–$0.80, before any changes you ask for afterwards" is
what is actually true.

The composition is part of the answer, not decoration: "6 parts · 4 reused · 2
built" is where the library's saving becomes visible to the person deciding
whether to press build.

---

## The heuristic, and how to calibrate it

Every number below is an OUTPUT-token count for one relay pass, keyed on what
the package is and how much of it there is.

**This under-predicts the point cost, and knowingly.** The relay used to price a
pass on its output alone, and these constants were calibrated against figures it
produced; the relay now prices input as well (it was a third to a half of the
real invoice), so a build's *measured* cost is higher than the point this
computes. The published range still holds — `HIGH_MULTIPLIER` is 2.6, which
covers it comfortably, and the ceiling is taken from the high end — but the low
end is now optimistic. Fixing it properly means predicting input tokens too, and
that needs a real run to calibrate against rather than a coefficient invented
here (B115).

Calibrated against the three real runs (2026-08-12), all of them on
**claude-sonnet-5 at two passes** — `SCIO_MODEL_PASSES=1`, $15/M output. The
shipped default is dearer (the full relay over the ranked matrix: Opus, four
passes), and the estimate moves with the profile rather than assuming either.

Cost observed per package, and the implied output tokens:

| package        | observed cost   | implied tokens | notes                     |
|----------------|-----------------|----------------|---------------------------|
| foundation     | $0.168 – $0.312 | 11k – 21k      | layout + header + client  |
| design_tokens  | $0.094 – $0.152 | 6k – 10k       | css + tailwind config     |
| schema         | $0.085 – $0.087 | ~5.7k          | migration + types         |
| auth           | $0.073 – $0.088 | ~5k            | one helper + a test       |
| feature (2 ops,| $0.857          | ~57k           | included a truncated      |
|  2 screens)    |                 |                | attempt; a clean pass is  |
|                |                 |                | roughly half that         |

The whole five-package plan, fully generated with one repair round, came to
**$1.42 in 14 minutes**. `tests/test_estimate.py` asserts the range still
contains that figure, so a change to these constants that drifts away from the
one real invoice we have fails the suite.

To re-calibrate: run a build, read `total_cost_usd` per package off the finished
event, divide by the model's `cost_per_mtok`, and adjust the constants here. They
are deliberately all in one place, and nothing else in the engine encodes an
opinion about how big a package is.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .execution.matrix import CapabilityMatrix, ModelCard
from .execution.profile import run_profile
from .layerc.plan import BuildPackage, BuildPlan, PackageKind

# --- the heuristic -----------------------------------------------------------

BASE_OUTPUT_TOKENS: dict[PackageKind, int] = {
    PackageKind.foundation: 5500,
    PackageKind.design_tokens: 3000,
    PackageKind.schema: 2500,
    PackageKind.auth: 2500,
    PackageKind.feature: 6000,
    PackageKind.connector: 3000,
}
"""What a package of this kind costs before counting what is in it."""

PER_OPERATION_TOKENS = 2500
PER_SCREEN_TOKENS = 2500
PER_TABLE_TOKENS = 800
"""Each thing the package owns adds code: an operation is a data path plus its
validation and a test, a screen is a page, a table is a few lines of migration."""

CRITIQUE_OUTPUT_TOKENS = 400
"""The judgment call at the end of each package. Short — it answers per criterion."""

LOW_MULTIPLIER = 0.7
HIGH_MULTIPLIER = 2.6
"""The range. Low is every package passing first time with tight output; high is
a build where the feature packages need repair rounds and the model is verbose.

Calibrated against every real build we have, not chosen (B077):

    5 generated + 1 assembled   point 13.6 min   took 10.8 min   ratio 0.79
    7 generated                 point 18.5 min   took 45.9 min   ratio 2.48
    7 generated                 point  $1.39     cost   $2.69    ratio 1.93

The old high of 1.8 excluded BOTH of the figures we later measured — a 46-minute
build was advertised as "up to 33 minutes", and $2.69 as "up to $2.51". A range
whose top the real world walks past is not a range, it is an underestimate with
error bars. `tests/test_estimate.py` pins all three observations inside the band,
so tightening these constants without new evidence fails the suite.

The spread is genuinely this wide because one feature package can need two full
repair rounds while another passes first time; B076's chunking narrows the worst
tail (a package can no longer be lost to the output cap) but does not remove it."""

ASSEMBLE_SECONDS = 3
"""An assembled package is a file copy and a verifier pass."""

SECONDS_PER_PASS = 60
PACKAGE_OVERHEAD_SECONDS = 30
"""Per generated package: each relay pass, plus writing, recompiling and looking
at the running app once."""

STARTUP_SECONDS = 60
"""Workspace scaffold, dependency install (cached after the first build) and the
first dev-server boot."""


class Range(BaseModel):
    """A low-high band. Never collapsed to one number for display."""

    low: float
    high: float

    def scaled(self, factor: float) -> Range:
        return Range(low=self.low * factor, high=self.high * factor)

    def rounded(self, places: int = 2) -> Range:
        return Range(low=round(self.low, places), high=round(self.high, places))


class Composition(BaseModel):
    """Where the app comes from — the library's saving, made visible."""

    parts_total: int = 0
    assembled: int = 0
    generated: int = 0

    def describe(self) -> str:
        if not self.parts_total:
            return "nothing to build"
        parts = f"{self.parts_total} parts"
        if self.assembled:
            return f"{parts} · {self.assembled} reused · {self.generated} built"
        return f"{parts} · all built"


class PackageEstimate(BaseModel):
    """One package's share, kept so a surprising total can be explained."""

    package_id: str
    kind: str
    assembled: bool
    output_tokens: int
    cost_usd: float
    seconds: float


class BuildEstimate(BaseModel):
    """The answer shown at the spec gate."""

    cost_usd: Range
    minutes: Range
    composition: Composition
    model: str = ""
    passes: int = 0
    price_per_mtok: float = 0.0
    basis: str = "the base build, without changes"
    per_package: list[PackageEstimate] = Field(default_factory=list)

    def describe(self) -> str:
        return (
            f"${self.cost_usd.low:.2f}–${self.cost_usd.high:.2f} · "
            f"{self.minutes.low:.0f}–{self.minutes.high:.0f} min · "
            f"{self.composition.describe()} — {self.basis}"
        )


def expected_output_tokens(package: BuildPackage) -> int:
    """How much code this package is, in output tokens for one pass."""
    slice_kinds = [node.kind for node in package.architecture_slice]
    return (
        BASE_OUTPUT_TOKENS.get(package.kind, 3000)
        + PER_OPERATION_TOKENS * slice_kinds.count("operation")
        + PER_SCREEN_TOKENS * slice_kinds.count("screen")
        + PER_TABLE_TOKENS * slice_kinds.count("table")
    )


def _pricing_model(matrix: CapabilityMatrix) -> ModelCard:
    """The model that will actually write the code — the one codegen ranks first.

    Read from the same matrix and profile the relay uses, so an operator who
    switches to Haiku sees the estimate move without touching this file.
    """
    return matrix.top_n("codegen", n=1)[0]


def estimate_plan(plan: BuildPlan) -> BuildEstimate:
    """Price a plan. Deterministic, and no model is called."""
    profile = run_profile()
    card = _pricing_model(profile.matrix)
    passes = max(1, profile.passes)

    per_package: list[PackageEstimate] = []
    for package in plan.packages:
        if package.assembled:
            per_package.append(
                PackageEstimate(
                    package_id=package.id,
                    kind=package.kind.value,
                    assembled=True,
                    output_tokens=0,
                    cost_usd=0.0,
                    seconds=ASSEMBLE_SECONDS,
                )
            )
            continue

        tokens = expected_output_tokens(package) * passes + CRITIQUE_OUTPUT_TOKENS
        per_package.append(
            PackageEstimate(
                package_id=package.id,
                kind=package.kind.value,
                assembled=False,
                output_tokens=tokens,
                cost_usd=tokens / 1_000_000 * card.cost_per_mtok,
                seconds=SECONDS_PER_PASS * passes + PACKAGE_OVERHEAD_SECONDS,
            )
        )

    point_cost = sum(p.cost_usd for p in per_package)
    point_seconds = STARTUP_SECONDS + sum(p.seconds for p in per_package)

    composition = Composition(
        parts_total=len(plan.packages),
        assembled=sum(1 for p in per_package if p.assembled),
        generated=sum(1 for p in per_package if not p.assembled),
    )

    return BuildEstimate(
        cost_usd=Range(
            low=point_cost * LOW_MULTIPLIER, high=point_cost * HIGH_MULTIPLIER
        ).rounded(2),
        minutes=Range(
            low=point_seconds * LOW_MULTIPLIER / 60,
            high=point_seconds * HIGH_MULTIPLIER / 60,
        ).rounded(1),
        composition=composition,
        model=card.id,
        passes=passes,
        price_per_mtok=card.cost_per_mtok,
        per_package=per_package,
    )
