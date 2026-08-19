"""How the library grows: what a finished build offers back, and what is kept.

The library is the nave (docs/STRATEGY.md) — the more of an app that comes from
curated parts, the cheaper and more predictable the next build is. A library
that only ever contains what someone sat down and wrote never gets big enough
for that to matter. So every build offers its work back, and this module is the
sequence of refusals that decides what is actually worth keeping:

    skip what came from the library  →  it is already in there
    require every build gate         →  the build's own checks ARE the quality bar
    generalize                       →  one project's code becomes anybody's
    re-verify                        →  generalization can break code; prove it did not
    gate                             →  no leakage, tested, instrumented
    dedup on the contract            →  new version, new entry, or nothing
    assign an id from the store      →  category.seqno.version, seqno from the DB

Two of these are worth spelling out.

**Skip-if-owned.** A package assembled from entry `booking.1.1` carries that id
(`PackageBuildResult.entry_id`). Without this check the library would contribute
its own entries back to itself on every build, and `booking` would fill up with
identical copies that all match each other.

**Version-vs-new is decided on the contract, not on similarity.** A candidate
whose contract already exists in the library is not a new entry — it is a claim
to be a better version of one. It replaces the existing entry only if it is
better on evidence that was actually counted (`Quality.better_than`), and is
otherwise discarded. This is the difference between a library that improves and
a library that accumulates.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..builder.file_plan import planned_files
from ..builder.result import PackageBuildResult, PackageStatus
from ..execution.provider import ProviderRegistry
from ..layerb.architecture import Architecture
from ..layerc.plan import BuildPackage, PackageKind
from .categories import CategoryRegistry, normalise
from .entry import CatalogEntry, Layer, Quality
from .gate import Candidate, GateResult, review
from .generalize import generalize, suggest_labels
from .identity import Contract
from .matcher import package_category, package_contract, package_entity, package_operations
from .placeholders import ENTITY
from .reverify import ReverifyResult, reverify
from .store import CatalogStore, default_store

CONTRIBUTABLE_KINDS = (PackageKind.feature, PackageKind.auth)
"""What may be offered back — the same kinds the matcher may cover.

Contributing a shell or a schema would be contributing something derived from
one architecture: the next project's foundation is a different shape, and an
entry claiming otherwise would assemble the wrong app."""


class Outcome(BaseModel):
    """What happened to one package's offer. Every path says why."""

    package_id: str
    action: str  # "skipped" | "added" | "improved" | "discarded" | "refused"
    entry_id: str = ""
    replaced: str = ""
    category: str = ""
    reason: str = ""
    gate: GateResult | None = None
    reverified: ReverifyResult | None = None

    @property
    def contributed(self) -> bool:
        return self.action in {"added", "improved"}

    def as_line(self) -> str:
        if self.action == "skipped":
            return f"{self.package_id}: already the library's ({self.entry_id})"
        if self.action == "added":
            return f"{self.package_id}: added as {self.entry_id}"
        if self.action == "improved":
            return f"{self.package_id}: improved {self.replaced} to {self.entry_id}"
        return f"{self.package_id}: not added — {self.reason}"


class ContributionReport(BaseModel):
    outcomes: list[Outcome] = Field(default_factory=list)
    proposed_categories: list[str] = Field(default_factory=list)

    @property
    def added(self) -> list[str]:
        return [o.entry_id for o in self.outcomes if o.contributed]

    def describe(self) -> str:
        if not self.outcomes:
            return "nothing was offered to the library"
        return "\n".join(o.as_line() for o in self.outcomes)


def _package_files(app_dir: Path, result: PackageBuildResult) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative in result.files:
        path = app_dir / relative
        if path.exists() and path.is_file():
            files[relative] = path.read_text()
    return files


def _project_terms(architecture: Architecture | None, entity: str) -> list[str]:
    """The words this project uses for its own concepts.

    Handed to the gate so leakage is checkable, and to the model so it knows
    what to remove. The entity itself is NOT in the list: it has already been
    replaced by the placeholder, and including it would flag every correct
    substitution as a leak.
    """
    if architecture is None:
        return []
    # The entities this app is about, and nothing else. Non-goals are NOT terms:
    # "no payments for now" would flag the word "payment" anywhere in the code
    # and refuse contributions for saying something the project never had.
    terms = {table.name for table in architecture.data_model.tables}
    return sorted(t for t in terms if t and t.lower() != entity.lower() and len(t) > 3)


def eligible(package: BuildPackage, result: PackageBuildResult) -> tuple[bool, str]:
    """Whether this package may be offered at all. Deterministic, and first."""
    if result.entry_id:
        return False, "it came from the library"
    if package.kind not in CONTRIBUTABLE_KINDS:
        return False, f"a {package.kind.value} package is this project's own shape"
    if result.status is not PackageStatus.passed:
        return False, f"the build did not pass it ({result.status.value})"
    if result.checks_total and result.checks_passed < result.checks_total:
        return False, (
            f"it passed {result.checks_passed} of {result.checks_total} build gates"
        )
    defects = [r for r in result.remainders if r.source != "scope"]
    if defects:
        return False, f"the build left something wrong on it: {defects[0].as_line()}"
    return True, ""


def _quality_from_build(result: PackageBuildResult, files: dict[str, str], ids: int) -> Quality:
    """The build's own verdict, recorded as the entry's quality.

    Nothing here is an opinion: every number was counted by a gate that already
    ran. `scores_measured=False` is the honest part — Lighthouse and axe do not
    run in the build yet (B048), and the gate reads the build's gates instead.

    A passing package can still carry `scope` remainders: acceptance criteria
    the gates could not OBSERVE (B054), which is different from criteria it
    failed. Those do not disqualify it — nothing would ever be contributed if
    they did — but they are written into the entry's review notes, so a curator
    reading the listing can see exactly what was never checked about it.
    """
    tests = sum(1 for path in files if "test" in path.lower() or "spec" in path.lower())
    unverified = [r.what for r in result.remainders if r.source == "scope"]
    return Quality(
        tested=tests > 0,
        security_reviewed=True,  # the build's validation agents ran and passed
        scores_measured=False,
        build_gates_passed=result.checks_passed,
        build_gates_total=result.checks_total,
        test_files=tests,
        instrumented_elements=ids,
        review_notes="; ".join(unverified),
    )


def _element_ids(files: dict[str, str]) -> list[str]:
    import re

    found: set[str] = set()
    for body in files.values():
        found |= set(re.findall(r'data-scio-id="([^"]+)"', body))
    return sorted(found)


async def contribute_package(
    package: BuildPackage,
    result: PackageBuildResult,
    app_dir: Path,
    *,
    registry: ProviderRegistry,
    store: CatalogStore | None = None,
    architecture: Architecture | None = None,
    project_id: str = "",
    categories: CategoryRegistry | None = None,
) -> Outcome:
    """Offer one built package to the library, and say what became of it."""
    book = store or default_store()
    entity = package_entity(package)

    allowed, why = eligible(package, result)
    if not allowed:
        return Outcome(
            package_id=package.id,
            action="skipped" if result.entry_id else "refused",
            entry_id=result.entry_id,
            reason=why,
        )

    files = _package_files(Path(app_dir), result)
    if not files:
        return Outcome(package_id=package.id, action="refused", reason="it wrote no files")

    registry_of_categories = categories or book.registry()
    general = await generalize(
        files,
        entity=entity,
        registry=registry,
        categories=registry_of_categories,
        project_terms=_project_terms(architecture, entity),
    )

    category = package_category(package, registry_of_categories)
    proposed = ""
    hashtags: list[str] = []
    if not category:
        # Ambiguous: this is the one place the relay is asked about labels, and
        # even then it may only choose from the registry or say "new".
        category, proposed, hashtags = await suggest_labels(
            general.description or package.goal,
            general.files,
            registry=registry,
            categories=registry_of_categories,
        )
    if not category:
        # A category NAME, never a sentence: it becomes half of an entry id.
        # The entity is the honest default — "sprockets" proposes `sprocket`.
        proposed = normalise(proposed) or normalise(
            entity or package.id.removeprefix("pkg_feature_").removeprefix("pkg_")
        )
        book.propose_category(proposed, general.description or package.goal)
        category = proposed

    ids = _element_ids(general.files)
    candidate_entry = CatalogEntry(
        id=f"{category}.pending.0",  # replaced by the store's id if it is kept
        name=(general.description or package.goal)[:80],
        layer=Layer.feature if package.kind is PackageKind.feature else Layer.pattern,
        description=general.description or package.goal,
        provenance=f"contributed:{project_id or 'unknown'}",
        source_project=project_id,
        category=category,
        hashtags=hashtags,
        provides={
            "entities": [ENTITY],
            "operations": package_operations(package),
            "routes": [n.name for n in package.architecture_slice if n.kind == "screen"],
            "capabilities": [],
        },
        files=general.files,
        element_ids=ids,
        quality=_quality_from_build(result, general.files, len(ids)),
        contract=package_contract(package),
    )
    # The operations were the project's own (`create_booking`); the entry states
    # them generalised, so a future package's contract can equal this one's.
    candidate_entry.provides.operations = list(candidate_entry.contract.operations)
    candidate_entry.provides.routes = list(candidate_entry.contract.routes)

    checked = reverify(candidate_entry)
    if not checked.ok:
        return Outcome(
            package_id=package.id,
            action="refused",
            category=category,
            reason=checked.explain(),
            reverified=checked,
        )

    verdict = review(
        Candidate(entry=candidate_entry, project_terms=_project_terms(architecture, entity))
    )
    if not verdict.accepted:
        return Outcome(
            package_id=package.id,
            action="refused",
            category=category,
            reason=verdict.explain(),
            gate=verdict,
            reverified=checked,
        )

    return _keep(
        book,
        candidate_entry,
        package_id=package.id,
        category=category,
        gate=verdict,
        reverified=checked,
        proposed_category=proposed,
    )


def _existing_with_same_contract(store: CatalogStore, contract: Contract) -> CatalogEntry | None:
    """The entry this candidate is claiming to be a better version of."""
    key = contract.key
    for entry in store.catalog().entries:
        if entry.effective_contract().key == key:
            return entry
    return None


def _keep(
    store: CatalogStore,
    candidate: CatalogEntry,
    *,
    package_id: str,
    category: str,
    gate: GateResult,
    reverified: ReverifyResult,
    proposed_category: str = "",
) -> Outcome:
    """Version-vs-new, then the id, then persist. Deterministic throughout."""
    from .identity import Status

    existing = _existing_with_same_contract(store, candidate.effective_contract())
    candidate.status = Status.provisional

    if existing is not None:
        parsed = existing.entry_id
        if parsed is None:
            # A seed already covers this contract. Seeds were written and
            # reviewed by a person; a build does not get to replace one.
            return Outcome(
                package_id=package_id,
                action="discarded",
                entry_id=existing.id,
                category=category,
                reason=f"the library already has this as the seed '{existing.id}'",
                gate=gate,
                reverified=reverified,
            )
        if not candidate.quality.better_than(existing.quality):
            return Outcome(
                package_id=package_id,
                action="discarded",
                entry_id=existing.id,
                category=category,
                reason=(
                    f"{existing.id} already covers this contract and is not worse "
                    f"({existing.quality.evidence()} vs {candidate.quality.evidence()})"
                ),
                gate=gate,
                reverified=reverified,
            )
        bumped = parsed.bumped()
        candidate.id = str(bumped)
        candidate.version = f"{bumped.version}.0.0"
        store.put(candidate)
        return Outcome(
            package_id=package_id,
            action="improved",
            entry_id=candidate.id,
            replaced=existing.id,
            category=category,
            reason="objectively better on the build's own measurements",
            gate=gate,
            reverified=reverified,
        )

    # `add`, not next_seqno-then-put: the store assigns the number and inserts
    # the row under one lock, so two builds contributing to the same category at
    # the same moment cannot both be handed `booking.2`.
    store.add(candidate, category)
    return Outcome(
        package_id=package_id,
        action="added",
        entry_id=candidate.id,
        category=category,
        reason=(
            f"a new '{category}' entry (category proposed for review)"
            if proposed_category
            else f"a new entry in '{category}'"
        ),
        gate=gate,
        reverified=reverified,
    )


async def contribute_build(
    packages: list[BuildPackage],
    results: list[PackageBuildResult],
    app_dir: Path,
    *,
    registry: ProviderRegistry,
    store: CatalogStore | None = None,
    architecture: Architecture | None = None,
    project_id: str = "",
) -> ContributionReport:
    """Offer everything a build produced. One package's refusal never stops the rest."""
    book = store or default_store()
    by_id = {p.id: p for p in packages}
    report = ContributionReport()

    for result in results:
        package = by_id.get(result.package_id)
        if package is None:
            continue
        try:
            outcome = await contribute_package(
                package,
                result,
                app_dir,
                registry=registry,
                store=book,
                architecture=architecture,
                project_id=project_id,
            )
        except Exception as exc:
            # Contributing is a side-effect of a finished build. It must never
            # be the reason a user's app fails to be delivered.
            outcome = Outcome(
                package_id=result.package_id,
                action="refused",
                reason=f"{type(exc).__name__}: {exc}",
            )
        report.outcomes.append(outcome)

    report.proposed_categories = sorted(
        c.name for c in book.registry().categories if not c.confirmed
    )
    return report


__all__ = [
    "ContributionReport",
    "Outcome",
    "contribute_build",
    "contribute_package",
    "eligible",
    "planned_files",
]
