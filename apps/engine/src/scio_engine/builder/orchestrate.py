"""Build the whole plan: packages in order, assembled into ONE growing app.

B041a builds a package. This builds an app. The difference is not a loop around
the loop — it is *assembly*:

- every package is generated into the workspace that already holds the packages
  before it, and the app runs as a whole after each addition (one sandbox, one
  URL, one manifest), so package N integrates with 1..N-1 instead of being
  correct alone and wrong together;
- the manifest and the instrumentation guardrail are app-wide, so a new package
  that collides with an existing id fails at the moment it is written;
- a package that cannot meet its contract is isolated: the packages that DEPEND
  on it are marked blocked and never built on top of something broken, while
  everything independent keeps building.

The result is one honest aggregate — what works, what needs a look, what was not
built and why — which is exactly what the reveal shows (PRODUCT-OVERVIEW).

MVP is sequential. `parallelizable` is already recorded on the packages by Layer
C; a scheduler is a later optimisation, not a correctness question.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field, replace
from pathlib import Path

from pydantic import BaseModel, Field

from ..core.instrumentation import Manifest
from ..core.manifest_builder import build_manifest
from ..core.public_url import public_url
from ..execution.provider import ProviderRegistry
from ..layerb.architecture import DesignTokens
from ..layerc.plan import BuildPackage, BuildPlan
from .file_plan import file_plan, planned_files
from .loop import GATES, BuildOptions, BuildPreview, build_package, verify_package
from .persistence import GitError, head_sha, persist_package_build
from .result import PackageBuildResult, PackageStatus, Remainder
from .typecheck import blame, typecheck


class BuildProgress(BaseModel):
    """One step of the progression the build view shows.

    The build view promises real progress ("9 of 12 parts done"), so the count
    comes from packages actually finished — never from a timer pretending.
    """

    package_id: str
    index: int  # 1-based position in the build order
    total: int
    done: int
    status: str
    message: str = ""

    def as_line(self) -> str:
        return f"{self.done} of {self.total} parts done — {self.message or self.package_id}"


class AppBuildResult(BaseModel):
    """The whole build, said honestly."""

    order: list[str] = Field(default_factory=list)
    packages: list[PackageBuildResult] = Field(default_factory=list)
    app_remainders: list[Remainder] = Field(
        default_factory=list,
        description="Things wrong with the app as a WHOLE rather than with one part — a "
        "compile error in a file nobody owns, say. Kept apart from the per-package lists so "
        "they do not distort the part count the reveal shows.",
    )
    app_unjudged: list[str] = Field(
        default_factory=list,
        description="App-wide checks nobody could run. They ride along exactly like a "
        "package's unjudged criteria: 'works' keeps meaning 'works, and here is what nobody "
        "checked'.",
    )
    build_version: int | None = None
    git_sha: str = ""
    app_url: str = ""
    element_count: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0

    def _ids(self, status: PackageStatus) -> list[str]:
        return [p.package_id for p in self.packages if p.status is status]

    @property
    def working(self) -> list[str]:
        return self._ids(PackageStatus.passed)

    @property
    def needs_look(self) -> list[str]:
        return self._ids(PackageStatus.needs_look)

    @property
    def blocked(self) -> list[str]:
        return self._ids(PackageStatus.blocked)

    @property
    def failed(self) -> list[str]:
        return self._ids(PackageStatus.failed)

    @property
    def total_parts(self) -> int:
        return len(self.packages)

    @property
    def works(self) -> bool:
        """True only when every part passed AND nothing is wrong app-wide.

        There is no partial 'yes' here — the parts that need a look are listed
        instead. The app-wide half was added when a build reported "5 of 5 parts
        work" for an app that did not compile: every part met its own contract,
        and the seam between two of them did not.
        """
        return (
            bool(self.packages)
            and all(p.works for p in self.packages)
            and not self.app_remainders
        )

    def get(self, package_id: str) -> PackageBuildResult | None:
        return next((p for p in self.packages if p.package_id == package_id), None)

    def honest_summary(self) -> str:
        """What the reveal says out loud: the count first, then every remainder."""
        head = f"{len(self.working)} of {self.total_parts} parts work."
        if self.app_remainders:
            head += f" {len(self.app_remainders)} problem(s) across the app."
        tail: list[str] = []
        if self.needs_look:
            tail.append(f"{len(self.needs_look)} need a look")
        if self.blocked:
            tail.append(f"{len(self.blocked)} not built (a dependency is broken)")
        if self.failed:
            tail.append(f"{len(self.failed)} failed")
        lines = [head + (" " + ", ".join(tail) + "." if tail else "")]
        lines += [
            p.honest_status() for p in self.packages if p.status is not PackageStatus.passed
        ]
        return "\n".join(lines)


@dataclass
class AppBuildOptions:
    """Caps for the whole build. Per-package caps live in `package`."""

    package: BuildOptions = field(default_factory=BuildOptions)
    build_version: int = 1
    persist: bool = True
    close_preview: bool = True  # B043 (the live design window) will keep it open
    tokens: DesignTokens | None = None  # the project's look, for assembled parts


ASSEMBLY_HEADER = "## Already in this app (built before you — integrate, do not rewrite)"


def assembly_context(built: list[PackageBuildResult], manifest: Manifest | None) -> str:
    """What is already standing in the workspace this package joins.

    The contract already names the *interfaces* a package may lean on (Layer C).
    This adds what actually exists on disk right now — files and ids — because a
    package generated against a plan rather than against the real workspace is
    how you get two site headers and a second, slightly different button.
    """
    standing = [r for r in built if r.files]
    if not standing:
        return ""

    lines = [ASSEMBLY_HEADER, ""]
    for result in standing:
        lines.append(f"- {result.package_id} ({result.status}):")
        lines += [f"    {path}" for path in result.files]
        if manifest:
            ids = sorted(
                scio_id
                for scio_id, location in manifest.elements.items()
                if location.package == result.package_id
            )
            if ids:
                lines.append(f"    ids already taken: {', '.join(ids)}")
    lines += [
        "",
        "Import what these export, reuse their components and names, and never "
        "redefine or restyle them. Every id above is taken: reusing one is a "
        "failed build.",
    ]
    return "\n".join(lines)


def _blocked_result(package: BuildPackage, dependency: str, root: str) -> PackageBuildResult:
    return PackageBuildResult(
        package_id=package.id,
        status=PackageStatus.blocked,
        checks_total=len(GATES),
        remainders=[
            Remainder(
                what=(
                    f"not built: it depends on {dependency}, which is not finished"
                    + (f" (because of {root})" if root != dependency else "")
                ),
                where=root,
                source="orchestration",
            )
        ],
    )


def _built_file_map(
    plan: BuildPlan, results: list[PackageBuildResult]
) -> dict[str, list[str]]:
    """Only packages that actually produced files. A manifest claiming files that
    do not exist is the drift the spike punished."""
    by_id = {p.id: p for p in plan.packages}
    return {
        result.package_id: planned_files(by_id[result.package_id])
        for result in results
        if result.files and result.package_id in by_id
    }


def _run_typecheck(
    app_dir: Path, plan: BuildPlan, results: list[PackageBuildResult]
) -> tuple[list[Remainder], list[str]]:
    """The app-wide gate: does what we are about to hand over actually compile?

    Run once, after everything is in place, because the failure it exists to
    catch lives BETWEEN packages — a library component written against an
    interface this app's foundation does not provide. Every per-package gate
    passed that build honestly, and it still did not compile.

    A package the compiler blames stops being `passed`: it is `needs_look`, with
    the file and the line. Files nobody owns go to the app's own list rather
    than being pinned on whichever part happened to be nearest.
    """
    report = typecheck(app_dir)
    if not report.ran:
        return [], ([report.unjudged] if report.unjudged else [])

    by_package = blame(report.problems, _built_file_map(plan, results))
    app_level: list[Remainder] = []
    for package_id, problems in by_package.items():
        remainders = [
            Remainder(what=p.as_line(), where=package_id or "the app", source="typecheck")
            for p in problems
        ]
        result = next((r for r in results if r.package_id == package_id), None)
        if result is None:
            app_level += remainders
            continue
        result.remainders += remainders
        if result.status is PackageStatus.passed:
            result.status = PackageStatus.needs_look

    if report.truncated:
        app_level.append(
            Remainder(
                what=f"and {report.truncated} more type error(s) not listed",
                where="the app",
                source="typecheck",
            )
        )
    return app_level, []


async def stream_build_plan(
    plan: BuildPlan,
    app_dir: Path,
    *,
    contracts: dict[str, str],
    registry: ProviderRegistry,
    preview: BuildPreview,
    options: AppBuildOptions | None = None,
) -> AsyncIterator[tuple[str, BaseModel | str]]:
    """Build every package in dependency order, into one app, yielding progress.

    Events: "progress" (BuildProgress, before and after each package), "package"
    (PackageBuildResult), "result" (AppBuildResult). The API turns these into
    SSE; tests consume them directly — the same shape the relay uses.
    """
    opts = options or AppBuildOptions()
    app_dir = Path(app_dir).resolve()
    app_dir.mkdir(parents=True, exist_ok=True)

    ordered = plan.ordered()
    total = len(ordered)
    plan_files = file_plan(plan.packages)

    results: list[PackageBuildResult] = []
    broken: dict[str, str] = {}  # package id -> the root cause package id
    manifest: Manifest | None = None
    done = 0

    try:
        for index, package in enumerate(ordered, start=1):
            bad_dep = next((d for d in package.dependencies if d in broken), None)
            if bad_dep is not None:
                # Never build on a broken dependency — and say which one.
                result = _blocked_result(package, bad_dep, broken[bad_dep])
                broken[package.id] = broken[bad_dep]
                results.append(result)
                done += 1
                yield "package", result
                yield (
                    "progress",
                    BuildProgress(
                        package_id=package.id,
                        index=index,
                        total=total,
                        done=done,
                        status=result.status,
                        message=result.honest_status(),
                    ),
                )
                continue

            yield (
                "progress",
                BuildProgress(
                    package_id=package.id,
                    index=index,
                    total=total,
                    done=done,
                    status="building",
                    message=f"Building {package.id}: {package.goal}",
                ),
            )

            # Imported here, not at module scope: the library reads the file
            # plan, which lives in this package — importing it eagerly makes a
            # cycle that only shows up depending on who imports first.
            from ..library.assembler import assemble_package, unmet_requirements
            from ..library.matcher import package_entity
            from ..library.store import default_store

            assemble = package.assembled
            if assemble:
                # Does this app provide what the component imports? The entry
                # names the packages it depends on, and until now that was all
                # it named — so a component could be dropped into an app whose
                # foundation exports something else entirely, and did (B116).
                # Checked BEFORE writing anything, because "generate it instead"
                # is a working app and a report about a broken one is not.
                entry = default_store().catalog().get(package.catalog_entry)
                missing = unmet_requirements(app_dir, entry) if entry else []
                if missing:
                    assemble = False
                    yield (
                        "progress",
                        BuildProgress(
                            package_id=package.id,
                            index=index,
                            total=total,
                            done=done,
                            status="building",
                            message=(
                                f"{package.id}: the library part needs {', '.join(missing)}, "
                                "which this app does not provide — building it instead"
                            ),
                        ),
                    )

            if assemble:
                # The library covers this one: no relay, no repair loop. The
                # instrumentation verifier still runs inside assemble_package —
                # curation settles whether the part is good, never whether it
                # fits THIS app's ids.
                result = assemble_package(
                    package,
                    app_dir,
                    entity=package_entity(package),
                    tokens=opts.tokens,
                    package_files=plan_files,
                    build_version=index,
                )
            else:
                contract = contracts.get(
                    package.id, f"# Build package: {package.id}\n{package.goal}"
                )
                context = assembly_context(results, manifest)
                if context:
                    contract = f"{contract}\n\n{context}\n"

                result = await build_package(
                    package,
                    contract,
                    app_dir,
                    registry=registry,
                    preview=preview,
                    options=replace(
                        opts.package,
                        package_files=plan_files,
                        build_version=index,
                    ),
                    close_preview=False,  # one app, one sandbox — it outlives this package
                )

            results.append(result)
            done += 1
            if result.status is not PackageStatus.passed:
                broken[package.id] = package.id
            if result.files:
                manifest = build_manifest(app_dir, _built_file_map(plan, results))

            yield "package", result
            yield (
                "progress",
                BuildProgress(
                    package_id=package.id,
                    index=index,
                    total=total,
                    done=done,
                    status=result.status,
                    message=result.honest_status(),
                ),
            )
    finally:
        # The engine drives the preview over loopback; the browser that opens it
        # may be somewhere else entirely, so what we PUBLISH can differ from
        # where it runs. Identity locally — see core/public_url.
        app_url = public_url(preview.url)
        if opts.close_preview:
            await asyncio.to_thread(preview.close)

    app_remainders, app_unjudged = _run_typecheck(app_dir, plan, results)

    app_result = AppBuildResult(
        order=[p.id for p in ordered],
        packages=results,
        app_url=app_url,
        total_cost_usd=sum(r.total_cost_usd for r in results),
        total_tokens=sum(r.total_tokens for r in results),
        element_count=len(manifest.elements) if manifest else 0,
        app_remainders=app_remainders,
        app_unjudged=app_unjudged,
    )

    if opts.persist and manifest is not None:
        _persist_app(app_dir, manifest, app_result, opts)

    yield "result", app_result


def _persist_app(
    app_dir: Path, manifest: Manifest, result: AppBuildResult, opts: AppBuildOptions
) -> None:
    """One version for the assembled app, with the app-wide manifest.

    Persisted even when parts need a look: the user is shown this build, so the
    user must be able to return to exactly it (PRODUCT-OVERVIEW's versions).
    """
    files = sorted({f for package in result.packages for f in package.files})
    try:
        persisted = persist_package_build(
            app_dir,
            package_id="app",
            description=f"assembled build — {len(result.working)}/{result.total_parts} parts work",
            manifest=manifest,
            files=files,
            build_version=opts.build_version,
        )
    except GitError as exc:
        result.packages.append(
            PackageBuildResult(
                package_id="app",
                status=PackageStatus.needs_look,
                remainders=[
                    Remainder(what=f"the assembled build was not persisted: {exc}", source="build")
                ],
            )
        )
        return
    result.build_version = persisted.build_version
    result.git_sha = persisted.git_sha


async def stream_verification(
    plan: BuildPlan,
    app_dir: Path,
    *,
    registry: ProviderRegistry,
    preview: BuildPreview,
    options: AppBuildOptions | None = None,
) -> AsyncIterator[tuple[str, BaseModel | str]]:
    """Judge an app that already exists, part by part, without building it.

    Same events, same order and the same honest aggregate as
    `stream_build_plan` — the build view cannot tell the difference and should
    not have to. What it never does is generate, repair, write or commit: the
    app on disk is the deliverable (the user shaped it in the design window),
    and this says what is true about it.

    There is no dependency isolation here for the same reason there is no repair
    loop. Nothing is being built on top of anything: every part already exists,
    so every part gets judged and reported rather than skipped for the company
    it keeps.
    """
    opts = options or AppBuildOptions()
    app_dir = Path(app_dir).resolve()

    ordered = plan.ordered()
    total = len(ordered)
    plan_files = file_plan(plan.packages)

    # Imported here rather than at module scope, like the assembler below: the
    # library reads the file plan, which lives in this package.
    from ..library.assembler import ASSEMBLY_GATES

    results: list[PackageBuildResult] = []
    done = 0

    try:
        for index, package in enumerate(ordered, start=1):
            yield (
                "progress",
                BuildProgress(
                    package_id=package.id,
                    index=index,
                    total=total,
                    done=done,
                    status="building",
                    message=f"Checking {package.id}: {package.goal}",
                ),
            )

            result = await verify_package(
                package,
                app_dir,
                registry=registry,
                preview=preview,
                options=replace(opts.package, package_files=plan_files, persist=False),
                close_preview=False,  # one app, one sandbox — it outlives this part
                # Judged the way it was built: a library part answers to its ids
                # and to curation, not to this app's operation names.
                gates=ASSEMBLY_GATES if package.assembled else GATES,
            )
            results.append(result)
            done += 1

            yield "package", result
            yield (
                "progress",
                BuildProgress(
                    package_id=package.id,
                    index=index,
                    total=total,
                    done=done,
                    status=result.status,
                    message=result.honest_status(),
                ),
            )
    finally:
        app_url = public_url(preview.url)
        if opts.close_preview:
            await asyncio.to_thread(preview.close)

    manifest = build_manifest(app_dir, _built_file_map(plan, results))
    app_remainders, app_unjudged = _run_typecheck(app_dir, plan, results)
    yield (
        "result",
        AppBuildResult(
            order=[p.id for p in ordered],
            packages=results,
            app_url=app_url,
            app_remainders=app_remainders,
            app_unjudged=app_unjudged,
            # Only the critique costs anything here; nothing was generated.
            total_cost_usd=sum(r.total_cost_usd for r in results),
            total_tokens=sum(r.total_tokens for r in results),
            element_count=len(manifest.elements),
            build_version=opts.build_version,
            git_sha=head_sha(app_dir),
        ),
    )


async def run_build_plan(
    plan: BuildPlan,
    app_dir: Path,
    *,
    contracts: dict[str, str],
    registry: ProviderRegistry,
    preview: BuildPreview,
    options: AppBuildOptions | None = None,
) -> AppBuildResult:
    """Run the whole plan to completion. Same pipeline, no progress events."""
    final: AppBuildResult | None = None
    async for event, payload in stream_build_plan(
        plan,
        app_dir,
        contracts=contracts,
        registry=registry,
        preview=preview,
        options=options,
    ):
        if event == "result" and isinstance(payload, AppBuildResult):
            final = payload
    assert final is not None  # stream_build_plan always ends with "result"
    return final
