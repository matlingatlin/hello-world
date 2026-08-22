"""Persist a package build as a version, with its coupling.

DATA-MODEL: code lives in git, the DB holds contracts and pointers. So a package
build is a real commit — which is what makes "you own the code, history
included" true rather than a slogan — and the manifest is committed with it so a
restored version carries its own marking→code coupling.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pydantic import BaseModel

from ..core.instrumentation import Manifest
from ..core.persistence import ManifestStore


class GitError(RuntimeError):
    """A git operation failed. The build is not persisted; say so rather than
    reporting a version that does not exist."""


def git(app_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=app_dir, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def ensure_repo(app_dir: Path) -> None:
    """A generated app is a git repo from its first commit — the user's history
    starts at the first build, not whenever they think to export."""
    if (app_dir / ".git").exists():
        return
    git(app_dir, "init", "-q")
    git(app_dir, "config", "user.email", "builder@scio.local")
    git(app_dir, "config", "user.name", "Scio builder")


def head_sha(app_dir: Path) -> str:
    """The commit the workspace is standing on, or "" if it has no history yet.

    A promotion delivers what is already committed rather than committing
    something new, so it needs to name that commit — and an empty string is the
    honest answer for a workspace nobody has persisted, where a raised error
    would only mean the same thing more loudly.
    """
    try:
        return git(app_dir, "rev-parse", "HEAD")
    except GitError:
        return ""


class PersistedBuild(BaseModel):
    build_version: int
    git_sha: str
    manifest_path: str
    files: list[str]


def persist_package_build(
    app_dir: Path,
    *,
    package_id: str,
    description: str,
    manifest: Manifest,
    files: list[str],
    build_version: int,
) -> PersistedBuild:
    """Commit the package's files plus the regenerated manifest.

    The manifest goes in the same commit deliberately: code and coupling that
    can be checked out separately will eventually be checked out separately, and
    then a marking resolves against the wrong version.
    """
    app_dir = Path(app_dir).resolve()
    ensure_repo(app_dir)

    manifest_path = ManifestStore(app_dir).save(manifest)
    git(app_dir, "add", "-A")

    status = git(app_dir, "status", "--porcelain")
    if not status:
        sha = git(app_dir, "rev-parse", "HEAD")
        return PersistedBuild(
            build_version=build_version,
            git_sha=sha,
            manifest_path=manifest_path.name,
            files=list(files),
        )

    git(app_dir, "commit", "-q", "-m", f"build({package_id}): {description}")
    sha = git(app_dir, "rev-parse", "HEAD")
    return PersistedBuild(
        build_version=build_version,
        git_sha=sha,
        manifest_path=manifest_path.name,
        files=list(files),
    )
