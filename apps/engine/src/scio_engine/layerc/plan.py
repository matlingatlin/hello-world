"""Layer C models — the build plan (docs/LAYER-C.md, ADR-0013).

A build package is the smallest unit the builder produces in one focused pass.
Its contract is the whole point: goal, the architecture slice it owns, the
*interfaces* of what it depends on (never their full code — that is what keeps
context tight), the relevant "why", the house rules, and testable acceptance
criteria the vision loop aims at.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from .criteria import Criterion, coerce


class PackageKind(StrEnum):
    foundation = "foundation"
    schema = "schema"
    auth = "auth"
    feature = "feature"
    connector = "connector"
    design_tokens = "design_tokens"


class NodeRef(BaseModel):
    """A reference to one node of Layer B's architecture graph.

    Stable, addressable identity is what makes coverage checkable and what the
    marking->code coupling later hangs on: a click on screen `/booking` resolves
    to `screen:/booking`, which resolves to exactly one package.
    """

    kind: str  # "table" | "operation" | "screen" | "connector" | "auth" | "tokens" | "security"
    name: str

    @property
    def id(self) -> str:
        return f"{self.kind}:{self.name}"

    def __hash__(self) -> int:
        return hash(self.id)


class PackageInterface(BaseModel):
    """What a package exposes to the ones that depend on it.

    Deliberately small: names and shapes, not implementations. A downstream
    package needs to know that `create_booking(payload) -> booking` exists, not
    how it was written.
    """

    tables: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    exports: list[str] = Field(default_factory=list)

    def as_lines(self) -> list[str]:
        lines: list[str] = []
        if self.tables:
            lines.append(f"tables: {', '.join(self.tables)}")
        if self.operations:
            lines.append(f"operations: {', '.join(self.operations)}")
        if self.routes:
            lines.append(f"routes: {', '.join(self.routes)}")
        if self.exports:
            lines.append(f"provides: {', '.join(self.exports)}")
        return lines


class BuildPackage(BaseModel):
    """One contract-bearing unit of work."""

    id: str
    kind: PackageKind
    goal: str
    architecture_slice: list[NodeRef] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)  # package ids
    interface: PackageInterface = Field(default_factory=PackageInterface)
    why: str = ""
    house_rules: str = ""
    canonical_vocabulary: dict[str, list[str]] = Field(default_factory=dict)
    scope_guard: list[str] = Field(default_factory=list)
    acceptance_criteria: list[Criterion] = Field(default_factory=list)
    parallelizable: bool = False

    @field_validator("acceptance_criteria", mode="before")
    @classmethod
    def _read_criteria(cls, value: object) -> object:
        """A plain string is still a valid criterion — it just means "judge this
        from the rendered app", which is the common case."""
        if isinstance(value, list):
            return [coerce(item) for item in value]
        return value

    def slice_ids(self) -> set[str]:
        return {node.id for node in self.architecture_slice}


class BuildPlan(BaseModel):
    packages: list[BuildPackage] = Field(default_factory=list)
    order: list[str] = Field(default_factory=list)  # package ids, build sequence
    graph: dict[str, list[str]] = Field(default_factory=dict)  # package id -> dependencies

    def get(self, package_id: str) -> BuildPackage | None:
        return next((p for p in self.packages if p.id == package_id), None)

    def ordered(self) -> list[BuildPackage]:
        by_id = {p.id: p for p in self.packages}
        return [by_id[pid] for pid in self.order if pid in by_id]
