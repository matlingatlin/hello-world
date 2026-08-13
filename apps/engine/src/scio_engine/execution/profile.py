"""The run profile — which models the relay may use, and how many passes.

docs/STRATEGY.md, section E: the model-passes setting is a user-facing control,
and **choosing 1 never means a raw single pass**. One means one *model*, run
twice: generate, then review its own work. More means the best model for the
task first, then the next ones to review and complement, finishing back in the
best. The relay already implements that shape (B031); this is the knob.

Until the Settings UI exists (B049), the knob is environment configuration —
which is also what makes a cheap, deterministic end-to-end run possible:

    SCIO_ONLY_PROVIDER=anthropic
    SCIO_MODEL=claude-opus-5
    SCIO_MODEL_PASSES=1

Note what this is NOT: it does not change what `passes=1` means inside the
relay, and it does not silently double every internal call. A critique asking
for one pass still gets one. The doubling belongs to the *setting*, which is
about how hard to work on a build.
"""

from __future__ import annotations

import os

from pydantic import BaseModel

from .matrix import CapabilityMatrix, ModelCard, TaskRanking, default_matrix
from .provider import Vendor

SETTING_ENV = "SCIO_MODEL_PASSES"
MODEL_ENV = "SCIO_MODEL"
PROVIDER_ENV = "SCIO_ONLY_PROVIDER"

MAX_SETTING = 4
"""Matches the relay's hard cap (MAX_PASSES). A setting above it buys little
and spends a lot."""


def relay_passes(setting: int) -> int:
    """Turn the user-facing setting into relay passes.

    1 -> 2: the same model generates, then reviews itself. `plan_models` puts
    the best model in both the first and last slot, so a one-model matrix at two
    passes is exactly "generate, then self-review".
    """
    if setting <= 1:
        return 2
    return min(setting, MAX_SETTING)


def single_model_matrix(
    model_id: str, *, vendor: Vendor = Vendor.anthropic, base: CapabilityMatrix | None = None
) -> CapabilityMatrix:
    """A matrix in which every task ranks exactly one model.

    Built from the shipped matrix when the model is already in it (keeping its
    real cost and context limit), otherwise from a minimal card — so an operator
    can point at a model the matrix has not caught up with yet without editing
    YAML first.
    """
    source = base or default_matrix()
    card = source.models.get(model_id) or ModelCard(
        id=model_id,
        vendor=vendor,
        context_limit=200_000,
        cost_per_mtok=25.0,
        latency="medium",
        strength=f"Operator-selected model ({model_id})",
    )
    return CapabilityMatrix(
        models={card.id: card},
        tasks={
            name: TaskRanking(description=task.description, ranking=[card.id])
            for name, task in source.tasks.items()
        },
    )


class RunProfile(BaseModel):
    """What the engine should actually run, this deployment."""

    model_config = {"arbitrary_types_allowed": True}

    matrix: CapabilityMatrix
    passes: int
    setting: int
    only_model: str = ""

    @property
    def single_model(self) -> bool:
        return bool(self.only_model)

    def describe(self) -> str:
        if self.single_model:
            return (
                f"{self.only_model} only, {self.passes} passes "
                f"(setting {self.setting}: one model, generate then self-review)"
            )
        return f"matrix ranking, {self.passes} passes (setting {self.setting})"


def _setting_from_env() -> int:
    raw = os.getenv(SETTING_ENV, "")
    try:
        return int(raw) if raw else MAX_SETTING
    except ValueError:
        return MAX_SETTING


def run_profile(matrix: CapabilityMatrix | None = None) -> RunProfile:
    """Read the profile from the environment.

    Unset means the full relay over the ranked matrix — the default the product
    ships with. Setting a model narrows it to that one model everywhere.
    """
    setting = _setting_from_env()
    model_id = os.getenv(MODEL_ENV, "").strip()
    vendor_name = os.getenv(PROVIDER_ENV, "anthropic").strip().lower()
    vendor = Vendor(vendor_name) if vendor_name in set(Vendor) else Vendor.anthropic

    base = matrix or default_matrix()
    if not model_id:
        return RunProfile(matrix=base, passes=relay_passes(setting), setting=setting)

    return RunProfile(
        matrix=single_model_matrix(model_id, vendor=vendor, base=base),
        passes=relay_passes(setting),
        setting=setting,
        only_model=model_id,
    )


def active_matrix() -> CapabilityMatrix:
    """The matrix the relay uses when a caller does not name one.

    Read per call rather than cached: the profile is environment configuration,
    and an operator who exports SCIO_MODEL and restarts expects it to take
    effect without also having to reason about a cache.
    """
    return run_profile().matrix
