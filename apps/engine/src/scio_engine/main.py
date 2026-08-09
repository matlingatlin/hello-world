"""Scio engine service. Layer A only for now: schema + gate. The matrix,
multi-pass relay, and extraction land in later kickoffs (B031, 4.3)."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .intake.gate import BuildableResult, is_buildable, triggered_conditionals
from .intake.schema import AppSpec

app = FastAPI(
    title="Scio Engine",
    description="Intake layers + (later) the matrix and multi-pass relay.",
    version="0.0.1",
)


class HealthResponse(BaseModel):
    status: str = "ok"


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


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/intake/validate", response_model=ValidateResponse)
def validate_intake(spec: AppSpec) -> ValidateResponse:
    """Takes a partial AppSpec, returns the gate verdict and what's still needed."""
    result = is_buildable(spec)
    return ValidateResponse(
        result=result,
        triggered=triggered_conditionals(spec),
        still_needed=[*result.missing_core, *result.unresolved_conditionals],
    )
