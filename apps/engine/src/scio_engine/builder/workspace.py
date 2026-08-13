"""Where a generated app lives while it is being built and previewed.

The sandbox refuses to start without installed dependencies — the spike proved
why: a dev server that installs on first boot dies mid-startup. So a workspace is
scaffolded from a prepared directory (package.json, tsconfig, and node_modules)
before the build begins, and the build only ever writes application files into it.

In production this is an ACA session with a prepared image (ADR-0005). Locally it
is a directory plus a symlink, configured by environment so nothing here is
hard-coded to one machine.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

SCAFFOLD_FILES = ("package.json", "next.config.js", "tsconfig.json", "next-env.d.ts")

ENGINE_ROOT = Path(__file__).resolve().parents[3]


class WorkspaceUnavailable(RuntimeError):
    """No runnable workspace can be prepared here.

    Raised rather than quietly building something that cannot run: a build the
    user cannot see is not a build, and pretending otherwise is the dishonesty
    the whole product is trying to avoid.
    """


def default_scaffold_dir() -> Path | None:
    """The prepared app skeleton, from SCIO_SCAFFOLD_DIR or the local spike app."""
    configured = os.getenv("SCIO_SCAFFOLD_DIR")
    if configured:
        path = Path(configured).expanduser().resolve()
        return path if path.exists() else None
    # apps/engine -> apps -> the repo root, where spikes/ lives.
    fallback = ENGINE_ROOT.parents[1] / "spikes" / "sandbox-marking" / "example-app"
    return fallback if fallback.exists() else None


def workspace_root() -> Path:
    return Path(os.getenv("SCIO_WORKSPACE_ROOT", str(ENGINE_ROOT / "out" / "projects"))).resolve()


def prepare_workspace(project_id: str, *, fresh: bool = True) -> Path:
    """A directory with dependencies in place, ready for the sandbox to serve."""
    scaffold = default_scaffold_dir()
    if scaffold is None:
        raise WorkspaceUnavailable(
            "No app scaffold available. Set SCIO_SCAFFOLD_DIR to a directory with "
            "package.json and installed node_modules — the sandbox cannot install "
            "dependencies during startup."
        )
    if not (scaffold / "node_modules").exists():
        raise WorkspaceUnavailable(
            f"{scaffold} has no node_modules. Install dependencies there first; a dev "
            "server that installs on first boot dies mid-startup (seen in the spike)."
        )

    target = workspace_root() / project_id
    if fresh and target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for name in SCAFFOLD_FILES:
        source = scaffold / name
        if source.exists():
            shutil.copy2(source, target / name)

    modules = target / "node_modules"
    if not modules.exists():
        # A symlink, not a copy: 400MB per project would be absurd, and the
        # generated app never writes into node_modules.
        modules.symlink_to(scaffold / "node_modules")

    return target
