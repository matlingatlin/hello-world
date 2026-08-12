"""SPIKE — marking -> code: scio-id to package and source location.

The second half of the mechanic. The manifest is the contract between what the
builder wrote and what the design window can address. In production the builder
emits it per package; here it is hand-written, which is exactly the assumption
the findings need to flag.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceLocation:
    package: str
    file: str
    component: str
    line: int
    matched_by: str  # "exact" | "pattern"


class UnknownElementError(KeyError):
    """The clicked element has no manifest entry — it cannot be addressed."""


class Manifest:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.elements: dict[str, dict] = data.get("elements", {})
        self.patterns: dict[str, dict] = {
            k: v for k, v in data.get("element_patterns", {}).items() if not k.startswith("$")
        }
        self.packages: dict[str, dict] = data.get("packages", {})

    @classmethod
    def load(cls, path: Path) -> Manifest:
        return cls(json.loads(path.read_text()))

    def resolve(self, scio_id: str) -> SourceLocation:
        entry = self.elements.get(scio_id)
        if entry:
            return SourceLocation(**entry, matched_by="exact")

        # Loop-rendered elements share a source location; the id carries the key.
        for pattern, value in self.patterns.items():
            if fnmatch.fnmatch(scio_id, pattern):
                return SourceLocation(**value, matched_by="pattern")

        raise UnknownElementError(
            f"'{scio_id}' is not in the manifest — the design window could not address it"
        )

    def files_for(self, package: str) -> list[str]:
        entry = self.packages.get(package)
        if entry is None:
            raise UnknownElementError(f"unknown package '{package}'")
        return list(entry.get("files", []))

    def all_files(self) -> list[str]:
        return sorted({f for pkg in self.packages.values() for f in pkg.get("files", [])})
