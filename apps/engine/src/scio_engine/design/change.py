"""The directed change: a batch in, a changed preview out — or a question.

The order is the whole design, and each step exists to stop a specific failure:

    resolve strictly   a marking that cannot be addressed is named, not guessed
    detect conflicts   a marking that argues with the spec is asked, not built
    ask the model      once per affected package, with that package's notes
    guardrails         isolation + instrumentation, per package, before accepting

The last step is the core's `directed_regenerate`, unchanged. The model's output
never reaches disk without going through it: a package that comes back with a
lost `data-scio-id`, or that edited a file it does not own, is rolled back and
reported. Several packages are simply that loop run several times — and a
package whose regeneration is rejected does not stop the others, because a batch
that fails whole would make people mark one thing at a time.

What does NOT happen here: unaffected packages are not rebuilt, not re-verified
and not touched. The isolation proof says so per package, and the byte-identical
count is what the design window shows.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..builder.codegen import FIX_SYSTEM, CodeExtractionError, extract_files
from ..core.instrumentation import Manifest
from ..core.regenerate import PackageRegenerator, directed_regenerate
from ..core.stamping import stamp_files
from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from ..layerb.architecture import Architecture
from .conflicts import Conflict, detect_conflicts
from .markings import ChangeBatch, MarkingOutcome, ResolvedBatch, resolve_batch

CHANGE_MAX_TOKENS = 16000
CHANGE_TIMEOUT_S = 900.0
"""The same budget the builder's codegen gets: this is the same job, on files
that already exist."""


class PackageChange(BaseModel):
    """What happened to one package."""

    package: str
    instruction: str
    edited_files: list[str] = Field(default_factory=list)
    unchanged_files: int = 0
    isolated: bool = False
    accepted: bool = False
    rejection: str = ""
    rolled_back: bool = False
    cost_usd: float = 0.0

    def as_line(self) -> str:
        if self.accepted:
            return (
                f"{self.package}: changed {', '.join(self.edited_files)} "
                f"({self.unchanged_files} other files byte-identical)"
            )
        return f"{self.package}: not applied — {self.rejection}"


class DesignChangeResult(BaseModel):
    """Everything the design window needs to show after a change."""

    applied: bool = False
    conflicts: list[Conflict] = Field(default_factory=list)
    packages: list[PackageChange] = Field(default_factory=list)
    unaddressable: list[MarkingOutcome] = Field(default_factory=list)
    manifest: Manifest | None = None
    total_cost_usd: float = 0.0
    description: str = ""

    @property
    def changed_packages(self) -> list[str]:
        return [p.package for p in self.packages if p.accepted]

    def summary(self) -> str:
        if self.conflicts:
            return (
                f"Not applied — {len(self.conflicts)} thing(s) need your call: "
                + "; ".join(c.question for c in self.conflicts)
            )
        if not self.packages:
            return "Nothing to change — no marking could be addressed."
        lines = [p.as_line() for p in self.packages]
        if self.unaddressable:
            lines.append(
                f"{len(self.unaddressable)} marking(s) could not be addressed and were skipped"
            )
        return "\n".join(lines)


class DesignChange(BaseModel):
    """A change request as the api sends it."""

    batch: ChangeBatch
    package_files: dict[str, list[str]] = Field(default_factory=dict)


class PreparedRegenerator(PackageRegenerator):
    """Edits that were computed before the guardrails run.

    `directed_regenerate` is synchronous and the relay is not, so the model call
    happens first and its result is handed in here. Nothing is skipped by doing
    it this way: the isolation proof, the instrumentation re-verification and the
    rollback all still run on exactly these files.
    """

    def __init__(self, edits: dict[str, str]) -> None:
        self.edits = edits

    def regenerate(self, app_dir, package, files, marking, instruction) -> dict[str, str]:
        stray = sorted(set(self.edits) - set(files))
        if stray:
            raise ValueError(f"'{package}' was given files it does not own: {', '.join(stray)}")
        if not self.edits:
            raise ValueError(f"the change produced no files for '{package}'")
        return self.edits


def change_prompt(
    package: str, contract: str, current: dict[str, str], instruction: str
) -> str:
    """What the builder is told. The code goes in verbatim.

    A model asked to change code it cannot see invents a plausible replacement,
    which is how ids get lost — and a lost id is a failed build (B039). It is
    also why the instruction names the exact elements the user marked.
    """
    listing = "\n\n".join(
        f"FILE: {path}\n```\n{content}```" for path, content in sorted(current.items())
    )
    return (
        f"{contract}\n\n"
        "---\n\n"
        f"## The current code for `{package}`\n\n{listing}\n\n"
        "## What the user marked, and what they want\n\n"
        f"{instruction}\n\n"
        "Change exactly these things. Keep every data-scio-id and every "
        "data-scio-package exactly as they are — they are how the user points at "
        "this code, and losing one fails the build. Return the complete files you "
        "changed, and only files this package owns."
    )


async def _edits_for(
    package: str,
    contract: str,
    current: dict[str, str],
    instruction: str,
    *,
    registry: ProviderRegistry,
    passes: int,
) -> tuple[dict[str, str], float]:
    """One package's new code, from the relay."""
    result = await run_relay(
        "codegen",
        change_prompt(package, contract, current, instruction),
        registry=registry,
        options=RelayOptions(
            passes=passes,
            system=FIX_SYSTEM,
            max_tokens=CHANGE_MAX_TOKENS,
            timeout_s=CHANGE_TIMEOUT_S,
        ),
    )
    if result.truncated:
        raise CodeExtractionError(
            "the reply hit the output-token limit and was cut off — nothing was written"
        )
    extracted = extract_files(result.final_text, allowed=list(current) or None)
    return stamp_files(extracted.files, package), result.total_cost_usd


async def apply_change(
    app_dir: Path,
    batch: ChangeBatch,
    *,
    manifest: Manifest,
    architecture: Architecture,
    registry: ProviderRegistry,
    contracts: dict[str, str] | None = None,
    package_files: dict[str, list[str]] | None = None,
    passes: int = 1,
) -> DesignChangeResult:
    """The whole guarded round trip. Never raises for a bad marking or a conflict."""
    app_dir = Path(app_dir).resolve()
    resolved: ResolvedBatch = resolve_batch(batch, manifest)

    result = DesignChangeResult(
        unaddressable=resolved.unaddressable,
        manifest=manifest,
        description=batch.described(),
    )

    # Asked before anything is built, and before a single token is spent.
    conflicts = detect_conflicts(batch, architecture)
    if conflicts:
        result.conflicts = conflicts
        return result

    if not resolved.addressable:
        return result

    files_map = package_files or manifest.packages
    for package in resolved.packages:
        instruction = resolved.instruction_for(package)
        owned = files_map.get(package, manifest.files_for(package))
        current = {f: (app_dir / f).read_text() for f in owned if (app_dir / f).exists()}

        change = PackageChange(package=package, instruction=instruction)
        try:
            edits, cost = await _edits_for(
                package,
                (contracts or {}).get(package, f"# Package: {package}"),
                current,
                instruction,
                registry=registry,
                passes=passes,
            )
            change.cost_usd = cost
            result.total_cost_usd += cost
        except Exception as exc:
            change.rejection = f"{type(exc).__name__}: {exc}"
            result.packages.append(change)
            continue

        # The first addressable marking in this package is the one the core
        # resolves against; the rest are in the instruction. Any of them resolves
        # to the same package, which is what the guardrail checks.
        anchor = resolved.by_package()[package][0]
        try:
            regeneration = directed_regenerate(
                app_dir,
                anchor.marking.as_hit(),
                instruction,
                manifest=result.manifest or manifest,
                regenerator=PreparedRegenerator(edits),
                package_files=files_map,
            )
        except Exception as exc:
            change.rejection = f"{type(exc).__name__}: {exc}"
            result.packages.append(change)
            continue

        change.edited_files = regeneration.edited_files
        change.unchanged_files = len(regeneration.isolation.unchanged_files)
        change.isolated = regeneration.isolation.isolated
        change.accepted = regeneration.accepted
        change.rejection = regeneration.rejection
        change.rolled_back = regeneration.rolled_back
        result.packages.append(change)
        if regeneration.accepted:
            # Each accepted package moves the manifest on, so the next package's
            # isolation proof compares against what is actually on disk.
            result.manifest = regeneration.manifest

    result.applied = any(p.accepted for p in result.packages)
    return result
