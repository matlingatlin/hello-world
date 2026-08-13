"""Plan validation — before a line of code is generated (docs/LAYER-C.md).

Three rules carry the weight: nothing from the architecture is dropped, the
graph can actually be built (no cycles), and every package carries a usable
contract. A plan error caught here costs a function call; caught during the
build it costs a relay run and a sandbox.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from ..builder.file_plan import planned_files
from ..layerb.architecture import Architecture
from .criteria import Observability, cover
from .decompose import architecture_nodes
from .plan import BuildPlan


class Severity(StrEnum):
    error = "error"
    warning = "warning"


class PlanViolation(BaseModel):
    rule: str
    severity: Severity = Severity.error
    message: str
    subject: str = ""


class PlanValidation(BaseModel):
    valid: bool
    violations: list[PlanViolation] = Field(default_factory=list)

    @property
    def errors(self) -> list[PlanViolation]:
        return [v for v in self.violations if v.severity is Severity.error]


def _check_coverage(plan: BuildPlan, arch: Architecture) -> list[PlanViolation]:
    """Every architecture node belongs to some package — nothing silently dropped."""
    covered: set[str] = set()
    for package in plan.packages:
        covered |= package.slice_ids()

    return [
        PlanViolation(
            rule="node_covered",
            message=(
                f"Architecture node '{node.id}' is not built by any package — it would "
                "silently disappear from the app."
            ),
            subject=node.id,
        )
        for node in architecture_nodes(arch)
        if node.id not in covered
    ]


def _check_acyclic(plan: BuildPlan) -> list[PlanViolation]:
    """The build order must cover every package; anything left out sits in a cycle."""
    if len(plan.order) == len(plan.packages):
        return []
    unordered = sorted({p.id for p in plan.packages} - set(plan.order))
    return [
        PlanViolation(
            rule="acyclic",
            message=(
                "The dependency graph has a cycle — these packages can never start: "
                + ", ".join(unordered)
            ),
            subject=", ".join(unordered),
        )
    ]


def _check_dependencies_exist(plan: BuildPlan) -> list[PlanViolation]:
    ids = {p.id for p in plan.packages}
    return [
        PlanViolation(
            rule="dependency_exists",
            message=f"Package '{package.id}' depends on '{dep}', which is not in the plan.",
            subject=package.id,
        )
        for package in plan.packages
        for dep in package.dependencies
        if dep not in ids
    ]


def _check_contracts(plan: BuildPlan) -> list[PlanViolation]:
    """A package without a goal, a slice or acceptance criteria cannot be built or
    verified — the builder would be guessing and the vision loop would have no target."""
    violations: list[PlanViolation] = []
    for package in plan.packages:
        if not package.goal.strip():
            violations.append(
                PlanViolation(
                    rule="contract_complete",
                    message=f"Package '{package.id}' has no goal.",
                    subject=package.id,
                )
            )
        if not package.architecture_slice:
            violations.append(
                PlanViolation(
                    rule="contract_complete",
                    message=(
                        f"Package '{package.id}' owns no architecture nodes — it has nothing "
                        "to build."
                    ),
                    subject=package.id,
                )
            )
        if not package.acceptance_criteria:
            violations.append(
                PlanViolation(
                    rule="contract_testable",
                    message=(
                        f"Package '{package.id}' has no acceptance criteria — the vision loop "
                        "would have nothing to verify against."
                    ),
                    subject=package.id,
                )
            )
    return violations


def _check_criteria_are_reachable(plan: BuildPlan) -> list[PlanViolation]:
    """Every "done when" must map to a file the package actually produces.

    The first real run failed a package on criteria its own file plan could never
    satisfy. That is a contract bug, and it costs a whole relay run and a sandbox
    to discover during a build — so it is caught here, before generation, for the
    price of a string comparison.

    A criterion nobody can *observe* is a warning, not an error: it is recorded,
    scoped out of the critique, and must never fail a build.
    """
    violations: list[PlanViolation] = []
    for package in plan.packages:
        files = planned_files(package)
        for coverage in cover(package.acceptance_criteria, files):
            if not coverage.produced:
                violations.append(
                    PlanViolation(
                        rule="criterion_producible",
                        message=(
                            f"Package '{package.id}' must be done when \"{coverage.criterion}\", "
                            "but nothing in its file plan would produce that. Either the "
                            "criterion belongs to another package or the file plan is missing "
                            "a file."
                        ),
                        subject=package.id,
                    )
                )
            elif coverage.observed_by is Observability.render and not coverage.observable:
                # Marked "the critique will see it" by a package that renders
                # nothing. The build scopes it out rather than failing, but the
                # contract is still wrong and this is where it gets fixed.
                violations.append(
                    PlanViolation(
                        rule="criterion_observable",
                        message=(
                            f"Package '{package.id}': \"{coverage.criterion}\" is marked as "
                            "judged from the rendered app, but this package produces no markup. "
                            "Check it deterministically or scope it out."
                        ),
                        subject=package.id,
                    )
                )
            elif coverage.observed_by is Observability.unsupported:
                violations.append(
                    PlanViolation(
                        rule="criterion_observable",
                        severity=Severity.warning,
                        message=(
                            f"Package '{package.id}': \"{coverage.criterion}\" has no evidence "
                            "channel, so nobody verifies it. It is scoped out of the critique "
                            "rather than failing the build."
                        ),
                        subject=package.id,
                    )
                )
    return violations


def _check_order_respects_dependencies(plan: BuildPlan) -> list[PlanViolation]:
    position = {pid: i for i, pid in enumerate(plan.order)}
    return [
        PlanViolation(
            rule="order_respects_dependencies",
            message=(
                f"Package '{package.id}' is built before its dependency '{dep}'."
            ),
            subject=package.id,
        )
        for package in plan.packages
        if package.id in position
        for dep in package.dependencies
        if dep in position and position[dep] > position[package.id]
    ]


def _check_duplicate_ids(plan: BuildPlan) -> list[PlanViolation]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for package in plan.packages:
        if package.id in seen:
            duplicates.add(package.id)
        seen.add(package.id)
    return [
        PlanViolation(
            rule="unique_package_id",
            message=f"Package id '{pid}' appears more than once.",
            subject=pid,
        )
        for pid in sorted(duplicates)
    ]


def validate_plan(plan: BuildPlan, arch: Architecture) -> PlanValidation:
    violations = [
        *_check_duplicate_ids(plan),
        *_check_coverage(plan, arch),
        *_check_acyclic(plan),
        *_check_dependencies_exist(plan),
        *_check_contracts(plan),
        *_check_criteria_are_reachable(plan),
        *_check_order_respects_dependencies(plan),
    ]
    has_error = any(v.severity is Severity.error for v in violations)
    return PlanValidation(valid=not has_error, violations=violations)
