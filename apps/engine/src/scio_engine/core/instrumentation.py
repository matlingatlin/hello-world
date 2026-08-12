"""The instrumentation contract — how generated code stays addressable.

Every element the user can mark carries two attributes:

    data-scio-id       unique within the app; identifies THIS element
    data-scio-package  the Layer C build package that owns it

The manifest maps id -> package + source location. The spike proved why this
must be derived from the code rather than written alongside it: when an id went
missing, a click resolved *confidently to the wrong package*, and a directed
change would have rewritten the app shell instead of the marked button.

This module holds the contract and the manifest model. `manifest_builder`
derives it; `verifier` enforces it.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

from pydantic import BaseModel, Field

ID_ATTRIBUTE = "data-scio-id"
PACKAGE_ATTRIBUTE = "data-scio-package"

INSTRUMENTATION_RULES = f"""## Instrumentation (required — the app is unusable without it)

Every element a user could point at carries both attributes:
- `{ID_ATTRIBUTE}` — unique across the whole app, stable across regenerations,
  kebab-case, derived from what the element IS (`booking-submit`), never from
  what it currently says or where it currently sits.
- `{PACKAGE_ATTRIBUTE}` — the build package that owns it.

Rules:
- Preserve existing ids when you rewrite a component. Restructure the markup
  freely; the ids are the contract, not the layout.
- Elements rendered in a loop get `${{base}}-${{key}}` — one id per instance.
- Interactive elements (buttons, inputs, links) and every distinct region MUST
  be instrumented. A user who can see it can mark it.
- Never invent an id for an element you did not create; never reuse one.
"""


class SourceLocation(BaseModel):
    """Where an element lives, and which package owns it."""

    package: str
    file: str
    line: int
    component: str = ""
    matched_by: str = "exact"  # "exact" | "pattern"


class Manifest(BaseModel):
    """id -> location, plus the file list per package.

    Generated (see manifest_builder). A hand-written manifest is exactly the
    drift the spike warned about, so `generated_from` records its provenance.
    """

    version: int = 1
    generated_from: str = "source"
    elements: dict[str, SourceLocation] = Field(default_factory=dict)
    patterns: dict[str, SourceLocation] = Field(default_factory=dict)
    packages: dict[str, list[str]] = Field(default_factory=dict)  # package -> files

    def resolve(self, scio_id: str) -> SourceLocation | None:
        """The location for an id, or None. Callers decide how loud to be —
        the resolver errors; the verifier collects."""
        exact = self.elements.get(scio_id)
        if exact:
            return exact
        for pattern, location in self.patterns.items():
            if fnmatch.fnmatch(scio_id, pattern):
                return location.model_copy(update={"matched_by": "pattern"})
        return None

    def files_for(self, package: str) -> list[str]:
        return list(self.packages.get(package, []))

    def all_files(self) -> list[str]:
        return sorted({f for files in self.packages.values() for f in files})

    def ids(self) -> set[str]:
        return set(self.elements)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> Manifest:
        return cls.model_validate_json(path.read_text())
