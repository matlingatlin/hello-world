"""GUARDRAIL 1 — verify instrumentation after every (re)generation.

The spike showed that losing an id does not fail loudly on its own: the app still
renders, the click still resolves, and it resolves to the wrong package. So the
check has to happen at generation time, when we still know what the ids were
supposed to be.

A regeneration that drops or renames an id is a FAILED build, not a successful
one with a caveat.
"""

from __future__ import annotations

from collections import Counter
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from .instrumentation import ID_ATTRIBUTE, Manifest
from .manifest_builder import (
    _ID_LITERAL,
    _ID_TEMPLATE,
    SOURCE_SUFFIXES,
    _template_to_pattern,
)


class Severity(StrEnum):
    error = "error"
    warning = "warning"


class InstrumentationIssue(BaseModel):
    rule: str
    severity: Severity = Severity.error
    message: str
    subject: str = ""


class InstrumentationReport(BaseModel):
    valid: bool
    issues: list[InstrumentationIssue] = Field(default_factory=list)
    element_count: int = 0

    @property
    def errors(self) -> list[InstrumentationIssue]:
        return [i for i in self.issues if i.severity is Severity.error]

    def raise_for_status(self) -> None:
        """Fail loudly. The whole point of this guardrail is that a caller
        cannot accidentally continue past a broken build."""
        if self.valid:
            return
        details = "\n".join(f"  - [{i.rule}] {i.message}" for i in self.errors)
        raise InstrumentationError(f"Instrumentation is broken:\n{details}")


class InstrumentationError(RuntimeError):
    """Raised when generated code fails the instrumentation contract."""


def _raw_ids_in_source(app_dir: Path, files: list[str]) -> Counter[str]:
    """Every literal id in the source, counted — duplicates included.

    The manifest is a dict and so silently swallows a duplicate id; counting the
    raw source is the only way to see one.
    """
    counts: Counter[str] = Counter()
    for relative in files:
        path = app_dir / relative
        if not path.exists() or path.suffix not in SOURCE_SUFFIXES:
            continue
        counts.update(_ID_LITERAL.findall(path.read_text()))
    return counts


def _patterns_in_source(app_dir: Path, files: list[str]) -> set[str]:
    """Loop-rendered ids, normalised to their pattern.

    `booking-slot-${value}` becomes `booking-slot-*` — the same normalisation the
    manifest builder applies. Comparing the raw template against literal ids
    would report the pattern as "lost" on every single regeneration.
    """
    patterns: set[str] = set()
    for relative in files:
        path = app_dir / relative
        if not path.exists() or path.suffix not in SOURCE_SUFFIXES:
            continue
        patterns.update(
            _template_to_pattern(raw) for raw in _ID_TEMPLATE.findall(path.read_text())
        )
    return patterns


def verify_instrumentation(
    app_dir: Path,
    manifest: Manifest,
    *,
    expected_ids: set[str] | None = None,
) -> InstrumentationReport:
    """Check the manifest against the code, and (on a regeneration) against what
    the ids used to be.

    `expected_ids` is the pre-regeneration id set. Passing it is what turns this
    from "the code is self-consistent" into "the code did not lose anything" —
    the check the spike proved we need.
    """
    app_dir = app_dir.resolve()
    issues: list[InstrumentationIssue] = []
    tracked = manifest.all_files()

    # 1. Duplicate ids — two elements claiming one identity.
    counts = _raw_ids_in_source(app_dir, tracked)
    for scio_id, count in sorted(counts.items()):
        if count > 1:
            issues.append(
                InstrumentationIssue(
                    rule="unique_id",
                    message=(
                        f"'{scio_id}' appears {count} times in the source. Two elements with "
                        "one identity means a marking cannot say which it meant."
                    ),
                    subject=scio_id,
                )
            )

    # 2. Every id in the source is in the manifest, and vice versa.
    source_ids = set(counts)
    manifest_ids = manifest.ids()
    for scio_id in sorted(source_ids - manifest_ids):
        issues.append(
            InstrumentationIssue(
                rule="manifest_complete",
                message=(
                    f"'{scio_id}' exists in the code but not the manifest — it would be "
                    "unaddressable from the design window."
                ),
                subject=scio_id,
            )
        )
    for scio_id in sorted(manifest_ids - source_ids):
        issues.append(
            InstrumentationIssue(
                rule="manifest_consistent",
                message=(
                    f"'{scio_id}' is in the manifest but no longer in the code — a stale entry "
                    "that would resolve a marking to a line that has moved or gone."
                ),
                subject=scio_id,
            )
        )

    # 3. Every element names a package, and that package is one we know.
    for scio_id, location in sorted(manifest.elements.items()):
        if not location.package:
            issues.append(
                InstrumentationIssue(
                    rule="element_has_package",
                    message=f"'{scio_id}' has no owning package — a change could not be targeted.",
                    subject=scio_id,
                )
            )
        elif location.package not in manifest.packages:
            issues.append(
                InstrumentationIssue(
                    rule="package_known",
                    message=(
                        f"'{scio_id}' claims package '{location.package}', which is not in the "
                        "build plan."
                    ),
                    subject=scio_id,
                )
            )

    # 3b. Loop patterns: in the source and in the manifest, both ways.
    source_patterns = _patterns_in_source(app_dir, tracked)
    manifest_patterns = set(manifest.patterns)
    for pattern in sorted(source_patterns - manifest_patterns):
        issues.append(
            InstrumentationIssue(
                rule="manifest_complete",
                message=(
                    f"Loop pattern '{pattern}' exists in the code but not the manifest — "
                    "every element it renders would be unaddressable."
                ),
                subject=pattern,
            )
        )
    for pattern in sorted(manifest_patterns - source_patterns):
        issues.append(
            InstrumentationIssue(
                rule="manifest_consistent",
                message=f"Loop pattern '{pattern}' is in the manifest but no longer in the code.",
                subject=pattern,
            )
        )

    # 4. THE SPIKE'S BUG: a regeneration that lost ids.
    # Compare the union of literals and normalised patterns, so a lost loop
    # counts as a loss and an unchanged loop does not look like one.
    addressable = source_ids | source_patterns
    if expected_ids is not None:
        for scio_id in sorted(expected_ids - addressable):
            issues.append(
                InstrumentationIssue(
                    rule="id_survives_regeneration",
                    message=(
                        f"'{scio_id}' was lost in this regeneration. A click on it would fall "
                        "through to an ancestor and resolve to the WRONG package, so this build "
                        "is rejected."
                    ),
                    subject=scio_id,
                )
            )
        for scio_id in sorted(addressable - expected_ids):
            issues.append(
                InstrumentationIssue(
                    rule="new_id_introduced",
                    severity=Severity.warning,
                    message=f"'{scio_id}' is new in this regeneration.",
                    subject=scio_id,
                )
            )

    # 5. Nothing instrumented at all.
    if not source_ids:
        issues.append(
            InstrumentationIssue(
                rule="has_instrumentation",
                message=(
                    f"No {ID_ATTRIBUTE} found in any file. Nothing in this app could be marked."
                ),
                subject=str(app_dir),
            )
        )

    has_error = any(i.severity is Severity.error for i in issues)
    return InstrumentationReport(
        valid=not has_error, issues=issues, element_count=len(source_ids)
    )


def ids_in_source(app_dir: Path, files: list[str]) -> set[str]:
    """Everything addressable right now — snapshot this before a regeneration.

    Literals plus normalised loop patterns, the same union the verifier compares
    against, so the two cannot disagree about what "lost" means.
    """
    return set(_raw_ids_in_source(app_dir, files)) | _patterns_in_source(app_dir, files)
