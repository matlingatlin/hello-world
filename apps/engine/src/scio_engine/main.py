"""Scio engine service.

Layer A (intake schema + gate) and the execution machinery (provider abstraction,
capability matrix, multi-pass relay). Requirements extraction, Layer B's
architecture logic, and codegen build on top of this — later kickoffs.
"""

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import build_registry, use_fake_providers
from .execution.matrix import UnknownTaskError, default_matrix
from .execution.narration import narrate
from .execution.provider import ProviderError
from .execution.relay import (
    BudgetExceeded,
    RelayOptions,
    RelayResult,
    clamp_passes,
    stream_relay,
)
from .intake.conversation import IntakeMessage
from .intake.gate import BuildableResult, is_buildable, triggered_conditionals
from .intake.schema import AppSpec
from .intake.service import IntakeStep, run_intake_step
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
    return HealthResponse(providers="fake" if use_fake_providers() else "real")


@app.post("/intake/validate", response_model=ValidateResponse)
def validate_intake(spec: AppSpec) -> ValidateResponse:
    """Takes a partial AppSpec, returns the gate verdict and what's still needed."""
    result = is_buildable(spec)
    return ValidateResponse(
        result=result,
        triggered=triggered_conditionals(spec),
        still_needed=[*result.missing_core, *result.unresolved_conditionals],
    )


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
        registry=build_registry(),
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
