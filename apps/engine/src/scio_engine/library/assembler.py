"""Put a catalog entry into a project — adapted, stamped, verified.

Assembling is not "skip the checks because it came from the library". It is the
same build with the expensive, uncertain step removed: no relay, no repair loop,
no waiting on a model to remember the instrumentation rules. Everything after
the writing still happens — the files go through the same instrumentation
verifier and the same manifest, because an entry that has drifted from the
contract must fail here rather than three packages later.

What adaptation actually is:

- **the project's name**: `__ENTITY__` becomes the canonical entity from Layer B,
  in every path, identifier and id. "Reservations" gets the booking blueprint,
  and the code that lands says `booking` everywhere;
- **the project's look**: `__TOKEN_ACCENT__` and friends resolve from the
  architecture's design tokens, falling back to a neutral value rather than
  shipping a placeholder;
- **the package tag**: `data-scio-package` is stamped exactly as for generated
  code (core/stamping.py). The entry carries the ids; only this project knows
  the package.
"""

from __future__ import annotations

from pathlib import Path

from ..builder.file_plan import planned_files
from ..builder.result import Attempt, PackageBuildResult, PackageStatus, Remainder
from ..core.manifest_builder import build_manifest
from ..core.stamping import stamp_files
from ..core.verifier import verify_instrumentation
from ..layerb.architecture import DesignTokens
from ..layerc.plan import BuildPackage
from .catalog import Catalog
from .entry import CatalogEntry
from .store import default_store

ASSEMBLY_GATES = ("library", "instrumentation")
"""What an assembled package is checked on. Fewer than a generated package's four
because two of them — does it run, does it meet its "done when" — were settled
when the entry was curated, and the third (validation agents) is what curation
means. The instrumentation check still runs on every build: it is about THIS
app's ids, which no entry can know."""


class AssemblyError(RuntimeError):
    """The entry could not be put into this project."""


def token_values(tokens: DesignTokens | None) -> dict[str, str]:
    """The project's tokens as a flat map an entry's bindings can read."""
    if tokens is None:
        return {}
    return {**tokens.palette, **tokens.typography, **tokens.radius}


def assemble_package(
    package: BuildPackage,
    app_dir: Path,
    *,
    entity: str,
    entry: CatalogEntry | None = None,
    catalog: Catalog | None = None,
    tokens: DesignTokens | None = None,
    package_files: dict[str, list[str]] | None = None,
    build_version: int = 1,
) -> PackageBuildResult:
    """Write one entry into the app as this package. No model is involved."""
    # The STORE, not the seed directory: the matcher chose from everything the
    # library knows, contributions included, and an assembler that could only
    # see the seeds would abort the build with "entry not in the catalog" for
    # every entry an earlier build taught it (B061).
    book = catalog or default_store().catalog()
    chosen = entry or book.get(package.catalog_entry)
    if chosen is None:
        raise AssemblyError(
            f"{package.id} is marked assemble but entry '{package.catalog_entry}' is not in "
            "the catalog"
        )

    app_dir = Path(app_dir).resolve()
    app_dir.mkdir(parents=True, exist_ok=True)

    files = chosen.adapt(entity, token_values(tokens))
    expected = set(planned_files(package))
    if set(files) != expected:
        # The matcher already checked this; checking again here means a catalog
        # edited after matching cannot quietly write somewhere else.
        raise AssemblyError(
            f"entry '{chosen.id}' would write {sorted(set(files) - expected)} and miss "
            f"{sorted(expected - set(files))} for {package.id}"
        )

    # The entry carries the ids; the package tag is ours, exactly as for
    # generated code — one code path, so one thing to trust.
    files = stamp_files(files, package.id)
    for relative, content in files.items():
        target = app_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    attempt = Attempt(
        index=1,
        action="assemble",
        files_written=sorted(files),
        instrumentation_ok=True,
        validation_ok=True,
        console_ok=True,
        critique_passed=True,
        cost_usd=0.0,
    )

    manifest = build_manifest(app_dir, package_files or {package.id: sorted(files)})
    report = verify_instrumentation(app_dir, manifest)
    if not report.valid:
        problems = [f"[instrumentation] {issue.message}" for issue in report.errors]
        attempt.instrumentation_ok = False
        attempt.problems = problems
        return PackageBuildResult(
            package_id=package.id,
            status=PackageStatus.needs_look,
            attempts=[attempt],
            files=sorted(files),
            checks_passed=1,
            checks_total=len(ASSEMBLY_GATES),
            build_version=build_version,
            entry_id=chosen.id,
            remainders=[
                Remainder(what=p, where=package.id, source="instrumentation") for p in problems
            ],
        )

    return PackageBuildResult(
        package_id=package.id,
        status=PackageStatus.passed,
        attempts=[attempt],
        files=sorted(files),
        checks_passed=len(ASSEMBLY_GATES),
        checks_total=len(ASSEMBLY_GATES),
        build_version=build_version,
        entry_id=chosen.id,
        total_cost_usd=0.0,
        remainders=[],
    )
