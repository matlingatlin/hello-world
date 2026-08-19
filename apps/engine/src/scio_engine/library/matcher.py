"""Between Layer B and Layer C: does the library already know how to build this?

The decision is per package and it is deliberately conservative, because the two
mistakes are not symmetric. Generating something the library already has costs
money and consistency. *Assembling the wrong thing* ships code that looks
reviewed and is not what the user asked for.

So the decision is made in two steps that do different jobs (B061):

**The category narrows.** A package about bookings only ever looks at entries in
the `booking` category. This is a canonical lookup, not free text
(`library/categories.py`) — which is what stops the library splitting into
`login`, `auth` and `user-accounts` holding three copies of one thing.

**The contract decides.** A contract is what a thing does with the project's own
words removed: canonical operations, routes and files, all against `__ENTITY__`
(`library/identity.py`). Equality of contracts is a match. That is an identity,
not a resemblance — it still means every operation is covered and the files
written are exactly the package's file plan, because both are *in* the contract.

It also means "reservations" finds the booking blueprint without anyone teaching
the matcher about restaurants, and it means an entry contributed by one project
matches the next project's equivalent package even though neither ever shared a
word.

Only when two vetted entries survive is there anything for a model to decide,
and only then does the relay get asked. The relay never decides a match.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from ..builder.file_plan import entity_of, planned_files
from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from ..layerb.vocabulary import canonical_name
from ..layerc.plan import BuildPackage, BuildPlan, PackageKind
from .catalog import Catalog, default_catalog
from .categories import CategoryRegistry, default_registry
from .entry import CatalogEntry
from .identity import Contract

MATCHABLE_KINDS = (PackageKind.feature, PackageKind.auth)
"""Which packages the library may cover.

Features and auth are the parts that repeat across apps in a shape a blueprint
can hold. The shell, the schema and the design tokens are project-shaped —
their content is derived from THIS app's architecture, and an entry claiming to
cover one would be claiming to know something it cannot."""


class Decision(StrEnum):
    assemble = "assemble"
    generate = "generate"


class Match(BaseModel):
    """What the library decided about one package, and why."""

    package_id: str
    decision: Decision
    entry_id: str = ""
    entity: str = ""
    category: str = ""
    contract_key: str = ""
    reason: str = ""
    considered: list[str] = Field(default_factory=list)

    @property
    def assembles(self) -> bool:
        return self.decision is Decision.assemble


class MatchReport(BaseModel):
    matches: list[Match] = Field(default_factory=list)

    def for_package(self, package_id: str) -> Match | None:
        return next((m for m in self.matches if m.package_id == package_id), None)

    @property
    def assembled(self) -> list[str]:
        return [m.package_id for m in self.matches if m.assembles]

    @property
    def generated(self) -> list[str]:
        return [m.package_id for m in self.matches if not m.assembles]

    def describe(self) -> str:
        """The line the build view can show: how much of this came from the library."""
        total = len(self.matches)
        if not total:
            return "no packages to match"
        return (
            f"{len(self.assembled)} of {total} parts from the library, "
            f"{len(self.generated)} generated"
        )


AMBIGUITY_SYSTEM = """You are Scio's library matcher. Two curated components both \
claim to cover the same feature. Answer with the id of the better fit and nothing else. \
If neither is clearly right, answer exactly: none."""


def package_entity(package: BuildPackage) -> str:
    """The canonical entity a feature package is about."""
    return canonical_name(entity_of(package))


def package_operations(package: BuildPackage) -> list[str]:
    """What this package DOES, as the contract's identity.

    Operation nodes when it has them. When it has none — `pkg_auth` owns a
    single `auth:auth_access` node and no operations — the other non-screen
    nodes stand in, by their addressable ids. Without this such a package would
    have an empty contract, which must never match anything, and it could
    therefore be neither assembled nor learned from. Screens are excluded here
    because they are already the contract's `routes`.
    """
    operations = [node.name for node in package.architecture_slice if node.kind == "operation"]
    if operations:
        return operations
    return [node.id for node in package.architecture_slice if node.kind != "screen"]


def package_routes(package: BuildPackage) -> list[str]:
    return [node.name for node in package.architecture_slice if node.kind == "screen"]


def package_contract(package: BuildPackage) -> Contract:
    """What this package does, in the same shape an entry states it.

    The files come from the file plan rather than from anything written yet:
    matching happens BEFORE the build, and the plan is the same source the
    manifest's package→file map uses, so the two cannot disagree.
    """
    return Contract.of(
        operations=package_operations(package),
        routes=package_routes(package),
        files=planned_files(package),
        entity=package_entity(package),
    )


def package_category(package: BuildPackage, registry: CategoryRegistry | None = None) -> str:
    """Which area of an app this package belongs to, canonically.

    Tried most specific first: the package's own entity, then the words in its
    id, then its kind. `pkg_auth` lands in `auth` without anyone having taught
    the registry about package ids.
    """
    book = registry or default_registry()
    return book.resolve(
        package_entity(package), package.id.removeprefix("pkg_"), package.kind.value
    )


def candidates(
    package: BuildPackage,
    catalog: Catalog,
    *,
    registry: CategoryRegistry | None = None,
) -> list[CatalogEntry]:
    """Every vetted entry that could build this package, whole."""
    if package.kind not in MATCHABLE_KINDS:
        return []

    contract = package_contract(package)
    if contract.empty:
        # A package that claims no operations describes nothing, and an empty
        # contract would otherwise equal every other empty one.
        return []

    category = package_category(package, registry)

    return [
        entry
        for entry in catalog.offerable()
        # The category narrows. An entry without one is not excluded — a seed
        # written before categories existed still matches on its contract.
        if (not entry.category or not category or entry.category == category)
        and contract.satisfied_by(entry.effective_contract())
    ]


async def resolve_ambiguity(
    package: BuildPackage,
    options: list[CatalogEntry],
    *,
    registry: ProviderRegistry,
) -> CatalogEntry | None:
    """The one place a model is asked: two vetted entries, both a real fit."""
    listing = "\n".join(f"- {e.id}: {e.name} — {e.description}" for e in options)
    prompt = (
        f"## The package\n{package.id} — {package.goal}\n\n"
        f"## Candidates\n{listing}\n\nWhich id fits better?"
    )
    try:
        result = await run_relay(
            "spec_extraction",
            prompt,
            registry=registry,
            options=RelayOptions(passes=1, system=AMBIGUITY_SYSTEM, max_tokens=64),
        )
    except Exception:
        return None  # a matcher that cannot decide generates; it never guesses

    answer = result.final_text.strip().lower()
    # Longest id first: "feature-booking" is a prefix of "feature-booking-twin",
    # and a substring scan would confidently return the wrong one.
    for entry in sorted(options, key=lambda e: len(e.id), reverse=True):
        if entry.id.lower() in answer:
            return entry
    return None


async def match_plan(
    plan: BuildPlan,
    *,
    catalog: Catalog | None = None,
    registry: ProviderRegistry | None = None,
    use_judgment: bool = True,
    categories: CategoryRegistry | None = None,
) -> MatchReport:
    """Decide assemble-vs-generate for every package in the plan."""
    book = catalog or default_catalog()
    matches: list[Match] = []

    for package in plan.packages:
        entity = package_entity(package)
        category = package_category(package, categories)
        contract = package_contract(package)
        options = candidates(package, book, registry=categories)
        considered = [e.id for e in options]

        if not options:
            matches.append(
                Match(
                    package_id=package.id,
                    decision=Decision.generate,
                    entity=entity,
                    category=category,
                    contract_key=contract.key,
                    reason="nothing in the library covers this package exactly",
                    considered=considered,
                )
            )
            continue

        chosen = options[0]
        reason = (
            f"'{category or entity}' is covered by a vetted entry with exactly this contract "
            f"({contract.describe()})"
        )
        if len(options) > 1:
            picked = (
                await resolve_ambiguity(package, options, registry=registry)
                if use_judgment and registry is not None
                else None
            )
            if picked is None:
                matches.append(
                    Match(
                        package_id=package.id,
                        decision=Decision.generate,
                        entity=entity,
                        category=category,
                        contract_key=contract.key,
                        reason=(
                            "several vetted entries fit and none was clearly better — "
                            "generating rather than picking one at random"
                        ),
                        considered=considered,
                    )
                )
                continue
            chosen = picked
            reason = "chosen between equally-matching entries"

        matches.append(
            Match(
                package_id=package.id,
                decision=Decision.assemble,
                entry_id=chosen.id,
                entity=entity,
                category=category,
                contract_key=contract.key,
                reason=reason,
                considered=considered,
            )
        )

    return MatchReport(matches=matches)


def apply_matches(plan: BuildPlan, report: MatchReport) -> None:
    """Record the decision on the plan, so everything downstream can see it."""
    for package in plan.packages:
        match = report.for_package(package.id)
        if match is None:
            continue
        package.source = match.decision.value
        package.catalog_entry = match.entry_id
