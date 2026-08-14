"""Between Layer B and Layer C: does the library already know how to build this?

The decision is per package and it is deliberately conservative, because the two
mistakes are not symmetric. Generating something the library already has costs
money and consistency. *Assembling the wrong thing* ships code that looks
reviewed and is not what the user asked for — so a match has to be an identity,
not a resemblance:

1. the entry must be vetted (tested + security-reviewed);
2. its entity must be the package's entity, in canonical vocabulary — this is
   what makes "reservations" find the booking blueprint without anyone teaching
   the matcher about restaurants;
3. every operation the package owns must be one the entry provides. An entry
   that does four of the package's five operations is not a match; the fifth
   would silently vanish;
4. the files it would write must be exactly the package's file plan. Anything
   else and the manifest's package→file map would disagree with the disk, which
   is the drift the spike punished.

Only when two vetted entries survive all four is there anything for a model to
decide, and only then does the relay get asked.
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
from .entry import CatalogEntry


class Decision(StrEnum):
    assemble = "assemble"
    generate = "generate"


class Match(BaseModel):
    """What the library decided about one package, and why."""

    package_id: str
    decision: Decision
    entry_id: str = ""
    entity: str = ""
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


def _covers_operations(entry: CatalogEntry, package: BuildPackage) -> bool:
    owned = {
        canonical_name(node.name)
        for node in package.architecture_slice
        if node.kind == "operation"
    }
    if not owned:
        return False
    provided = {canonical_name(op) for op in entry.provides.operations}
    return owned <= provided


def _writes_exactly_the_plan(entry: CatalogEntry, package: BuildPackage, entity: str) -> bool:
    return set(entry.adapted_paths(entity)) == set(planned_files(package))


def candidates(package: BuildPackage, catalog: Catalog) -> list[CatalogEntry]:
    """Every vetted entry that could build this package, whole."""
    if package.kind is not PackageKind.feature:
        # This slice matches feature blueprints only. The shell, the schema and
        # the tokens are project-shaped in ways no seed entry can claim yet.
        return []

    entity = package_entity(package)
    if not entity:
        return []

    return [
        entry
        for entry in catalog.offerable()
        if entity in entry.provides.canonical_entities()
        and _covers_operations(entry, package)
        and _writes_exactly_the_plan(entry, package, entity)
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
) -> MatchReport:
    """Decide assemble-vs-generate for every package in the plan."""
    book = catalog or default_catalog()
    matches: list[Match] = []

    for package in plan.packages:
        entity = package_entity(package)
        options = candidates(package, book)
        considered = [e.id for e in options]

        if not options:
            matches.append(
                Match(
                    package_id=package.id,
                    decision=Decision.generate,
                    entity=entity,
                    reason="nothing in the library covers this package exactly",
                    considered=considered,
                )
            )
            continue

        chosen = options[0]
        reason = f"'{entity}' is covered by a vetted entry, files and operations exactly"
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
