"""Going back to an earlier design version.

A version list you cannot return to is decoration. The whole reason someone is
willing to keep marking things is that the previous answer is still there, so
"return to this version" has to actually put that code back on disk — and the
preview has to still be markable afterwards.

Two decisions here are load-bearing:

1. **The restore moves history forward, it does not rewrite it.** `git read-tree
   -u --reset` puts the old tree in the index and the working tree, and the
   result is committed on top of HEAD. Nothing is lost: the version you came
   *from* is still a commit, so returning to it is another restore rather than a
   recovery job.

2. **A restore is a write, so it passes the same guardrail as every other
   write.** The manifest is rebuilt from the restored source and the
   instrumentation is re-verified. If the restored tree does not verify, the
   working tree is put back where it was and the restore is refused — a preview
   whose ids do not match its manifest is one where marking lands in the wrong
   package (B039), which is worse than not going back at all.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..builder.persistence import GitError, git
from ..core.instrumentation import Manifest
from ..core.manifest_builder import build_manifest
from ..core.verifier import verify_instrumentation


class RestoreResult(BaseModel):
    """What happened, in enough detail for the design window to say it."""

    restored: bool = False
    git_sha: str = Field(default="", description="The version that was asked for")
    head: str = Field(default="", description="The commit the restore produced")
    manifest: Manifest | None = None
    error: str = ""


def restore_version(
    app_dir: Path,
    git_sha: str,
    *,
    package_files: dict[str, list[str]],
) -> RestoreResult:
    """Put an earlier design version's code back. Never raises for a bad sha."""
    app_dir = Path(app_dir).resolve()

    if not (app_dir / ".git").exists():
        return RestoreResult(git_sha=git_sha, error=f"{app_dir} is not a git repository")

    try:
        target = git(app_dir, "rev-parse", "--verify", f"{git_sha}^{{commit}}")
        was = git(app_dir, "rev-parse", "HEAD")
    except GitError as exc:
        return RestoreResult(git_sha=git_sha, error=str(exc))

    try:
        # Tracked files only: node_modules, .next and .env.local are ignored in
        # a generated app, so a restore never disturbs what it takes to run.
        git(app_dir, "read-tree", "-u", "--reset", target)
    except GitError as exc:
        return RestoreResult(git_sha=target, error=str(exc))

    manifest = build_manifest(app_dir, package_files)
    report = verify_instrumentation(app_dir, manifest)
    if report.errors:
        try:
            git(app_dir, "read-tree", "-u", "--reset", was)
        except GitError as exc:  # pragma: no cover — the tree was just read
            return RestoreResult(
                git_sha=target,
                error=f"the restore did not verify and could not be undone: {exc}",
            )
        return RestoreResult(
            git_sha=target,
            error=(
                "that version's code no longer matches its instrumentation "
                f"({report.errors[0].message}) — nothing was changed"
            ),
        )

    try:
        if git(app_dir, "status", "--porcelain"):
            git(app_dir, "commit", "-q", "-m", f"design: return to {target[:12]}")
        head = git(app_dir, "rev-parse", "HEAD")
    except GitError as exc:
        return RestoreResult(git_sha=target, error=str(exc))

    return RestoreResult(restored=True, git_sha=target, head=head, manifest=manifest)
