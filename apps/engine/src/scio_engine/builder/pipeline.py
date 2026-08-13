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

from ..core.sandbox import SandboxProvider, choose_sandbox
from ..execution.profile import run_profile
from ..execution.provider import ProviderRegistry
from ..intake.schema import AppSpec
from ..layerb.service import run_layer_b
from ..layerc.service import run_layer_c
from .loop import BuildOptions, BuildPreview, SandboxPreview
from .orchestrate import AppBuildOptions, AppBuildResult, stream_build_plan
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

    @classmethod
    def of(
        cls,
        result: AppBuildResult,
        *,
        project_id: str,
        whole: str,
        standin: bool,
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
    running = preview or SandboxPreview(
        sandbox or choose_sandbox(),
        screenshot_dir=workspace.parent / f"{project_id}-shots",
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
            # The reveal embeds the running app, so the sandbox outlives the build.
            close_preview=close_preview,
        ),
    ):
        if isinstance(payload, AppBuildResult):
            result = payload
        else:
            yield event, payload

    assert result is not None  # stream_build_plan always ends with a result
    yield (
        "finished",
        BuildFinished.of(result, project_id=project_id, whole=whole, standin=using_standin),
    )
