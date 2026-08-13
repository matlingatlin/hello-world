"""The build loop for ONE package: generate, run, look, judge, fix — capped.

This is where the pieces meet. Layer C hands over a contract; B031's relay writes
the code; B040's core runs it and holds the three guardrails; the critique judges
it against its acceptance criteria; the deterministic agents check what judgment
should never be asked. Anything still wrong comes back as a fix instruction, and
the whole thing is capped so a package that cannot be finished is *reported*
rather than retried forever.

Order matters, and it is the cheap-and-certain checks first:

    generate -> write -> instrumentation (guardrail 1, rollback on failure)
             -> validation agents -> run + look (guardrail 3: classified console)
             -> critique against "done when" -> fix -> repeat, capped

The critique runs only once the deterministic gates are clean. A model asked to
judge a page we already know is broken costs a relay and tells us what a regex
told us for free.

Full-plan orchestration — dependency order, packages assembled into one app,
aggregate status — is B041b. This builds one package.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from ..core.console import ConsoleReport
from ..core.instrumentation import Manifest
from ..core.manifest_builder import build_manifest
from ..core.preview import Observation, PreviewInspector
from ..core.sandbox import SandboxHandle, SandboxProvider
from ..core.verifier import ids_in_source, verify_instrumentation
from ..execution.provider import ProviderRegistry
from ..execution.relay import BudgetExceeded, RelayOptions, run_relay
from ..layerc.plan import BuildPackage
from .codegen import (
    CODEGEN_SYSTEM,
    FIX_SYSTEM,
    CodeExtractionError,
    build_prompt,
    extract_files,
    fix_prompt,
)
from .critique import Evidence, critique_package
from .file_plan import planned_files
from .persistence import GitError, persist_package_build
from .result import Attempt, PackageBuildResult, PackageStatus, Remainder
from .validation import validate_package

GATES = ("instrumentation", "validation", "console", "critique")
"""What a package must pass. `checks_passed/len(GATES)` is what the reveal shows,
so the count is a real count and not a number chosen to look reassuring."""


class BuildPreview(ABC):
    """How the loop sees the package running.

    An interface because the loop must be testable without booting a dev server
    per iteration. `scripts/verify_core.py` proves the real path against a real
    sandbox; these tests prove the loop's decisions.
    """

    def apply(self, app_dir: Path, files: dict[str, str]) -> None:
        """Put the generated files where the app is served from."""
        for relative, content in files.items():
            target = app_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

    @abstractmethod
    def observe(self, app_dir: Path, *, attempt: int) -> Observation:
        """Load the app and report what it looks like and what it logged."""

    def close(self) -> None:  # noqa: B027 - optional: a scripted preview owns nothing
        """Tear down anything started. Must be safe to call twice."""

    @property
    def url(self) -> str:
        """Where the app is being served, when it is. Empty when nothing runs."""
        return ""


class ScriptedPreview(BuildPreview):
    """Canned observations, in order — for tests and dry runs."""

    def __init__(self, observations: list[Observation], *, loop_last: bool = True) -> None:
        if not observations:
            raise ValueError("ScriptedPreview needs at least one observation")
        self._observations = observations
        self._loop_last = loop_last
        self.calls = 0

    def observe(self, app_dir: Path, *, attempt: int) -> Observation:
        index = self.calls
        self.calls += 1
        if index < len(self._observations):
            return self._observations[index]
        if self._loop_last:
            return self._observations[-1]
        raise AssertionError("ScriptedPreview ran out of observations")


class SandboxPreview(BuildPreview):
    """The real thing: a sandbox serving the app, driven by a headless browser."""

    def __init__(
        self,
        sandbox: SandboxProvider,
        *,
        route: str = "/",
        screenshot_dir: Path | None = None,
    ) -> None:
        self.sandbox = sandbox
        self.route = route
        self.screenshot_dir = screenshot_dir
        self._handle: SandboxHandle | None = None

    def _ensure_started(self, app_dir: Path) -> SandboxHandle:
        if self._handle is None:
            self._handle = self.sandbox.start(app_dir)
        return self._handle

    @property
    def url(self) -> str:
        return self._handle.url if self._handle else ""

    def apply(self, app_dir: Path, files: dict[str, str]) -> None:
        if self._handle is None:
            super().apply(app_dir, files)
            return
        self.sandbox.apply_change(self._handle, files)

    def observe(self, app_dir: Path, *, attempt: int) -> Observation:
        handle = self._ensure_started(app_dir)
        shot = (
            self.screenshot_dir / f"attempt-{attempt}.png" if self.screenshot_dir else None
        )
        return PreviewInspector(handle.url.rstrip("/") + self.route).observe(shot)

    def close(self) -> None:
        if self._handle is not None:
            self.sandbox.stop(self._handle)
            self._handle = None


CODEGEN_MAX_TOKENS = 16000
"""A package is several complete files, and the relay's 4096-token default cuts
the third one in half. Generous rather than exact: output tokens are only billed
when used, and a truncated reply costs a whole extra attempt."""

CODEGEN_TIMEOUT_S = 900.0
"""Writing that much code takes minutes, not seconds. The relay's 120s default is
sized for short calls (a question, a critique verdict); using it for codegen made
every real pass time out — twice, silently, before failing the build."""


@dataclass
class BuildOptions:
    """The caps. Every one of them exists so a bad package costs a known amount."""

    max_attempts: int = 3
    codegen_passes: int = 4  # the full relay for code; clamped to MAX_PASSES
    critique_passes: int = 1
    budget_usd: float | None = None  # the metering hook (ADR-0009) attaches here
    build_version: int = 1
    persist: bool = True
    package_files: dict[str, list[str]] | None = None  # the plan's file map, when known


@dataclass
class _Gate:
    """One iteration's verdicts, collected before deciding what to do."""

    instrumentation_ok: bool = True
    validation_ok: bool = True
    console_ok: bool = True
    critique_passed: bool = False
    problems: list[str] = field(default_factory=list)
    remainders: list[Remainder] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.instrumentation_ok
            and self.validation_ok
            and self.console_ok
            and self.critique_passed
        )

    @property
    def score(self) -> int:
        return sum(
            [
                self.instrumentation_ok,
                self.validation_ok,
                self.console_ok,
                self.critique_passed,
            ]
        )


def _snapshot(app_dir: Path, paths: list[str]) -> dict[str, str | None]:
    """Current contents of every file the package may touch; None = did not exist."""
    snapshot: dict[str, str | None] = {}
    for relative in paths:
        path = app_dir / relative
        snapshot[relative] = path.read_text() if path.exists() else None
    return snapshot


def _restore(app_dir: Path, snapshot: dict[str, str | None]) -> None:
    """Undo a rejected write completely — including deleting files that are new.

    A half-applied rejection is worse than no rejection: the next attempt would
    be judged against code nobody chose.
    """
    for relative, content in snapshot.items():
        path = app_dir / relative
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


def _files_on_disk(app_dir: Path, paths: list[str]) -> dict[str, str]:
    return {p: (app_dir / p).read_text() for p in paths if (app_dir / p).exists()}


async def _generate(
    package: BuildPackage,
    contract: str,
    *,
    registry: ProviderRegistry,
    options: BuildOptions,
    current_files: dict[str, str],
    problems: list[str],
) -> tuple[str, float, bool]:
    """One codegen relay — a first draft, or a repair with the code in hand.

    Returns the reply, what it cost, and whether it was cut off.
    """
    first = not problems
    prompt = (
        build_prompt(package, contract)
        if first
        else fix_prompt(package, contract, current_files, problems)
    )
    result = await run_relay(
        "codegen",
        prompt,
        registry=registry,
        options=RelayOptions(
            passes=options.codegen_passes,
            system=CODEGEN_SYSTEM if first else FIX_SYSTEM,
            budget_usd=options.budget_usd,
            max_tokens=CODEGEN_MAX_TOKENS,
            timeout_s=CODEGEN_TIMEOUT_S,
        ),
    )
    return result.final_text, result.total_cost_usd, result.truncated


def _check_instrumentation(
    app_dir: Path,
    package: BuildPackage,
    allowed: list[str],
    expected_ids: set[str] | None,
    package_files: dict[str, list[str]] | None,
) -> tuple[Manifest, list[str]]:
    """GUARDRAIL 1. Returns the derived manifest and any blocking problems."""
    manifest = build_manifest(app_dir, package_files or {package.id: allowed})
    report = verify_instrumentation(app_dir, manifest, expected_ids=expected_ids)
    return manifest, [f"[instrumentation] {issue.message}" for issue in report.errors]


def _console_problems(console: ConsoleReport) -> list[str]:
    """GUARDRAIL 3. Only failures the classifier attributes to the app itself."""
    return [f"[console] {failure}" for failure in console.failures]


async def build_package(
    package: BuildPackage,
    contract: str,
    app_dir: Path,
    *,
    registry: ProviderRegistry,
    preview: BuildPreview,
    options: BuildOptions | None = None,
    close_preview: bool = True,
) -> PackageBuildResult:
    """Build one package until it passes or the cap is reached.

    Never returns a cheerful result it cannot evidence: a package that ran out of
    attempts comes back as `needs_look` with the remainders that are still true,
    and one that never produced usable code comes back as `failed`.

    `close_preview=False` is for the orchestrator (B041b): packages are built
    into ONE growing app, so the sandbox running it outlives any single package
    and closing it here would tear down the app between parts.
    """
    opts = options or BuildOptions()
    app_dir = Path(app_dir).resolve()
    app_dir.mkdir(parents=True, exist_ok=True)
    allowed = planned_files(package)
    # Everything already standing, when we are building into an assembled app —
    # so the guardrail is app-wide, not merely package-wide.
    tracked = sorted(
        {f for files in (opts.package_files or {}).values() for f in files} | set(allowed)
    )

    result = PackageBuildResult(
        package_id=package.id,
        status=PackageStatus.failed,
        checks_total=len(GATES),
    )
    problems: list[str] = []
    last_gate = _Gate()
    manifest: Manifest | None = None

    try:
        for index in range(1, opts.max_attempts + 1):
            attempt = Attempt(index=index, action="generate" if index == 1 else "fix")
            current = _files_on_disk(app_dir, allowed)

            try:
                text, cost, truncated = await _generate(
                    package,
                    contract,
                    registry=registry,
                    options=opts,
                    current_files=current,
                    problems=problems,
                )
            except BudgetExceeded as exc:
                attempt.problems = [f"[budget] {exc}"]
                result.attempts.append(attempt)
                problems = attempt.problems
                last_gate = _Gate(problems=list(problems))
                break
            attempt.cost_usd = cost
            result.total_cost_usd += cost

            if truncated:
                # The reply ends inside a file. Writing what arrived would put
                # half a component on disk, so nothing is written and the next
                # attempt is told exactly what went wrong.
                attempt.problems = [
                    "[codegen] the reply hit the output-token limit and was cut off — "
                    "no partial file was written. Return the files complete, and shorter."
                ]
                result.attempts.append(attempt)
                problems = attempt.problems
                last_gate = _Gate(problems=list(problems))
                continue

            try:
                extracted = extract_files(text, allowed=allowed)
            except CodeExtractionError as exc:
                attempt.problems = [f"[codegen] {exc}"]
                result.attempts.append(attempt)
                problems = attempt.problems
                last_gate = _Gate(problems=list(problems))
                continue

            # Snapshot before writing: a rejected build must leave no trace.
            before = _snapshot(app_dir, allowed)
            # Every id standing right now must still be addressable afterwards —
            # including ids belonging to packages built before this one.
            expected_ids = ids_in_source(app_dir, tracked) or None

            # Off the event loop: a real preview writes into a sandbox and waits
            # for a dev server to recompile, and Playwright's sync API refuses to
            # run inside a running asyncio loop at all.
            await asyncio.to_thread(preview.apply, app_dir, extracted.files)
            attempt.files_written = sorted(extracted.files)

            gate = _Gate()
            manifest, instrumentation_problems = _check_instrumentation(
                app_dir, package, allowed, expected_ids, opts.package_files
            )
            if instrumentation_problems:
                # GUARDRAIL 1: a regeneration that lost an id is a failed build.
                gate.instrumentation_ok = False
                gate.problems += instrumentation_problems
                gate.remainders += [
                    Remainder(what=p, where=package.id, source="instrumentation")
                    for p in instrumentation_problems
                ]
                _restore(app_dir, before)
                attempt.rolled_back = True
                attempt.instrumentation_ok = False
                attempt.problems = gate.problems
                result.attempts.append(attempt)
                problems = gate.problems
                last_gate = gate
                continue

            on_disk = _files_on_disk(app_dir, allowed)

            report = validate_package(package, on_disk)
            if not report.passed:
                gate.validation_ok = False
                gate.problems += report.instructions()
                gate.remainders += [
                    Remainder(what=f.message, where=f.file or package.id, source="validation")
                    for f in report.errors
                ]

            observation = await asyncio.to_thread(preview.observe, app_dir, attempt=index)
            console_problems = _console_problems(observation.console)
            if console_problems:
                # GUARDRAIL 3: benign browser noise was already filtered out.
                gate.console_ok = False
                gate.problems += console_problems
                gate.remainders += [
                    Remainder(what=p, where=package.id, source="console")
                    for p in console_problems
                ]

            if gate.validation_ok and gate.console_ok:
                evidence = Evidence(
                    console=observation.console,
                    screenshot_path=str(observation.screenshot_path or ""),
                    element_ids=sorted(manifest.elements),
                    extra=[f"Page title: {observation.title}"] if observation.title else [],
                )
                critique = await critique_package(
                    package, evidence, registry=registry, passes=opts.critique_passes
                )
                gate.critique_passed = critique.passed
                if not critique.passed:
                    gate.problems += critique.problems or [
                        f"Criterion not met: {c}" for c in critique.unmet
                    ]
                    gate.remainders += [
                        Remainder(what=p, where=package.id, source="critique")
                        for p in (critique.problems or critique.unmet)
                    ]

            attempt.validation_ok = gate.validation_ok
            attempt.console_ok = gate.console_ok
            attempt.critique_passed = gate.critique_passed
            attempt.problems = gate.problems
            result.attempts.append(attempt)
            last_gate = gate

            if gate.passed:
                break
            problems = gate.problems
    finally:
        if close_preview:
            await asyncio.to_thread(preview.close)

    result.files = sorted(_files_on_disk(app_dir, allowed))
    result.checks_passed = last_gate.score

    if last_gate.passed:
        result.status = PackageStatus.passed
        result.remainders = []
    elif result.files:
        # Built, but with something still wrong: say what, and where.
        result.status = PackageStatus.needs_look
        result.remainders = last_gate.remainders or [
            Remainder(what=p, where=package.id, source="build") for p in last_gate.problems
        ]
    else:
        result.status = PackageStatus.failed
        result.remainders = [
            Remainder(what=p, where=package.id, source="build") for p in last_gate.problems
        ] or [Remainder(what="no usable code was produced", where=package.id, source="build")]

    if opts.persist and result.files and manifest is not None:
        _persist(app_dir, package, manifest, result, opts)

    return result


def _persist(
    app_dir: Path,
    package: BuildPackage,
    manifest: Manifest,
    result: PackageBuildResult,
    opts: BuildOptions,
) -> None:
    """A build that exists on disk gets a version, even when it needs a look.

    Persisting only the good ones would leave the user unable to see — or roll
    back to — the thing they were just shown.
    """
    try:
        persisted = persist_package_build(
            app_dir,
            package_id=package.id,
            description=package.goal,
            manifest=manifest,
            files=result.files,
            build_version=opts.build_version,
        )
    except GitError as exc:
        result.remainders.append(
            Remainder(what=f"the build was not persisted: {exc}", where=package.id, source="build")
        )
        return
    result.build_version = persisted.build_version
    result.git_sha = persisted.git_sha
