"""Approved spec -> running app. The whole path, in one stream.

    spec -> Layer B (the whole + architecture) -> Layer C (the build plan)
         -> orchestrated build into ONE running app -> honest aggregate

Each stage already exists and is tested on its own; this is the seam that makes
them a product rather than a set of parts. It streams because a build takes
minutes and the build view promises real progress — "9 of 12 parts done" has to
come from parts actually finishing.

The preview is deliberately left running when the build ends: the reveal embeds
the app the user just watched being built, so tearing the sandbox down at the
last event would hand them a dead frame.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from pydantic import BaseModel, Field

from ..core.instrumentation import Manifest
from ..core.manifest_builder import build_manifest
from ..core.sandbox import SandboxProvider, choose_sandbox
from ..execution.profile import run_profile
from ..execution.provider import ProviderRegistry
from ..intake.schema import AppSpec
from ..layerb.service import run_layer_b
from ..layerc.service import run_layer_c
from ..library.contribute import ContributionReport, contribute_build
from ..library.verification import VerificationDatabase, verification_enabled
from ..library.verification import prepare as prepare_verification
from .file_plan import file_plan
from .loop import BuildOptions, BuildPreview, SandboxPreview
from .orchestrate import AppBuildOptions, AppBuildResult, stream_build_plan
from .preview_bridge import prepare as prepare_bridge
from .preview_bridge import preview_env
from .result import PackageBuildResult
from .standin import standin_registry
from .workspace import prepare_workspace


class BuildStarted(BaseModel):
    """What is about to be built — sent before any package runs, so the build
    view draws the real schedule instead of a spinner."""

    project_id: str
    whole: str = ""
    packages: list[str] = Field(default_factory=list)
    total: int = 0
    workspace: str = ""
    models: str = ""  # what the relay will run, so the build view can say so


class BuildFinished(BaseModel):
    """The reveal's payload: the running app, and what is true about it."""

    project_id: str
    app_url: str = ""
    build_version: int | None = None
    git_sha: str = ""
    whole: str = ""
    summary: str = ""
    works: bool = False
    parts_working: list[str] = Field(default_factory=list)
    parts_needing_a_look: list[str] = Field(default_factory=list)
    parts_blocked: list[str] = Field(default_factory=list)
    parts_failed: list[str] = Field(default_factory=list)
    remainders: list[str] = Field(default_factory=list)
    element_count: int = 0
    files: list[str] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    standin: bool = False
    workspace: str = ""
    preview: bool = Field(
        default=False, description="Whether this build carries the design window's marking bridge"
    )
    manifest: Manifest | None = Field(
        default=None,
        description="id -> package + source location. The design window resolves markings "
        "against this, so it travels with the build rather than being re-derived by a caller.",
    )
    package_files: dict[str, list[str]] = Field(default_factory=dict)

    @classmethod
    def of(
        cls,
        result: AppBuildResult,
        *,
        project_id: str,
        whole: str,
        standin: bool,
        workspace: str = "",
        preview: bool = False,
        manifest: Manifest | None = None,
        package_files: dict[str, list[str]] | None = None,
    ) -> BuildFinished:
        return cls(
            project_id=project_id,
            app_url=result.app_url,
            build_version=result.build_version,
            git_sha=result.git_sha,
            whole=whole,
            summary=result.honest_summary(),
            works=result.works,
            parts_working=result.working,
            parts_needing_a_look=result.needs_look,
            parts_blocked=result.blocked,
            parts_failed=result.failed,
            remainders=_remainders(result.packages),
            element_count=result.element_count,
            files=sorted({f for package in result.packages for f in package.files}),
            total_cost_usd=result.total_cost_usd,
            standin=standin,
            workspace=workspace,
            preview=preview,
            manifest=manifest,
            package_files=package_files or {},
        )


def _remainders(packages: list[PackageBuildResult]) -> list[str]:
    """Every honest status line that is not "works" — the trust receipt's body."""
    return [p.honest_status() for p in packages if not p.works]


async def stream_full_build(
    spec: AppSpec,
    *,
    project_id: str,
    registry: ProviderRegistry,
    builder_registry: ProviderRegistry | None = None,
    sandbox: SandboxProvider | None = None,
    preview: BuildPreview | None = None,
    app_dir: Path | None = None,
    build_version: int = 1,
    max_attempts: int = 2,
    codegen_passes: int | None = None,
    close_preview: bool = False,
    shell_origin: str = "",
) -> AsyncIterator[tuple[str, BaseModel | str]]:
    """Run the whole path, yielding events as they happen.

    Events: "started" (BuildStarted), then "progress"/"package" from the
    orchestrator, then "finished" (BuildFinished).

    `builder_registry` defaults to the stand-in when the ordinary registry has no
    real model: the relay's fake provider returns digests, which produce no code
    at all, so without this the whole path would be untestable without keys.
    Layers B and C keep the ordinary registry — their fallbacks are already
    honest (a deterministic narrative, and rules).
    """
    # Layer B raises NotBuildableError on a spec that has not passed gate 1, and
    # it runs first — so a half-answered spec never reaches a workspace.
    # The run profile is the user-facing "how hard to work" setting (STRATEGY.md
    # section E): 1 means one model, run twice — generate, then self-review.
    profile = run_profile()
    passes = codegen_passes if codegen_passes is not None else profile.passes

    using_standin = builder_registry is None and registry.is_fake
    builder = builder_registry or (standin_registry() if using_standin else registry)

    layer_b = await run_layer_b(spec, registry=registry)
    whole = layer_b.whole.narrative

    layer_c = await run_layer_c(
        layer_b.architecture,
        registry=registry,
        whole=whole,
        use_judgment=not registry.is_fake,
    )
    plan = layer_c.plan

    workspace = Path(app_dir) if app_dir else prepare_workspace(project_id)

    # With data, a build can check that saving actually saves — the criteria
    # B054 had to scope out as unobservable (library/verification). Off unless
    # the flag is set, and then it is one fresh database for this build, owned
    # and discarded here.
    database: VerificationDatabase | None = None
    app_env: dict[str, str] = {}
    if verification_enabled():
        database = prepare_verification(workspace)
        app_env.update(database.env)

    # Level 2: the app is served for the design window, so it carries the
    # marking bridge. `shell_origin` is what the bridge is allowed to talk to —
    # without one it stays silent rather than broadcasting to any frame.
    # A build with no shell_origin is a delivery build and gets no bridge at all.
    if shell_origin:
        prepare_bridge(workspace)
        app_env.update(preview_env(shell_origin))

    running = preview or SandboxPreview(
        sandbox or choose_sandbox(),
        screenshot_dir=workspace.parent / f"{project_id}-shots",
        env=app_env,
        # Only when there IS a database: without one the interaction channel
        # says "I did not look" rather than failing a feature for an insert
        # that had nowhere to go.
        verify_path=database.verify_path if database else "",
    )

    yield (
        "started",
        BuildStarted(
            project_id=project_id,
            whole=whole,
            packages=plan.order,
            total=len(plan.order),
            workspace=str(workspace),
            models=profile.describe(),
        ),
    )

    result: AppBuildResult | None = None
    async for event, payload in stream_build_plan(
        plan,
        workspace,
        contracts=layer_c.prompts,
        registry=builder,
        preview=running,
        options=AppBuildOptions(
            package=BuildOptions(
                max_attempts=max_attempts,
                codegen_passes=passes,
                critique_passes=1,
            ),
            build_version=build_version,
            # Assembled parts take their look from the project's tokens.
            tokens=layer_b.architecture.design_tokens,
            # The reveal embeds the running app, so the sandbox outlives the build.
            close_preview=close_preview,
        ),
    ):
        if isinstance(payload, AppBuildResult):
            result = payload
        else:
            yield event, payload

    assert result is not None  # stream_build_plan always ends with a result

    # ~39MB per database (measured in the spike). It is build output, and the
    # next build gets a fresh one, so it goes when the build does — but only
    # after the sandbox has stopped reading it.
    if database is not None and close_preview:
        database.discard()

    # Offer what this build produced back to the library (B061).
    #
    # After the build and before the finish, because a contribution is a
    # side-effect of a delivered app and must never be the reason one is not
    # delivered — `contribute_build` swallows its own failures for the same
    # reason. Parts that CAME from the library are skipped there: they carry the
    # entry id they were assembled from.
    #
    # Skipped entirely for a preview build: a Level 2 preview is a draft the
    # user is about to mark up and change, and learning from it would fill the
    # library with things nobody kept.
    contribution: ContributionReport | None = None
    if not shell_origin:
        contribution = await contribute_build(
            plan.packages,
            result.packages,
            workspace,
            registry=builder,
            architecture=layer_b.architecture,
            project_id=project_id,
        )
        if contribution.outcomes:
            yield "library", {"summary": contribution.describe(), "added": contribution.added}

    # Derived from the source that is actually on disk, not remembered from the
    # build: the design window resolves markings against it, and a manifest that
    # drifted from the code is exactly how a marking targets the wrong package.
    file_map = file_plan(plan.packages)
    yield (
        "finished",
        BuildFinished.of(
            result,
            project_id=project_id,
            whole=whole,
            standin=using_standin,
            workspace=str(workspace),
            preview=bool(shell_origin),
            manifest=build_manifest(workspace, file_map),
            package_files=file_map,
        ),
    )
