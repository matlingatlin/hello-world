"""What a package build produced — including when it didn't work.

PRODUCT-OVERVIEW: the vision loop has a cap, so builds sometimes finish with
known remainders. Those are shown honestly ("this works; this still needs a
look"), never hidden. That promise starts here, in the shape of the result.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class PackageStatus(StrEnum):
    passed = "passed"
    needs_look = "needs_look"  # built, but a known remainder — honest status
    failed = "failed"  # could not produce usable code at all
    blocked = "blocked"  # never attempted: something it depends on is broken


class Remainder(BaseModel):
    """One thing that is still wrong, said plainly enough to act on."""

    what: str
    where: str = ""
    source: str = ""  # "critique" | "validation" | "console" | "interaction" | ...

    def as_line(self) -> str:
        where = f" ({self.where})" if self.where else ""
        return f"{self.what}{where}"


class Attempt(BaseModel):
    """One trip round the loop, kept so the reveal can explain what happened."""

    index: int
    action: str  # "generate" | "fix"
    files_written: list[str] = Field(default_factory=list)
    instrumentation_ok: bool = True
    validation_ok: bool = True
    console_ok: bool = True
    interaction_ok: bool = True
    critique_passed: bool = False
    problems: list[str] = Field(default_factory=list)
    rolled_back: bool = False
    cost_usd: float = 0.0
    tokens: int = 0


class PackageBuildResult(BaseModel):
    package_id: str
    status: PackageStatus
    attempts: list[Attempt] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    remainders: list[Remainder] = Field(default_factory=list)
    build_version: int | None = None
    git_sha: str = ""
    entry_id: str = Field(
        default="",
        description="The library entry this package was assembled from, when it was. This is "
        "what lets the contribute step skip a package that CAME from the library instead of "
        "offering it back as if the build had invented it.",
    )
    total_cost_usd: float = 0.0
    total_tokens: int = Field(
        default=0,
        description="Input + output tokens spent on this package. Recorded beside the cost "
        "because a figure with no quantity behind it cannot be audited or re-priced.",
    )
    checks_passed: int = 0
    checks_total: int = 0

    @property
    def works(self) -> bool:
        return self.status is PackageStatus.passed

    def honest_status(self) -> str:
        """The line the reveal shows. Never optimistic beyond the evidence."""
        if self.status is PackageStatus.passed:
            checks = f"{self.checks_passed}/{self.checks_total}"
            return f"{self.package_id}: works — {checks} checks passed."
        if self.status is PackageStatus.needs_look:
            first = self.remainders[0].as_line() if self.remainders else "something is unfinished"
            more = f" (+{len(self.remainders) - 1} more)" if len(self.remainders) > 1 else ""
            return f"{self.package_id}: needs a look — {first}{more}"
        if self.status is PackageStatus.blocked:
            reason = self.remainders[0].as_line() if self.remainders else "a dependency is broken"
            return f"{self.package_id}: not built — {reason}"
        reason = self.remainders[0].as_line() if self.remainders else "no usable code was produced"
        return f"{self.package_id}: failed — {reason}"
