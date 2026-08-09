"""Canonical vocabulary (docs/LAYER-B.md, "Method").

Users say "bookings", "Booking", "table reservation" for one thing. Layer B picks
ONE name per concept and uses it everywhere — in the architecture, in every build
prompt, and in the generated code. Fewer names means fewer bugs and more shared
context across the relay's passes.

Deterministic: same input words always yield the same canonical set.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

# Irregular plurals worth handling explicitly; the rules below cover the rest.
_IRREGULAR_SINGULARS: dict[str, str] = {
    "people": "person",
    "children": "child",
    "men": "man",
    "women": "woman",
    "data": "data",
    "media": "media",
}

# Words users commonly use for the same concept. Left = alias, right = canonical.
_SYNONYMS: dict[str, str] = {
    "reservation": "booking",
    "appointment": "booking",
    "customer": "guest",
    "client": "guest",
    "member": "user",
    "account": "user",
    "staff_member": "staff",
    "employee": "staff",
    "admin": "administrator",
    "photo": "image",
    "picture": "image",
}

_NON_WORD = re.compile(r"[^a-z0-9]+")


def slugify(term: str) -> str:
    """Lowercase snake_case, punctuation stripped."""
    return _NON_WORD.sub("_", term.strip().lower()).strip("_")


def singularize(word: str) -> str:
    """Enough English plural handling for entity names — not a linguistics engine."""
    if word in _IRREGULAR_SINGULARS:
        return _IRREGULAR_SINGULARS[word]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "sses", "xes", "zes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def canonical_name(term: str) -> str:
    """One canonical, singular, snake_case name for a concept.

    "Bookings" / "booking" / "Reservations" all collapse to "booking".
    """
    slug = slugify(term)
    if not slug:
        return ""
    parts = slug.split("_")
    parts[-1] = singularize(parts[-1])
    slug = "_".join(parts)
    return _SYNONYMS.get(slug, slug)


class Vocabulary(BaseModel):
    """The name set for one project: canonical name -> the terms the user used.

    Keeping the aliases matters — the "whole" is retold in the user's words, while
    the architecture and code use the canonical name.
    """

    canonical: dict[str, list[str]] = Field(default_factory=dict)

    def add(self, term: str) -> str:
        """Register a user term, return its canonical name."""
        name = canonical_name(term)
        if not name:
            return ""
        aliases = self.canonical.setdefault(name, [])
        if term not in aliases:
            aliases.append(term)
        return name

    def resolve(self, term: str) -> str:
        """Canonical name for a term (registered or not)."""
        return canonical_name(term)

    def names(self) -> list[str]:
        return sorted(self.canonical)

    @classmethod
    def from_terms(cls, terms: list[str]) -> Vocabulary:
        vocab = cls()
        for term in terms:
            vocab.add(term)
        return vocab
