"""Layer C end to end: architecture -> validated build plan.

Deterministic decomposition first, LLM judgment only for what the rules left
ambiguous, then contracts, then validation — in that order, so a plan error is
caught before the builder ever runs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from ..layerb.architecture import Architecture
from ..layerb.playbook import Playbook, default_playbook
from .contract import assemble_contract, contract_prompt
from .decompose import build_plan, topological_order
from .judgment import GroupingAdvice, advise_grouping, apply_advice
from .plan import BuildPlan
from .validate import PlanValidation, validate_plan


class LayerCResult(BaseModel):
    plan: BuildPlan
    validation: PlanValidation
    grouping_advice: GroupingAdvice = Field(default_factory=GroupingAdvice)
    prompts: dict[str, str] = Field(
        default_factory=dict,
        description="package id -> the assembled contract prompt the builder will run",
    )


async def run_layer_c(
    arch: Architecture,
    *,
    registry: ProviderRegistry,
    whole: str = "",
    playbook: Playbook | None = None,
    use_judgment: bool = True,
) -> LayerCResult:
    """Plan the build. `use_judgment=False` keeps it fully deterministic."""
    book = playbook or default_playbook()
    plan = build_plan(arch)

    advice = GroupingAdvice()
    if use_judgment:
        advice = await advise_grouping(plan, registry=registry)
        if advice.applied:
            apply_advice(plan, advice, arch)
            plan.order = topological_order(plan.packages)
            plan.graph = {p.id: list(p.dependencies) for p in plan.packages}

    for package in plan.packages:
        assemble_contract(package, plan, arch, whole=whole, playbook=book)

    validation = validate_plan(plan, arch)
    prompts = {p.id: contract_prompt(p, plan, arch) for p in plan.ordered()}

    return LayerCResult(
        plan=plan,
        validation=validation,
        grouping_advice=advice,
        prompts=prompts,
    )
