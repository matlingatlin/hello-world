"""A catalog entry — one thing the library knows how to build without a model.

The library is the nave (docs/STRATEGY.md): the more of an app that comes from
curated, tested parts, the cheaper, faster and more predictable a build is, and
the less of it is a model's guess. An entry is therefore not a snippet. It is a
contract with files attached:

- **what it provides** — the architecture nodes and capabilities it covers, in
  canonical vocabulary, so matching is a lookup rather than a judgment call;
- **the files it contributes** — deterministic paths, the same decision the file
  plan makes, so the manifest's package→file map cannot disagree with reality;
- **its instrumentation** — every element already carries `data-scio-id`. The
  builder stamps `data-scio-package` (core/stamping.py), because that is
  per-project and the entry is not;
- **quality metadata** — tested, security-reviewed, scores. An entry nobody
  vetted is worse than generating fresh, because it carries authority it has not
  earned.

Entries are written against a *placeholder* entity, never a project's own words:
`__ENTITY__` in paths, code and ids. Adapting an entry is then a substitution
with the project's canonical name, which is deterministic and reviewable —
"rename the generic thing to the project's thing" done by a regex, not a model.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from ..layerb.vocabulary import canonical_name

ENTITY = "__ENTITY__"
ENTITY_PASCAL = "__ENTITY_PASCAL__"
ENTITY_TITLE = "__ENTITY_TITLE__"
ENTITY_PLURAL = "__ENTITY_PLURAL__"

TOKEN_PREFIX = "__TOKEN_"


class Layer(StrEnum):
    """Which of the library's layers an entry belongs to (docs/LIBRARY.md).

    This slice seeds `ui` and `feature`; the rest exist so an entry never has to
    be re-homed when the library grows.
    """

    token = "token"
    ui = "ui"
    pattern = "pattern"
    feature = "feature"
    integration = "integration"


class Quality(BaseModel):
    """What has actually been checked about this entry.

    Not decoration: `usable` is what the matcher consults, and an entry that has
    not been tested and security-reviewed is not offered, however good it looks.
    """

    tested: bool = False
    security_reviewed: bool = False
    accessibility_score: int = 0  # 0-100
    lighthouse_score: int = 0  # 0-100
    review_notes: str = ""

    @property
    def usable(self) -> bool:
        return self.tested and self.security_reviewed


class Provides(BaseModel):
    """What the entry covers, in canonical vocabulary — the matcher's index."""

    entities: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)

    def canonical_entities(self) -> set[str]:
        return {canonical_name(name) for name in self.entities if canonical_name(name)}


class CatalogEntry(BaseModel):
    """One curated, reusable part of an app."""

    id: str
    name: str
    layer: Layer
    description: str  # what it is, in the words a matcher would search
    version: str = "1.0.0"
    provenance: str = "scio-seed"

    provides: Provides = Field(default_factory=Provides)
    depends_on: list[str] = Field(default_factory=list)  # other entry ids
    package_dependencies: list[str] = Field(
        default_factory=list,
        description="Build-package ids this entry's code expects to exist (foundation, schema…)",
    )
    npm_dependencies: list[str] = Field(default_factory=list)

    files: dict[str, str] = Field(
        default_factory=dict,
        description="Path template -> file body. Both carry __ENTITY__ placeholders.",
    )
    token_bindings: dict[str, str] = Field(
        default_factory=dict,
        description="__TOKEN_X__ placeholder -> the token key it reads from the project",
    )
    element_ids: list[str] = Field(
        default_factory=list, description="The data-scio-id templates this entry carries"
    )
    quality: Quality = Field(default_factory=Quality)

    @property
    def offerable(self) -> bool:
        """Whether the matcher may propose this at all."""
        return self.quality.usable and bool(self.files)

    def adapt(self, entity: str, tokens: dict[str, str] | None = None) -> dict[str, str]:
        """This entry as files for one project: paths and bodies, substituted.

        Substitution only — no model, no reformatting. What was reviewed is what
        lands on disk, modulo the project's own name and colours.
        """
        values = _entity_forms(entity)
        return {
            _substitute(path, values, tokens or {}, self.token_bindings): _substitute(
                body, values, tokens or {}, self.token_bindings
            )
            for path, body in self.files.items()
        }

    def adapted_paths(self, entity: str) -> list[str]:
        values = _entity_forms(entity)
        return sorted(_substitute(path, values, {}, {}) for path in self.files)

    def adapted_ids(self, entity: str) -> list[str]:
        values = _entity_forms(entity)
        return sorted(_substitute(i, values, {}, {}) for i in self.element_ids)

    @classmethod
    def load(cls, path: Path) -> CatalogEntry:
        """Read an entry directory: entry.json plus a files/ tree.

        The code lives as real files rather than strings in JSON so it can be
        read, linted and reviewed like the code it is.
        """
        data = json.loads((path / "entry.json").read_text())
        files_root = path / "files"
        if files_root.exists():
            data["files"] = {
                str(f.relative_to(files_root)): f.read_text()
                for f in sorted(files_root.rglob("*"))
                if f.is_file()
            }
        return cls.model_validate(data)


def _entity_forms(entity: str) -> dict[str, str]:
    """Every shape of the project's name an entry might need."""
    name = canonical_name(entity) or "item"
    words = name.split("_")
    return {
        ENTITY: name,
        ENTITY_PASCAL: "".join(w.capitalize() for w in words),
        ENTITY_TITLE: " ".join(w.capitalize() for w in words),
        ENTITY_PLURAL: _pluralize(name),
    }


def _pluralize(name: str) -> str:
    if name.endswith("y") and not name.endswith(("ay", "ey", "oy", "uy")):
        return name[:-1] + "ies"
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    return name + "s"


_TOKEN_PLACEHOLDER = re.compile(rf"{TOKEN_PREFIX}[A-Z0-9_]+__")


def _substitute(
    text: str, values: dict[str, str], tokens: dict[str, str], bindings: dict[str, str]
) -> str:
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    for placeholder, token_key in bindings.items():
        if placeholder in text:
            text = text.replace(placeholder, tokens.get(token_key, _fallback_for(placeholder)))
    # Any binding the project did not supply still must not ship a placeholder.
    return _TOKEN_PLACEHOLDER.sub(lambda m: _fallback_for(m.group(0)), text)


def _fallback_for(placeholder: str) -> str:
    """A neutral value when the project has no token for this binding.

    A missing token must never leave `__TOKEN_ACCENT__` in shipped code: the app
    would render the placeholder text and the build would be a lie.
    """
    return {
        "__TOKEN_ACCENT__": "#0f766e",
        "__TOKEN_INK__": "#101319",
        "__TOKEN_PAPER__": "#ffffff",
        "__TOKEN_RADIUS__": "0.5rem",
    }.get(placeholder, "inherit")
