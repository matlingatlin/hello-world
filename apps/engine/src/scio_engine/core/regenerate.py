"""Directed regeneration — the product promise, enforced rather than trusted.

marking -> resolve the package -> regenerate ONLY that package -> re-verify the
instrumentation -> prove nothing else moved.

The regenerator itself is an interface. B041 plugs the LLM builder in; tests use
a mechanical one, because what is under test here is the *targeting and the
guardrails*, not the quality of an edit.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field

from .instrumentation import Manifest
from .manifest_builder import build_manifest
from .resolver import ElementHit, ResolvedMarking, resolve_marking
from .sandbox import SandboxHandle, SandboxProvider
from .verifier import (
    InstrumentationError,
    InstrumentationReport,
    ids_in_source,
    verify_instrumentation,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(app_dir: Path, files: list[str]) -> dict[str, str]:
    """Content hashes for every tracked file, before a change."""
    return {f: _digest(app_dir / f) for f in files if (app_dir / f).exists()}


class IsolationProof(BaseModel):
    """Which files actually changed, versus which were allowed to."""

    target_package: str
    allowed_files: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    unchanged_files: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)

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


class IsolationViolation(RuntimeError):
    """A directed change leaked outside its package. Refuse the result."""


def verify_isolation(
    app_dir: Path, before: dict[str, str], target_package: str, manifest: Manifest
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
    """A marking turned into an instruction."""

    hit: ElementHit
    instruction: str


class PackageRegenerator(ABC):
    """Rewrites one package's files. The LLM builder implements this in B041."""

    @abstractmethod
    def regenerate(
        self,
        app_dir: Path,
        package: str,
        files: list[str],
        marking: ResolvedMarking,
        instruction: str,
    ) -> dict[str, str]:
        """Return {relative path -> new content} for the target package ONLY.

        Implementations must preserve every data-scio-id they were given; the
        verifier rejects the result otherwise.
        """


class MechanicalRegenerator(PackageRegenerator):
    """A find/replace stand-in, for tests and for the core's own proof.

    Deliberately dumb: it makes the targeting testable without a model, and it
    cannot accidentally "fix" instrumentation the way a model might.
    """

    def __init__(self, find: str, replace: str) -> None:
        self.find = find
        self.replace = replace

    def regenerate(
        self,
        app_dir: Path,
        package: str,
        files: list[str],
        marking: ResolvedMarking,
        instruction: str,
    ) -> dict[str, str]:
        edits: dict[str, str] = {}
        for relative in files:
            path = app_dir / relative
            if not path.exists():
                continue
            content = path.read_text()
            if self.find in content:
                edits[relative] = content.replace(self.find, self.replace)
        if not edits:
            raise ValueError(
                f"'{self.find}' not found in {package}'s files — the change would touch nothing"
            )
        return edits


@dataclass
class RegenerationResult:
    """Everything a caller needs to decide whether to keep the change."""

    marking: ResolvedMarking
    package: str
    edited_files: list[str]
    isolation: IsolationProof
    instrumentation: InstrumentationReport
    manifest: Manifest
    accepted: bool = True
    rejection: str = ""
    rolled_back: bool = False
    warnings: list[str] = field(default_factory=list)


def directed_regenerate(
    app_dir: Path,
    hit: ElementHit,
    instruction: str,
    *,
    manifest: Manifest,
    regenerator: PackageRegenerator,
    sandbox: SandboxProvider | None = None,
    handle: SandboxHandle | None = None,
    package_files: dict[str, list[str]] | None = None,
) -> RegenerationResult:
    """The whole guarded path, in order.

    Resolve strictly, snapshot, regenerate only the target package, re-derive the
    manifest, re-verify instrumentation against the ids we had, prove isolation —
    and roll back if either guardrail fails. A rejected change must leave no
    trace, or the next marking resolves against a half-applied edit.
    """
    app_dir = app_dir.resolve()

    marking = resolve_marking(hit, manifest)  # raises rather than guessing
    package = marking.package
    files = manifest.files_for(package)
    if not files:
        raise ValueError(f"package '{package}' owns no files in the manifest")

    tracked = manifest.all_files()
    before_hashes = snapshot(app_dir, tracked)
    before_ids = ids_in_source(app_dir, tracked)
    original_contents = {f: (app_dir / f).read_text() for f in tracked if (app_dir / f).exists()}

    edits = regenerator.regenerate(app_dir, package, files, marking, instruction)
    stray = [f for f in edits if f not in files]
    if stray:
        raise IsolationViolation(
            f"the regenerator returned files outside '{package}': {', '.join(stray)}"
        )

    if sandbox and handle:
        sandbox.apply_change(handle, edits)
    else:
        for relative, content in edits.items():
            (app_dir / relative).write_text(content)

    new_manifest = build_manifest(app_dir, package_files or manifest.packages)
    report = verify_instrumentation(app_dir, new_manifest, expected_ids=before_ids)
    proof = verify_isolation(app_dir, before_hashes, package, new_manifest)

    result = RegenerationResult(
        marking=marking,
        package=package,
        edited_files=sorted(edits),
        isolation=proof,
        instrumentation=report,
        manifest=new_manifest,
        warnings=[i.message for i in report.issues if i.severity == "warning"],
    )

    if not report.valid or proof.violations:
        result.accepted = False
        result.rejection = (
            "instrumentation broken by the regeneration"
            if not report.valid
            else f"change leaked outside {package}: {', '.join(proof.violations)}"
        )
        _roll_back(app_dir, original_contents, sandbox, handle)
        result.rolled_back = True
        result.manifest = manifest

    return result


def _roll_back(
    app_dir: Path,
    original_contents: dict[str, str],
    sandbox: SandboxProvider | None,
    handle: SandboxHandle | None,
) -> None:
    if sandbox and handle:
        sandbox.apply_change(handle, original_contents)
        return
    for relative, content in original_contents.items():
        (app_dir / relative).write_text(content)


def regenerate_or_raise(*args, **kwargs) -> RegenerationResult:
    """directed_regenerate, but a rejected change raises.

    For callers that want the guardrail to stop them rather than hand them a
    result object they might forget to check.
    """
    result = directed_regenerate(*args, **kwargs)
    if not result.accepted:
        if not result.instrumentation.valid:
            raise InstrumentationError(result.rejection)
        raise IsolationViolation(result.rejection)
    return result
