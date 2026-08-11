"""LLM judgment for genuinely ambiguous grouping (docs/LAYER-C.md).

The deterministic decomposition is the default and the fallback. This module
only asks a model when the rules produced something a human planner would
question — today: operations the architecture couldn't attach to any entity,
which land in a "general" bucket. Everything else is rules, because rules are
reproducible and free.

Grounded: the model sees the package list and the loose operations, and may only
answer with an existing package id.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from ..layerb.architecture import Architecture
from .plan import BuildPackage, BuildPlan, PackageKind

GROUPING_SYSTEM = """You are Scio's build planner, deciding where loose pieces of \
work belong.

Rules:
- Answer only with package ids from the list you are given, one per line, in the \
form `operation -> package_id`.
- If nothing fits, answer `operation -> keep` for that operation.
- No explanation, no other text."""


class GroupingAdvice(BaseModel):
    """What the model suggested, and whether it was used."""

    consulted: bool = False
    applied: bool = False
    moves: dict[str, str] = Field(default_factory=dict)  # operation name -> package id
    models_used: list[str] = Field(default_factory=list)


def ambiguous_operations(plan: BuildPlan) -> list[str]:
    """Operations the deterministic pass couldn't attach to an entity."""
    general = plan.get("pkg_feature_general")
    if general is None:
        return []
    return [node.name for node in general.architecture_slice if node.kind == "operation"]


def _candidate_packages(plan: BuildPlan) -> list[BuildPackage]:
    return [
        p
        for p in plan.packages
        if p.kind is PackageKind.feature and p.id != "pkg_feature_general"
    ]


def _parse(text: str, valid_ids: set[str], operations: set[str]) -> dict[str, str]:
    moves: dict[str, str] = {}
    for line in text.splitlines():
        if "->" not in line:
            continue
        left, right = (part.strip() for part in line.split("->", 1))
        if left in operations and right in valid_ids:
            moves[left] = right
    return moves


async def advise_grouping(
    plan: BuildPlan,
    *,
    registry: ProviderRegistry,
    passes: int = 1,
) -> GroupingAdvice:
    """Ask where loose operations belong. Never fails the plan: any error, and
    the deterministic grouping stands."""
    loose = ambiguous_operations(plan)
    candidates = _candidate_packages(plan)
    if not loose or not candidates:
        return GroupingAdvice()

    listing = "\n".join(f"- {p.id}: {p.goal}" for p in candidates)
    prompt = (
        "These build packages exist:\n"
        f"{listing}\n\n"
        "These operations were not attached to any entity:\n"
        + "\n".join(f"- {name}" for name in loose)
        + "\n\nWhere does each belong?"
    )

    try:
        result = await run_relay(
            "architecture",
            prompt,
            registry=registry,
            options=RelayOptions(passes=passes, system=GROUPING_SYSTEM, temperature=0.0),
        )
    except Exception:
        return GroupingAdvice(consulted=True)

    moves = _parse(result.final_text, {p.id for p in candidates}, set(loose))
    return GroupingAdvice(
        consulted=True,
        applied=bool(moves),
        moves=moves,
        models_used=result.models,
    )


def apply_advice(plan: BuildPlan, advice: GroupingAdvice, arch: Architecture) -> None:
    """Move the advised operations into their packages, in place.

    A screen that exists only to serve a moved operation travels with it —
    otherwise it would be stranded in a package that no longer builds anything
    it needs. The general package is dropped only once it is genuinely empty, so
    anything left behind stays visible to validation.
    """
    if not advice.moves:
        return
    general = plan.get("pkg_feature_general")
    if general is None:
        return

    for operation, target_id in advice.moves.items():
        target = plan.get(target_id)
        if target is None:
            continue

        moved = [
            n for n in general.architecture_slice if n.kind == "operation" and n.name == operation
        ]
        if not moved:
            continue

        # Screens whose every operation is this one move along with it.
        for node in list(general.architecture_slice):
            if node.kind != "screen":
                continue
            screen = next(
                (s for s in arch.screens_routing.screens if s.route == node.name), None
            )
            if screen and screen.operations and set(screen.operations) == {operation}:
                moved.append(node)
                target.interface.routes = sorted({*target.interface.routes, node.name})

        general.architecture_slice = [n for n in general.architecture_slice if n not in moved]
        target.architecture_slice.extend(moved)
        target.interface.operations = sorted({*target.interface.operations, operation})

    if not general.architecture_slice:
        plan.packages = [p for p in plan.packages if p.id != general.id]
        plan.order = [pid for pid in plan.order if pid != general.id]
        plan.graph.pop(general.id, None)
