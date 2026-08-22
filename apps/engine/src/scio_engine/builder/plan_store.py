"""The plan that produced an app, kept with the app.

A promotion (B070) delivers the app the user shaped in the design window
*without* regenerating it — but delivering still means judging, and judging
means the acceptance criteria these packages were written against.

Re-deriving them would be worse than expensive. Layers B and C are model calls:
run again they can produce a *different* plan, and the app on disk would then be
measured against criteria it was never built to meet. So the plan is written
into the workspace beside the code, travels with it through git, and is read
back verbatim.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from ..layerc.plan import BuildPlan

PLAN_PATH = Path(".scio") / "plan.json"


class StoredPlan(BaseModel):
    """What a later pass needs to judge this app without re-planning it."""

    plan: BuildPlan
    contracts: dict[str, str] = Field(default_factory=dict)
    whole: str = ""


def save_plan(app_dir: Path, plan: BuildPlan, contracts: dict[str, str], whole: str) -> Path:
    path = Path(app_dir) / PLAN_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(StoredPlan(plan=plan, contracts=contracts, whole=whole).model_dump_json())
    return path


def load_plan(app_dir: Path) -> StoredPlan | None:
    """The stored plan, or None when this workspace has none.

    None rather than an exception: a workspace built before plans were stored is
    a real thing that exists, and the caller decides what to do about it.
    """
    path = Path(app_dir) / PLAN_PATH
    if not path.exists():
        return None
    try:
        return StoredPlan.model_validate_json(path.read_text())
    except (ValueError, json.JSONDecodeError):
        return None
