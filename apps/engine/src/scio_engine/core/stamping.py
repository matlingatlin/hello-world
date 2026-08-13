"""Stamp `data-scio-package` deterministically instead of asking for it.

The first real run produced this, from a real model that had the rules in front
of it:

    <li data-scio-id="home-step-choose">1. Choose a table that's free.</li>

The id is there; the package tag is not. The manifest still resolved it — by
inheriting the nearest package attribute above — which is precisely the silent
wrong answer the spike warned about: a click resolves *confidently* to whatever
element happened to be written earlier.

The builder always knows which package it is generating. So the model supplies
the thing only it can (a meaningful id per element) and the builder supplies the
thing it already knows (the owning package). Nothing about that requires
judgment, so nothing about it should depend on the model complying.

Scanning is textual, matching manifest_builder: an element is the span from the
`<` that opens its tag to the `>` that closes it.
"""

from __future__ import annotations

import re

from .instrumentation import ID_ATTRIBUTE, PACKAGE_ATTRIBUTE

STAMPABLE_SUFFIXES = (".tsx", ".jsx", ".html")

# data-scio-id="literal"  or  data-scio-id={`template-${x}`}
_ANY_ID = re.compile(
    rf'{ID_ATTRIBUTE}=(?:"(?P<literal>[^"]*)"|\{{`(?P<template>[^`]*)`\}})'
)
_HAS_PACKAGE = re.compile(rf"{PACKAGE_ATTRIBUTE}\s*=")


def _tag_span(text: str, position: int) -> tuple[int, int]:
    """The `<…>` the attribute at `position` belongs to.

    Falls back to the whole line when the tag cannot be delimited, which keeps a
    malformed file from crashing the build — the verifier will speak up instead.
    """
    start = text.rfind("<", 0, position)
    end = text.find(">", position)
    if start == -1 or end == -1:
        line_start = text.rfind("\n", 0, position) + 1
        line_end = text.find("\n", position)
        return line_start, (line_end if line_end != -1 else len(text))
    return start, end


def ids_missing_package(text: str) -> list[str]:
    """Ids whose own element carries no package attribute.

    Deliberately strict about "own element": inheriting from a neighbour is the
    behaviour that made a lost tag invisible.
    """
    missing: list[str] = []
    for match in _ANY_ID.finditer(text):
        start, end = _tag_span(text, match.start())
        if not _HAS_PACKAGE.search(text[start:end]):
            missing.append(match.group("literal") or match.group("template") or "")
    return missing


def stamp_package(text: str, package: str) -> str:
    """Add `data-scio-package="<package>"` to every marked element that lacks it.

    Inserted immediately after the id attribute, so the pair stays legible in the
    source a user owns and can read. Elements that already name a package are
    left exactly as they are — including one that names a *different* package,
    which is a contract violation for the verifier to catch, not for this to
    paper over.
    """
    result: list[str] = []
    cursor = 0
    for match in _ANY_ID.finditer(text):
        start, end = _tag_span(text, match.start())
        if _HAS_PACKAGE.search(text[start:end]):
            continue
        result.append(text[cursor : match.end()])
        result.append(f' {PACKAGE_ATTRIBUTE}="{package}"')
        cursor = match.end()
    result.append(text[cursor:])
    return "".join(result)


def stamp_files(files: dict[str, str], package: str) -> dict[str, str]:
    """Stamp every markup file a package produced."""
    return {
        path: stamp_package(content, package)
        if path.endswith(STAMPABLE_SUFFIXES)
        else content
        for path, content in files.items()
    }
