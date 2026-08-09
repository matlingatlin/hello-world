"""Output 3 of Layer B — the generation playbook (docs/LAYER-B.md).

The fixed house rules every build prompt carries. Loading is trivial; the point
is the assembler: it turns playbook + architecture slice into the exact context
a build package's prompt should carry — small, tight, and contract-bearing.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .architecture import Architecture

DEFAULT_PLAYBOOK_PATH = Path(__file__).with_name("playbook.yaml")


class Stack(BaseModel):
    name: str
    adr: str = ""
    frontend: str = ""
    styling: str = ""
    backend: str = ""
    database: str = ""
    auth: str = ""
    storage: str = ""


class Playbook(BaseModel):
    stack: Stack
    folder_structure: list[str] = Field(default_factory=list)
    naming: dict[str, str] = Field(default_factory=dict)
    secure_by_default: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    accessibility: list[str] = Field(default_factory=list)
    quality: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path | None = None) -> Playbook:
        raw = yaml.safe_load((path or DEFAULT_PLAYBOOK_PATH).read_text())
        return cls(**raw)

    def as_prompt_section(self) -> str:
        """The playbook as the system-prompt block that rides along with every
        build and every review pass."""
        lines = [
            "# House rules (follow these exactly)",
            "",
            f"## Stack — fixed, do not substitute ({self.stack.adr})",
            f"- {self.stack.name}",
        ]
        for label in ("frontend", "styling", "backend", "database", "auth", "storage"):
            value = getattr(self.stack, label)
            if value:
                lines.append(f"- {label}: {value}")

        for title, items in (
            ("Folder structure", self.folder_structure),
            ("Secure by default", self.secure_by_default),
            ("Tests", self.tests),
            ("Accessibility", self.accessibility),
            ("Quality", self.quality),
        ):
            lines += ["", f"## {title}"]
            lines += [f"- {item}" for item in items]

        lines += ["", "## Naming"]
        lines += [f"- {key}: {value}" for key, value in self.naming.items()]
        return "\n".join(lines)


@lru_cache(maxsize=1)
def default_playbook() -> Playbook:
    return Playbook.load()


class BuildContext(BaseModel):
    """What a build prompt carries: the house rules, the architecture slice it
    must satisfy, and the "why" behind it. Layer C will call this per package;
    for now it assembles the whole architecture."""

    playbook: str
    architecture: str
    whole: str = ""
    vocabulary: dict[str, list[str]] = Field(default_factory=dict)
    scope_guard: list[str] = Field(default_factory=list)

    def as_prompt(self) -> str:
        parts = [self.playbook, "", "# The architecture you must implement", self.architecture]
        if self.whole:
            parts += ["", "# Why this exists (the approved whole)", self.whole]
        if self.vocabulary:
            names = ", ".join(sorted(self.vocabulary))
            parts += [
                "",
                "# Canonical vocabulary — use exactly these names",
                names,
            ]
        if self.scope_guard:
            parts += ["", "# Out of scope — do not build"]
            parts += [f"- {item}" for item in self.scope_guard]
        return "\n".join(parts)


def assemble_build_context(
    architecture: Architecture,
    *,
    whole: str = "",
    playbook: Playbook | None = None,
) -> BuildContext:
    """Attach the playbook to an architecture, ready to hand to the relay."""
    book = playbook or default_playbook()
    return BuildContext(
        playbook=book.as_prompt_section(),
        architecture=architecture.model_dump_json(indent=2),
        whole=whole,
        vocabulary=architecture.vocabulary,
        scope_guard=architecture.scope_guard,
    )
