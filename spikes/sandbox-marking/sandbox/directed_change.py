"""SPIKE — the directed change and its isolation proof.

The product promise is that a marking regenerates only what was marked. Here the
edit itself is mechanical (a string swap, not an LLM) because the thing under
test is the *targeting*: does the mapping let us touch exactly one package, and
can we prove the rest is byte-identical afterwards?
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .resolver import Manifest


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(app_dir: Path, files: list[str]) -> dict[str, str]:
    """Content hashes for every tracked file, before a change."""
    return {f: _digest(app_dir / f) for f in files if (app_dir / f).exists()}


@dataclass
class IsolationProof:
    """Which files actually changed, versus which were allowed to."""

    target_package: str
    allowed_files: list[str]
    changed_files: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    @property
    def isolated(self) -> bool:
        return not self.violations and bool(self.changed_files)

    def summary(self) -> str:
        lines = [
            f"target package: {self.target_package}",
            f"changed:   {', '.join(self.changed_files) or '(nothing)'}",
            f"unchanged: {len(self.unchanged_files)} file(s) byte-identical",
        ]
        if self.violations:
            lines.append(f"VIOLATIONS: {', '.join(self.violations)}")
        return "\n".join(lines)


def verify_isolation(
    app_dir: Path,
    before: dict[str, str],
    target_package: str,
    manifest: Manifest,
) -> IsolationProof:
    """Compare hashes: anything changed outside the target package is a violation."""
    allowed = manifest.files_for(target_package)
    proof = IsolationProof(target_package=target_package, allowed_files=allowed)

    for relative, old_hash in before.items():
        path = app_dir / relative
        new_hash = _digest(path) if path.exists() else None
        if new_hash == old_hash:
            proof.unchanged_files.append(relative)
            continue
        proof.changed_files.append(relative)
        if relative not in allowed:
            proof.violations.append(relative)
    return proof


@dataclass
class ChangeRequest:
    """A marking turned into an edit: this element, this change."""

    scio_id: str
    instruction: str
    find: str
    replace: str


def plan_directed_change(
    request: ChangeRequest, manifest: Manifest, app_dir: Path
) -> tuple[str, dict[str, str]]:
    """Resolve the marking to its package and produce the new file contents.

    Only files belonging to the resolved package are considered — that
    restriction is the mechanic, and it is enforced here rather than trusted to
    whoever writes the edit.
    """
    location = manifest.resolve(request.scio_id)
    package_files = manifest.files_for(location.package)

    edits: dict[str, str] = {}
    for relative in package_files:
        path = app_dir / relative
        if not path.exists():
            continue
        content = path.read_text()
        if request.find in content:
            edits[relative] = content.replace(request.find, request.replace)

    if not edits:
        raise ValueError(
            f"'{request.find}' not found in {location.package}'s files "
            f"({', '.join(package_files)}) — the change would touch nothing"
        )
    return location.package, edits
