"""Canonical categories — the reason the library does not split into synonyms.

Left to itself, a library that names its own categories ends up with `login`,
`auth`, `authentication`, `sign-in` and `user-accounts` holding five copies of
one thing, none of which ever match each other. That is not a hypothetical
failure mode; it is what happens by default the moment a model is allowed to
invent a label.

So a category is never free text. There is a registry: a seeded set of canonical
categories with their aliases, growable through an explicit proposal that a
person confirms. Mapping a function to a category is a deterministic lookup over
canonical vocabulary; only when that lookup finds nothing is anything proposed,
and a proposal is a *reviewable row*, not a new category in use.

The category narrows the search. It never decides a match — the contract does
(`identity.Contract`). A wrong category costs a missed reuse; a wrong match
ships the wrong code, which is why the two jobs are kept apart.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from ..layerb.vocabulary import canonical_name, singularize

UNCATEGORISED = ""


class Category(BaseModel):
    """One canonical area of an app."""

    name: str
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    seeded: bool = True
    confirmed: bool = True

    def matches(self, term: str) -> bool:
        needle = _normalise(term)
        return bool(needle) and needle in self.terms()

    def terms(self) -> set[str]:
        return {_normalise(self.name), *(_normalise(a) for a in self.aliases)} - {""}


SEED_CATEGORIES: tuple[Category, ...] = (
    Category(
        name="auth",
        description="Signing in, sessions, accounts and who someone is.",
        aliases=["login", "signin", "sign_in", "signup", "sign_up", "authentication",
                 "user_account", "account", "session", "password", "logout"],
    ),
    Category(
        name="booking",
        description="Reserving a slot in time: create, list, cancel.",
        aliases=["reservation", "appointment", "slot", "schedule_booking", "table_booking"],
    ),
    Category(
        name="catalog",
        description="Browsing a set of things: listing, detail, search, filter.",
        aliases=["listing", "product", "menu", "inventory", "directory", "browse"],
    ),
    Category(
        name="content",
        description="Written content someone publishes and readers read.",
        aliases=["post", "article", "blog", "page_content", "cms", "note"],
    ),
    Category(
        name="messaging",
        description="People sending things to each other or being told about them.",
        aliases=["message", "chat", "comment", "notification", "inbox", "thread"],
    ),
    Category(
        name="payment",
        description="Taking money: checkout, deposits, subscriptions, invoices.",
        aliases=["checkout", "billing", "invoice", "subscription", "deposit", "order_payment"],
    ),
    Category(
        name="profile",
        description="A person's own record and settings.",
        aliases=["account_settings", "preference", "avatar", "member_profile"],
    ),
    Category(
        name="scheduling",
        description="Times, availability and opening hours — the rules behind a booking.",
        aliases=["availability", "opening_hours", "calendar", "timeslot", "shift"],
    ),
    Category(
        name="upload",
        description="Files and images going in, and being served back out.",
        aliases=["file", "media", "image_upload", "attachment", "document"],
    ),
    Category(
        name="admin",
        description="The back-office view: managing what everyone else uses.",
        aliases=["dashboard", "back_office", "management", "moderation"],
    ),
)


class CategoryRegistry(BaseModel):
    """Every category the library recognises, plus anything proposed."""

    categories: list[Category] = Field(default_factory=lambda: list(SEED_CATEGORIES))

    def names(self) -> list[str]:
        return sorted(c.name for c in self.categories if c.confirmed)

    def get(self, name: str) -> Category | None:
        needle = _normalise(name)
        return next((c for c in self.categories if _normalise(c.name) == needle), None)

    def usable(self) -> list[Category]:
        """Confirmed categories only.

        A proposed category is a question, not an answer: matching against one
        would let a single unreviewed build create the split the registry exists
        to prevent.
        """
        return [c for c in self.categories if c.confirmed]

    def resolve(self, *terms: str) -> str:
        """The canonical category for these words, or "" if none is recognised.

        Terms are tried in the order given — most specific first — so a package
        about `booking` in an app that also mentions users lands in `booking`.
        """
        for term in terms:
            for word in _words(term):
                for category in self.usable():
                    if category.matches(word):
                        return category.name
        return UNCATEGORISED

    def propose(self, name: str, description: str = "") -> Category:
        """Record a new category as a question for a person.

        Unconfirmed, so nothing matches against it yet. This is the ONLY way the
        registry grows, and it is deliberately visible.
        """
        existing = self.get(name)
        if existing:
            return existing
        proposed = Category(
            name=_normalise(name) or "uncategorised",
            description=description,
            seeded=False,
            confirmed=False,
        )
        self.categories.append(proposed)
        return proposed

    def confirm(self, name: str) -> Category | None:
        category = self.get(name)
        if category:
            category.confirmed = True
        return category


def normalise(term: str) -> str:
    """Public form of the category-name normaliser — a slug, singularised."""
    return _normalise(term)


def _normalise(term: str) -> str:
    """A category term, in one shape. Singularised so `bookings` finds `booking`."""
    slug = re.sub(r"[^a-z0-9]+", "_", term.strip().lower()).strip("_")
    if not slug:
        return ""
    parts = slug.split("_")
    parts[-1] = singularize(parts[-1])
    return "_".join(parts)


def _words(term: str) -> list[str]:
    """The whole term first, then its parts, then each part canonicalised.

    Whole-term first matters: `opening_hours` is an alias of `scheduling`, and
    splitting it up first would match `hour` against nothing and lose it.
    """
    whole = _normalise(term)
    if not whole:
        return []
    parts = whole.split("_")
    canonical = [canonical_name(p) for p in parts]
    return [whole, *reversed(parts), *reversed(canonical)]


def default_registry() -> CategoryRegistry:
    return CategoryRegistry()
