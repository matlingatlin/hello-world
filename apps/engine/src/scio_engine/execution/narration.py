"""Transparency narration (PROJECT-PLAN 4.1).

The user-facing sentence explaining what the engine is about to do — Scio's
signature move: say which models will run, in what order, and why. Deterministic
text so the UI can show it before the first token arrives.
"""

from __future__ import annotations

from .matrix import ModelCard


def narrate(task: str, models: list[ModelCard], passes: int) -> str:
    """Describe the planned relay in the user's language.

    The relay cycles through the ranked models and finishes back in the best
    one, so the narration mirrors exactly what `run_relay` will do.
    """
    if not models:
        return "I have no model available for this task."

    readable_task = task.replace("_", " ")
    if passes <= 1:
        return f"I'll run this once, in {models[0].id} — the best model for {readable_task}."

    plan = plan_models(models, passes)
    parts = [f"I'll run this prompt {passes} times — first in {plan[0].id}"]
    for i, model in enumerate(plan[1:], start=1):
        is_final = i == len(plan) - 1
        if is_final:
            parts.append(f"then a final pass back in {model.id}")
        else:
            parts.append(
                f"then take that result into {model.id} to review, rewrite and complement"
            )
    return "; ".join(parts) + "."


def plan_models(models: list[ModelCard], passes: int) -> list[ModelCard]:
    """Which model runs each pass: best first, then down the ranking, then back
    to the best for the final pass (PROJECT-PLAN 4.2)."""
    if not models:
        return []
    if passes <= 1:
        return [models[0]]

    plan: list[ModelCard] = [models[0]]
    for i in range(1, passes - 1):
        plan.append(models[i % len(models)])
    plan.append(models[0])  # final pass back in the best model
    return plan
