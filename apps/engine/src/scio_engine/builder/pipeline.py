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
from ..execution.relay import Spend
from ..intake.schema import AppSpec
from ..layerb.service import run_layer_b
from ..layerc.plan import BuildPlan
from ..layerc.service import run_layer_c
from ..library.contribute import ContributionReport, contribute_build
from ..library.verification import VerificationDatabase, verification_enabled
from ..library.verification import prepare as prepare_verification
from .file_plan import file_plan
from .loop import BuildOptions, BuildPreview, SandboxPreview
from .orchestrate import (
    AppBuildOptions,
    AppBuildResult,
    stream_build_plan,
    stream_verification,
)
from .plan_store import load_plan, save_plan
from .preview_bridge import prepare as prepare_bridge
from .preview_bridge import preview_env
from .standin import standin_registry
from .workspace import WorkspaceUnavailable, prepare_workspace


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
    total_tokens: int = 0
    model: str = Field(
        default="",
        description="Which model actually wrote this build. Recorded with the spend, because "
        "a cost is only re-checkable if you know what rate card it came from.",
    )
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
    routes: list[str] = Field(
        default_factory=list,
        description="Every page this app has, from the plan that built it. The design window "
        "used to show whichever one the app opens on and offer no way to reach the others — "
        "so half a booking app could not be marked up at all (B069).",
    )

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
        model: str = "",
        routes: list[str] | None = None,
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
            remainders=_remainders(result),
            element_count=result.element_count,
            files=sorted({f for package in result.packages for f in package.files}),
            total_cost_usd=result.total_cost_usd,
            total_tokens=result.total_tokens,
            model=model,
            standin=standin,
            workspace=workspace,
            preview=preview,
            manifest=manifest,
            package_files=package_files or {},
            routes=routes or [],
        )


def _routes_of(plan: BuildPlan) -> list[str]:
    """Every page the plan says this app has, in a stable order.

    Read off the packages' interfaces rather than the architecture, because the
    plan is what actually got built — a screen Layer B imagined and Layer C
    never scheduled is not a page anyone can open. "/" leads, then the rest
    alphabetically: the app opens on it, so it is where the user already is.
    """
    routes = {route for package in plan.packages for route in package.interface.routes}
    ordered = sorted(r for r in routes if r != "/")
    return (["/"] if "/" in routes else []) + ordered


def _remainders(result: AppBuildResult) -> list[str]:
    """Every honest status line that is not "works" — the trust receipt's body.

    App-wide findings are included, and named as such: a compile error in a file
    no package owns belongs to the app, and dropping it because it has no part
    to sit under is how "5 of 5 parts work" gets printed over an app that does
    not build.
    """
    lines = [p.honest_status() for p in result.packages if not p.works]
    lines += [f"the app: {r.as_line()}" for r in result.app_remainders]
    lines += [f"Not verified: {item}" for item in result.app_unjudged]
    return lines


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
    budget_usd: float | None = None,
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

    # The plan travels with the app. A promotion judges this workspace later
    # without re-running Layers B and C — which would cost money and, worse,
    # could produce a different plan than the one the code was written to.
    save_plan(workspace, plan, layer_c.prompts, whole)

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
                # ONE accumulator for the whole build, not a number handed to
                # each call. The first attempt at this passed `budget_usd` into
                # every codegen and every critique, which granted the ceiling
                # once per call — a seven-package build makes at least fourteen,
                # so a $3.76 "build ceiling" licensed nearer $50.
                spend=Spend(ceiling_usd=budget_usd),
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
            model=profile.only_model,
            routes=_routes_of(plan),
        ),
    )


async def stream_promotion(
    *,
    project_id: str,
    app_dir: Path,
    registry: ProviderRegistry,
    build_version: int = 1,
    sandbox: SandboxProvider | None = None,
    preview: BuildPreview | None = None,
    close_preview: bool = False,
    budget_usd: float | None = None,
) -> AsyncIterator[tuple[str, BaseModel | str]]:
    """Deliver the app the user shaped in the design window — as it stands.

    "Build it" used to run the whole path again on a fresh workspace, which
    deleted the directory the design window had been committing into. Two things
    died with it, and the smaller one is the one that was noticed: the version
    history the design panel offers to return to. The larger one is every change
    the user made. They had spent the session marking elements and describing
    what should be different, and the delivery build regenerated the app from
    the spec — which never contained any of it.

    So a promotion regenerates nothing. It takes the workspace as it is, serves
    it *without* the preview flag (the delivered app carries no bridge), and
    runs the same gates over it that a fresh build would, using the plan that
    was stored with the app. It emits the same events, so the build view needs
    to know nothing about any of this.
    """
    workspace = Path(app_dir)
    if not workspace.exists():
        raise WorkspaceUnavailable(f"there is no workspace at {workspace}")

    stored = load_plan(workspace)
    if stored is None:
        # Never silently fall back to a rebuild: that is the data loss this
        # exists to prevent, and it would be invisible to the person it happens
        # to. The caller decides, and the honest answer to them is "not this
        # workspace".
        raise WorkspaceUnavailable(
            f"{workspace} carries no build plan, so what is in it cannot be judged "
            "against what it was meant to do. Build this project again from its spec."
        )

    plan = stored.plan
    profile = run_profile()

    # The same choice the build made, for the same reason: with no real key the
    # fake provider answers a critique with a digest, `parse_critique` cannot
    # read it, and an unreadable verdict is a failure. Judging a promotion with
    # the ordinary registry therefore downgraded parts that had *passed* minutes
    # earlier — the first free-path click-through went "5 of 5 parts work" at
    # the preview and "3 of 5" at the delivery, on files nobody had touched.
    using_standin = registry.is_fake
    judge = standin_registry() if using_standin else registry

    database: VerificationDatabase | None = None
    app_env: dict[str, str] = {}
    if verification_enabled():
        database = prepare_verification(workspace)
        app_env.update(database.env)

    # No `prepare_bridge`, no `preview_env`: this is the delivery, and the
    # delivered app is the one the user owns rather than the one we instrument.
    running = preview or SandboxPreview(
        sandbox or choose_sandbox(),
        screenshot_dir=workspace.parent / f"{project_id}-shots",
        env=app_env,
        verify_path=database.verify_path if database else "",
    )

    yield (
        "started",
        BuildStarted(
            project_id=project_id,
            whole=stored.whole,
            packages=plan.order,
            total=len(plan.order),
            workspace=str(workspace),
            models=profile.describe(),
        ),
    )

    result: AppBuildResult | None = None
    async for event, payload in stream_verification(
        plan,
        workspace,
        registry=judge,
        preview=running,
        options=AppBuildOptions(
            package=BuildOptions(critique_passes=1, spend=Spend(ceiling_usd=budget_usd)),
            build_version=build_version,
            close_preview=close_preview,
        ),
    ):
        if isinstance(payload, AppBuildResult):
            result = payload
        else:
            yield event, payload

    assert result is not None  # stream_verification always ends with a result

    if database is not None and close_preview:
        database.discard()

    file_map = file_plan(plan.packages)
    yield (
        "finished",
        BuildFinished.of(
            result,
            project_id=project_id,
            whole=stored.whole,
            standin=using_standin,
            workspace=str(workspace),
            preview=False,
            manifest=build_manifest(workspace, file_map),
            package_files=file_map,
            model=profile.only_model,
            routes=_routes_of(plan),
        ),
    )
