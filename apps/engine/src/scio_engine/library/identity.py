"""What an entry IS: its id, its status, and the contract that decides matching.

Three things the first slice of the library did without, and could not grow
without:

**An id that means something.** `category.seqno.version` — `booking.1.1`. The
category says what area of an app this covers, the seqno says which entry within
it, the version says how many times it has been improved. The seqno is assigned
by the store, never by the process proposing the entry, because two builds
finishing at once would otherwise both claim `booking.2`.

**A status.** Anything the library learns from a real build is PROVISIONAL until
a person says otherwise. A seed entry was written and reviewed deliberately; a
contributed one was extracted from one project's code by a pipeline. Treating
those as equal is how a curated library quietly becomes a scrapyard.

**A contract.** This is the part that makes matching and de-duplication
deterministic rather than a judgment call. A contract is what an entry DOES,
with every project-specific word removed: the canonical operations, the routes
and the files, all written against `__ENTITY__`. Two things with the same
contract are the same thing — for assembling into a build, and for deciding
whether a candidate is a new version of something the library already has.

The contract deliberately excludes the entity. "Bookings" and "appointments"
produce identical contracts, which is exactly right: one blueprint serves both,
and that is what the library is for.
"""

from __future__ import annotations

import hashlib
import re
from enum import StrEnum

from pydantic import BaseModel, Field

from ..layerb.vocabulary import canonical_name, singularize
from .placeholders import ENTITY

ID_PATTERN = re.compile(r"^(?P<category>[a-z][a-z0-9_]*)\.(?P<seqno>\d+)\.(?P<version>\d+)$")


class Status(StrEnum):
    """How much authority an entry carries.

    `provisional` is offerable — a contributed entry that cleared every gate is
    genuinely usable, and holding it back until someone clicks approve would
    mean the library never grows in practice. What `provisional` changes is that
    it is visible AS provisional, everywhere, and a seed never silently becomes
    indistinguishable from a machine's extraction.
    """

    provisional = "provisional"
    approved = "approved"
    rejected = "rejected"


class EntryId(BaseModel):
    """`category.seqno.version`, parsed."""

    category: str
    seqno: int
    version: int = 1

    def __str__(self) -> str:
        return f"{self.category}.{self.seqno}.{self.version}"

    @property
    def line(self) -> str:
        """The id without its version — the identity that survives improvement."""
        return f"{self.category}.{self.seqno}"

    def bumped(self) -> EntryId:
        return EntryId(category=self.category, seqno=self.seqno, version=self.version + 1)

    @classmethod
    def parse(cls, raw: str) -> EntryId | None:
        """Parse, or None. Seed ids like `feature-booking` are not entry ids and
        must not be coerced into looking like one."""
        match = ID_PATTERN.match(raw.strip())
        if not match:
            return None
        return cls(
            category=match["category"],
            seqno=int(match["seqno"]),
            version=int(match["version"]),
        )


OPERATION_ENTITY = "entity"
"""What the entity becomes inside an operation name.

Not `__ENTITY__`: `create_booking` would become `create___ENTITY__`, three
underscores deep, which is unreadable in a contract anyone has to look at. Paths
keep `__ENTITY__` because those have to match an entry's file templates
literally.
"""


def entity_forms(entity: str) -> list[str]:
    """Every spelling of the project's entity that could appear in its own code.

    The project wrote "appointments"; Layer B canonicalised it to "booking"; the
    file plan used the singular. All three appear somewhere, and a contract that
    generalised only one of them would keep the project's own word — which is
    both a leak and a match key nothing else can ever equal.

    Longest first, so replacing "bookings" never leaves a stray "s".
    """
    raw = entity.strip().lower()
    singulars = {singularize(raw), singularize(canonical_name(raw) or raw)}
    forms = {raw, *singulars} | {f"{s}s" for s in singulars if s}
    return sorted((f for f in forms if f), key=len, reverse=True)


def _blank(forms: list[str], text: str, placeholder: str) -> str:
    """Replace every spelling of the entity with the placeholder.

    The boundary is "not a letter or a digit", NOT `\b`: an operation is called
    `create_booking`, and `\b` treats the underscore as a word character, so the
    obvious regex silently matches nothing and every contract stays
    project-specific.
    """
    for form in forms:
        text = re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(form)}(?![A-Za-z0-9])", placeholder, text
        )
    return text


def _generalize_term(term: str, forms: list[str]) -> str:
    """One operation name, lowercased and generalised."""
    return _blank(forms, term.strip().lower(), OPERATION_ENTITY)


def _generalize_path(path: str, forms: list[str]) -> str:
    return _blank(forms, path, ENTITY)


class Contract(BaseModel):
    """What a thing does, with the project's own words taken out.

    Sorted and de-duplicated on construction so two orderings of the same
    contract cannot hash differently — the whole value of this object is that
    equality is decidable.
    """

    operations: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)

    @classmethod
    def of(
        cls,
        *,
        operations: list[str],
        routes: list[str],
        files: list[str],
        entity: str = "",
    ) -> Contract:
        """Build a contract, generalising away `entity` as it goes."""
        # Every spelling, not just the canonical one: a project that says
        # "appointments" must produce the same contract as one that says
        # "bookings", or the library learns the same blueprint twice.
        forms = entity_forms(entity) if entity else []
        return cls(
            operations=sorted({_generalize_term(op, forms) for op in operations if op.strip()}),
            routes=sorted({_generalize_path(r, forms) for r in routes if r.strip()}),
            files=sorted({_generalize_path(f, forms) for f in files if f.strip()}),
        )

    @property
    def key(self) -> str:
        """A stable identity for this contract. Equality of keys IS a match."""
        payload = "|".join(
            [
                ",".join(self.operations),
                ",".join(self.routes),
                ",".join(self.files),
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def satisfied_by(self, other: Contract) -> bool:
        """Whether `other` can build this — the assemble-vs-generate question.

        Not equality, and the asymmetry is deliberate. An entry may provide MORE
        than a package needs (the booking blueprint lists as well as creates and
        cancels, and a package that only creates and cancels is still built
        correctly by it). It may never provide less: the missing operation would
        silently vanish from the app.

        The files must be exactly the plan, though. Anything else and the
        manifest's package→file map disagrees with the disk, which is the drift
        the sandbox spike punished.

        De-duplication asks a different question and uses `key` equality: two
        entries with the same contract are the same thing, and "does more" is
        then a reason to keep one rather than to hold both.
        """
        if self.empty or other.empty:
            return False
        return (
            set(self.operations) <= set(other.operations)
            and set(self.routes) <= set(other.routes)
            and set(self.files) == set(other.files)
        )

    @property
    def empty(self) -> bool:
        """A contract with no operations claims nothing, and must never match.

        Two empty contracts would otherwise hash identically and every
        uncharacterised package would 'match' every other one.
        """
        return not self.operations

    def describe(self) -> str:
        return f"{', '.join(self.operations) or 'nothing'} over {len(self.files)} files"
