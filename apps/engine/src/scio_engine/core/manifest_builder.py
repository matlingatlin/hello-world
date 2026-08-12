"""Derive the manifest FROM the generated source.

The spike's headline finding: a hand-written manifest drifts from the code, and
the drift is silent. So the manifest is an artifact of the build — scanned out of
the files each package actually produced, never authored beside them.

Scanning is textual (a regex over JSX attributes) rather than a full parse. That
is honest for the shapes the playbook mandates — literal attributes and template
literals in loops — and its limits are recorded in KNOWN_LIMITS below. An AST
parse is the upgrade when generated code gets cleverer than the playbook allows.
"""

from __future__ import annotations

import re
from pathlib import Path

from .instrumentation import ID_ATTRIBUTE, PACKAGE_ATTRIBUTE, Manifest, SourceLocation

KNOWN_LIMITS = """Textual scanning does not see:
- ids built by string concatenation outside a template literal
- ids passed down as props from another file
- attributes assembled via spread ({...props})
The playbook forbids all three; the verifier is what catches a violation."""

# data-scio-id="literal"  or  data-scio-id={`base-${key}`}
_ID_LITERAL = re.compile(rf'{ID_ATTRIBUTE}="([^"]+)"')
_ID_TEMPLATE = re.compile(rf'{ID_ATTRIBUTE}=\{{`([^`]+)`\}}')
_PACKAGE = re.compile(rf'{PACKAGE_ATTRIBUTE}="([^"]+)"')
_COMPONENT = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?function\s+([A-Za-z0-9_]+)")

SOURCE_SUFFIXES = (".tsx", ".jsx", ".ts", ".js", ".html")


class ManifestBuildError(RuntimeError):
    """The source could not be scanned into a coherent manifest."""


def _template_to_pattern(raw: str) -> str:
    """`booking-slot-${value}` -> booking-slot-*  — one entry per loop, not per row."""
    return re.sub(r"\$\{[^}]*\}", "*", raw)


def _component_at(lines: list[str], index: int) -> str:
    """The nearest enclosing function name above this line — good enough to name
    the component in an error message, which is all it is for."""
    for line in reversed(lines[: index + 1]):
        match = _COMPONENT.match(line)
        if match:
            return match.group(1)
    return ""


def _package_on_line(line: str, fallback: str) -> str:
    match = _PACKAGE.search(line)
    return match.group(1) if match else fallback


def scan_file(
    path: Path, relative: str
) -> tuple[dict[str, SourceLocation], dict[str, SourceLocation]]:
    """Every instrumented element in one file, split into exact ids and patterns.

    An element's package comes from its own line when present; otherwise from the
    nearest package attribute above it, since JSX often spreads one element over
    several lines.
    """
    text = path.read_text()
    lines = text.splitlines()
    exact: dict[str, SourceLocation] = {}
    patterns: dict[str, SourceLocation] = {}

    nearest_package = ""
    for index, line in enumerate(lines):
        package_here = _PACKAGE.search(line)
        if package_here:
            nearest_package = package_here.group(1)

        for match in _ID_LITERAL.finditer(line):
            scio_id = match.group(1)
            package = (
                _package_on_line(line, "")
                or _lookahead_package(lines, index)
                or nearest_package
            )
            exact[scio_id] = SourceLocation(
                package=package,
                file=relative,
                line=index + 1,
                component=_component_at(lines, index),
            )

        for match in _ID_TEMPLATE.finditer(line):
            pattern = _template_to_pattern(match.group(1))
            package = (
                _package_on_line(line, "")
                or _lookahead_package(lines, index)
                or nearest_package
            )
            patterns[pattern] = SourceLocation(
                package=package,
                file=relative,
                line=index + 1,
                component=_component_at(lines, index),
            )
    return exact, patterns


def _lookahead_package(lines: list[str], index: int, window: int = 4) -> str:
    """A multi-line JSX element often carries its package attribute a line or two
    below the id. Look a short way ahead before giving up."""
    for line in lines[index + 1 : index + 1 + window]:
        match = _PACKAGE.search(line)
        if match:
            return match.group(1)
    return ""


def build_manifest(app_dir: Path, package_files: dict[str, list[str]]) -> Manifest:
    """Scan the files each package produced into a manifest.

    `package_files` comes from the build plan (Layer C), so the manifest's
    package list and the plan's cannot disagree.
    """
    app_dir = app_dir.resolve()
    manifest = Manifest(generated_from="source-scan", packages={})

    for package, files in package_files.items():
        manifest.packages[package] = list(files)
        for relative in files:
            path = app_dir / relative
            if not path.exists() or path.suffix not in SOURCE_SUFFIXES:
                continue
            exact, patterns = scan_file(path, relative)
            for scio_id, location in exact.items():
                if not location.package:
                    location.package = package
                manifest.elements[scio_id] = location
            for pattern, location in patterns.items():
                if not location.package:
                    location.package = package
                manifest.patterns[pattern] = location
    return manifest
