"""Scio engine service.

Layer A (intake schema + gate) and the execution machinery (provider abstraction,
capability matrix, multi-pass relay). Requirements extraction, Layer B's
architecture logic, and codegen build on top of this — later kickoffs.
"""

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .builder.pipeline import stream_full_build
from .builder.standin import standin_registry
from .builder.workspace import WorkspaceUnavailable
from .config import build_registry, use_fake_providers
from .core.manifest_builder import build_manifest
from .design import ChangeBatch, DesignChangeResult, RestoreResult, apply_change, restore_version
from .estimate import BuildEstimate, estimate_plan
from .execution.matrix import UnknownTaskError, default_matrix
from .execution.narration import narrate
from .execution.profile import run_profile
from .execution.provider import ProviderError
from .execution.relay import (
    BudgetExceeded,
    RelayOptions,
    RelayResult,
    clamp_passes,
    stream_relay,
)
from .intake.conversation import IntakeMessage
from .intake.correction import (
    CorrectionError,
    CorrectionResult,
    FieldCorrection,
    correct_field,
)
from .intake.gate import BuildableResult, is_buildable, triggered_conditionals
from .intake.schema import AppSpec
from .intake.service import IntakeStep, run_intake_step
from .intake.standin import intake_standin_registry
from .layerb.architecture import Architecture
from .layerb.service import LayerBResult, NotBuildableError, run_layer_b
from .layerc.service import LayerCResult, run_layer_c

app = FastAPI(
    title="Scio Engine",
    description="Intake layers + the capability matrix and multi-pass relay.",
    version="0.0.2",
)


class HealthResponse(BaseModel):
    status: str = "ok"
    providers: str = Field(description="'fake' when no API keys are configured")
    profile: str = Field(
        default="", description="Which models will run, and how many passes (SCIO_MODEL et al.)"
    )
    builder: str = Field(
        default="",
        description="'standin' when no real model is available to write code, else 'model'",
    )


class ValidateResponse(BaseModel):
    """The is_buildable result plus what the wizard still needs to ask."""

    result: BuildableResult
    triggered: list[str] = Field(
        default_factory=list, description="All conditional branches the answers triggered"
    )
    still_needed: list[str] = Field(
        default_factory=list,
        description="Missing core fields + triggered-but-unresolved conditionals",
    )


class GenerateRequest(BaseModel):
    task: str = Field(description="Task type from the capability matrix, e.g. 'codegen'")
    prompt: str
    options: RelayOptions = Field(default_factory=RelayOptions)


class PlanResponse(BaseModel):
    """What the relay would do, without running it."""

    task: str
    models: list[str]
    passes: int
    narration: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Says plainly what this engine would actually do if asked to build.

    The operator's first check before a real run: if this still reports `fake`
    and `standin`, no key reached the process and the build will produce
    placeholder code.
    """
    fake = use_fake_providers()
    return HealthResponse(
        providers="fake" if fake else "real",
        profile=run_profile().describe(),
        builder="standin" if fake else "model",
    )


@app.post("/intake/validate", response_model=ValidateResponse)
def validate_intake(spec: AppSpec) -> ValidateResponse:
    """Takes a partial AppSpec, returns the gate verdict and what's still needed."""
    result = is_buildable(spec)
    return ValidateResponse(
        result=result,
        triggered=triggered_conditionals(spec),
        still_needed=[*result.missing_core, *result.unresolved_conditionals],
    )


class CorrectFieldRequest(BaseModel):
    """One hand correction to the working spec."""

    spec: AppSpec
    correction: FieldCorrection


@app.post("/intake/correct", response_model=CorrectionResult)
def correct_intake_field(req: CorrectFieldRequest) -> CorrectionResult:
    """Correct a field the wizard filed wrongly, and re-run Layer A's gate.

    Two things come back that a plain write would not give you: what the
    correction OPENED (two roles trigger role_permissions; sensitive data
    triggers compliance), and a gate verdict computed over the corrected spec.
    A correction is recorded as `stated` with a provenance mark, and extraction
    will not overwrite it afterwards — the conversation still contains the
    sentence that was misfiled.
    """
    try:
        return correct_field(req.spec, req.correction)
    except CorrectionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class IntakeStepRequest(BaseModel):
    """The conversation so far, plus whatever the spec already holds."""

    messages: list[IntakeMessage] = Field(default_factory=list)
    spec: AppSpec | None = Field(
        default=None, description="The spec as it stands; omit on the first turn"
    )
    extraction_passes: int = Field(default=2, description="Relay passes for extraction (1-4)")
    question_passes: int = Field(default=1, description="Relay passes for the question (1-4)")


@app.post("/intake/step", response_model=IntakeStep)
async def intake_step(req: IntakeStepRequest) -> IntakeStep:
    """One turn of gate 1: extract what was said, then ask what is still missing.

    Returns the updated spec, whether it is buildable, the next question (null
    once it is), and any contradiction the answers contain — surfaced as a
    question rather than resolved for the user.
    """
    return await run_intake_step(
        req.messages,
        req.spec,
        # Without keys the extractor gets a digest back and records nothing, so
        # the wizard asks the same question forever and gate 1 never closes —
        # found by the first local click-through. The stand-in files each answer
        # under the question that was asked, which is enough to finish.
        registry=intake_standin_registry() if use_fake_providers() else build_registry(),
        extraction_passes=req.extraction_passes,
        question_passes=req.question_passes,
    )


class ArchitectureRequest(BaseModel):
    spec: AppSpec
    whole_passes: int = Field(
        default=2, description="Relay passes for the whole narrative (1-4)"
    )


@app.post("/architecture", response_model=LayerBResult)
async def architecture(req: ArchitectureRequest) -> LayerBResult:
    """Layer B: a buildable spec in, the whole + architecture graph + playbook +
    validation out. Rejects a spec that hasn't passed Layer A's gate — running
    Layer B on an incomplete spec would only produce a confident wrong answer."""
    try:
        return await run_layer_b(
            req.spec, registry=build_registry(), whole_passes=req.whole_passes
        )
    except NotBuildableError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Spec is not buildable yet — finish the wizard first.",
                "missing_core": exc.result.missing_core,
                "unresolved_conditionals": exc.result.unresolved_conditionals,
                "contradictions": [c.model_dump() for c in exc.result.contradictions],
            },
        ) from exc


class PlanRequest(BaseModel):
    architecture: Architecture
    whole: str = Field(default="", description="The approved whole, for each package's 'why'")
    use_judgment: bool = Field(
        default=True,
        description="Consult the relay for genuinely ambiguous grouping; false stays deterministic",
    )


class EstimateRequest(BaseModel):
    architecture: Architecture
    use_judgment: bool = Field(
        default=False,
        description="Estimating never needs judgment; kept so a caller can match /plan exactly",
    )


@app.post("/estimate", response_model=BuildEstimate)
async def estimate(req: EstimateRequest) -> BuildEstimate:
    """What the base build would cost and take. Deterministic and free.

    Pricing must never cost a model call: a spec is priced every time someone
    finishes the wizard or revisits the review screen, and most specs are priced
    far more often than they are built.
    """
    result = await run_layer_c(
        req.architecture,
        registry=build_registry(),
        use_judgment=req.use_judgment,
    )
    return result.estimate or estimate_plan(result.plan)


@app.post("/plan", response_model=LayerCResult)
async def plan(req: PlanRequest) -> LayerCResult:
    """Layer C: a Layer B architecture in, a validated build plan out — ordered,
    contract-bearing packages with their assembled prompts."""
    return await run_layer_c(
        req.architecture,
        registry=build_registry(),
        whole=req.whole,
        use_judgment=req.use_judgment,
    )


class BuildRequest(BaseModel):
    spec: AppSpec
    project_id: str = Field(default="project", description="Names the workspace directory")
    build_version: int = Field(default=1, description="The version number to persist as")
    max_attempts: int = Field(default=2, description="Vision-loop attempts per package")
    shell_origin: str = Field(
        default="",
        description="Level 2 only: the design window's origin. Set it and the build carries "
        "the marking bridge, pinned to that origin. Empty means a delivery build, which "
        "has no bridge at all.",
    )


@app.post("/build")
async def build(req: BuildRequest) -> StreamingResponse:
    """The whole path: an approved spec in, a running app out, streamed.

    Events: `started` (the plan and the whole), then `progress`/`package` as each
    part finishes, then `finished` (the running URL and the honest status).
    Errors arrive as an `error` event rather than a severed stream, so the build
    view can show them where the progress was.

    Without keys this builds with the stand-in (see builder/standin.py): it
    proves the pipeline, not the quality of the code.
    """

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for event, payload in stream_full_build(
                req.spec,
                project_id=req.project_id,
                registry=build_registry(),
                build_version=req.build_version,
                max_attempts=req.max_attempts,
                shell_origin=req.shell_origin,
            ):
                if isinstance(payload, str):
                    yield _sse(event, json.dumps({"text": payload}))
                else:
                    yield _sse(event, payload.model_dump_json())
        except NotBuildableError as exc:
            yield _sse("error", json.dumps({"type": "not_buildable", "message": str(exc)}))
        except WorkspaceUnavailable as exc:
            yield _sse("error", json.dumps({"type": "workspace_unavailable", "message": str(exc)}))
        except Exception as exc:  # a build must never sever the stream silently
            yield _sse("error", json.dumps({"type": "build_failed", "message": str(exc)}))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class DesignChangeRequest(BaseModel):
    """A batch of markings from the design window, plus where the app lives."""

    app_dir: str = Field(description="The workspace the preview is running from")
    spec: AppSpec = Field(description="The approved spec — what a conflict is measured against")
    batch: ChangeBatch
    package_files: dict[str, list[str]] = Field(
        default_factory=dict, description="package -> files, from the build that produced it"
    )
    passes: int = Field(default=1, description="Relay passes per changed package (1-4)")
    allowances: list[str] = Field(
        default_factory=list,
        description="Conflicts the user has already answered yes to, quoted by the exact "
        "`spec_says` the question used. A spec change the user made in writing, not a switch.",
    )


@app.post("/design/change", response_model=DesignChangeResult)
async def design_change(req: DesignChangeRequest) -> DesignChangeResult:
    """Apply a batch of markings to ONLY the packages they touch.

    Three outcomes, and the middle one is the point:

    - **applied** — the affected packages were regenerated, each proven isolated
      and re-verified for instrumentation. Everything else is byte-identical.
    - **conflicts** — something in the batch argues with the approved spec. It is
      returned as a question and NOTHING is built; the user decides.
    - **unaddressable** — a marking landed on an element with no `data-scio-id`.
      That marking is named and skipped; the others still apply.
    """
    app_dir = Path(req.app_dir)
    if not app_dir.exists():
        raise HTTPException(status_code=404, detail=f"no workspace at {req.app_dir}")

    architecture = (await run_layer_b(req.spec, registry=build_registry())).architecture
    package_files = req.package_files or None
    manifest = build_manifest(app_dir, package_files or {})

    registry = build_registry()
    return await apply_change(
        app_dir,
        req.batch,
        manifest=manifest,
        architecture=architecture,
        # Without keys the relay returns digests, which contain no code — the
        # stand-in builder is what makes the free path produce files at all.
        registry=standin_registry() if registry.is_fake else registry,
        package_files=package_files,
        passes=req.passes,
        allowances=req.allowances,
    )


class DesignRestoreRequest(BaseModel):
    """Go back to an earlier design version."""

    app_dir: str = Field(description="The workspace the preview is running from")
    git_sha: str = Field(description="The commit that design version recorded")
    package_files: dict[str, list[str]] = Field(
        default_factory=dict, description="package -> files, from the build that produced it"
    )


@app.post("/design/restore", response_model=RestoreResult)
def design_restore(req: DesignRestoreRequest) -> RestoreResult:
    """Put an earlier design version's code back, or say why it cannot go back.

    A restore is a write, so it goes through the same instrumentation guardrail
    as a change: the manifest is rebuilt from the restored source and verified,
    and a tree that does not verify is undone rather than served. Returning to a
    preview where marking silently lands in the wrong package would be worse
    than not returning at all.
    """
    app_dir = Path(req.app_dir)
    if not app_dir.exists():
        raise HTTPException(status_code=404, detail=f"no workspace at {req.app_dir}")
    return restore_version(app_dir, req.git_sha, package_files=req.package_files)


@app.get("/matrix/tasks")
def matrix_tasks() -> dict[str, list[str]]:
    """The task types the matrix knows, and the models ranked for each."""
    matrix = default_matrix()
    return {task: [m.id for m in matrix.top_n(task)] for task in matrix.task_types}


@app.post("/generate/plan", response_model=PlanResponse)
def generate_plan(req: GenerateRequest) -> PlanResponse:
    """Matrix selection + narration only — what would run, and in what order."""
    matrix = default_matrix()
    try:
        models = matrix.top_n(req.task)
    except UnknownTaskError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    passes = clamp_passes(req.options.passes, len(models))
    return PlanResponse(
        task=req.task,
        models=[m.id for m in models],
        passes=passes,
        narration=narrate(req.task, models, passes),
    )


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


@app.post("/generate")
async def generate(req: GenerateRequest) -> StreamingResponse:
    """Run the matrix selection + multi-pass relay, streaming each pass as SSE.

    Events: `narration`, then one `pass` per relay pass (with the model that ran
    it), then `result`. Errors arrive as an `error` event rather than a broken
    stream, so the UI can show them in place.
    """
    matrix = default_matrix()
    try:
        matrix.top_n(req.task)
    except UnknownTaskError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    registry = build_registry()

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for event, payload in stream_relay(
                req.task, req.prompt, registry=registry, matrix=matrix, options=req.options
            ):
                if isinstance(payload, str):
                    yield _sse(event, json.dumps({"text": payload}))
                else:
                    yield _sse(event, payload.model_dump_json())
        except BudgetExceeded as exc:
            yield _sse("error", json.dumps({"type": "budget_exceeded", "message": str(exc)}))
        except ProviderError as exc:
            yield _sse("error", json.dumps({"type": "provider_error", "message": str(exc)}))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


__all__ = ["app", "RelayResult"]
