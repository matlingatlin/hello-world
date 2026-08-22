"""Capability matrix — task type -> ranked models (PROJECT-PLAN 4.1).

Data-driven on purpose: rankings change monthly, so they live in matrix.yaml and
this module only loads, validates and selects. `top_n` returns the models the
relay runs, in order.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .provider import Vendor

DEFAULT_MATRIX_PATH = Path(__file__).with_name("matrix.yaml")


class ModelCard(BaseModel):
    """One model's metadata, as the selector and narration see it."""

    id: str
    vendor: Vendor
    context_limit: int
    input_cost_per_mtok: float
    """USD per 1M input tokens. Required, not defaulted: a card without it would
    price its input at zero, which is the bug this replaced — silently."""
    cost_per_mtok: float
    """USD per 1M OUTPUT tokens. The name predates there being two prices; it is
    left alone because the matrix file, the estimate and two stored figures all
    use it."""
    latency: str
    strength: str


class TaskRanking(BaseModel):
    description: str = ""
    ranking: list[str] = Field(default_factory=list)


class UnknownTaskError(KeyError):
    """Raised for a task type the matrix doesn't define."""


class CapabilityMatrix(BaseModel):
    models: dict[str, ModelCard]
    tasks: dict[str, TaskRanking]

    @classmethod
    def load(cls, path: Path | None = None) -> CapabilityMatrix:
        raw = yaml.safe_load((path or DEFAULT_MATRIX_PATH).read_text())
        models = {m["id"]: ModelCard(**m) for m in raw.get("models", [])}
        tasks = {name: TaskRanking(**spec) for name, spec in raw.get("tasks", {}).items()}

        for name, task in tasks.items():
            unknown = [m for m in task.ranking if m not in models]
            if unknown:
                raise ValueError(f"Task '{name}' ranks unknown models: {unknown}")
        return cls(models=models, tasks=tasks)

    @property
    def task_types(self) -> list[str]:
        return sorted(self.tasks)

    def top_n(self, task: str, n: int = 3) -> list[ModelCard]:
        """The n best models for this task, best first.

        Returns fewer than n if the task ranks fewer — the relay adapts rather
        than inventing a model that isn't ranked for the job.
        """
        ranking = self.tasks.get(task)
        if ranking is None:
            raise UnknownTaskError(
                f"Unknown task '{task}'. Known tasks: {', '.join(self.task_types)}"
            )
        return [self.models[model_id] for model_id in ranking.ranking[:n]]


@lru_cache(maxsize=1)
def default_matrix() -> CapabilityMatrix:
    """The shipped matrix, loaded once."""
    return CapabilityMatrix.load()
