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
from .intake.gate import BuildableResult, is_buildable, triggered_conditionals
from .intake.schema import AppSpec

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
