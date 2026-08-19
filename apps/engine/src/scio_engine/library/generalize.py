"""Turning one project's code into something the library can lend to the next.

This is the only step in contribute-back where a model is involved, and it is
worth being precise about why. Everything that DECIDES anything — does this
match, is it better, may it be added — is deterministic, because a library that
grows on a model's opinion grows wrong in ways nobody notices for months. What a
model is genuinely good at is the rewriting: taking "Book a table at Bistro
Nord" and producing "Book a __ENTITY_TITLE__" without mangling the code around
it.

Even here it is not trusted. The substitution it should have made is applied
deterministically first, so the model is correcting copy rather than performing
the rename; and everything it returns goes through the contribute gate
(`library/gate.py`) and a real build (`library/reverify.py`) before it is added.
A generalization that drops an id, breaks the code, or leaves the project's own
words in is discarded — the model gets no benefit of the doubt.

If no model is available at all, the deterministic pass stands on its own. It
handles the case that actually matters (the entity's name, everywhere) and the
gate catches what it cannot reach.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from .categories import CategoryRegistry, default_registry, normalise
from .identity import entity_forms
from .placeholders import (
    ENTITY,
    ENTITY_PASCAL,
    ENTITY_PLURAL,
    ENTITY_PLURAL_TITLE,
    ENTITY_TITLE,
)

GENERALIZE_TIMEOUT_S = 300.0
GENERALIZE_MAX_TOKENS = 16000

GENERALIZE_SYSTEM = """You prepare code for Scio's component library. You are given \
files from one working app, already renamed so the app's own concept is written as \
the placeholder __ENTITY__. Your job is the part a rename cannot do: remove what is \
still specific to that one project, so the same files can be dropped into a \
different app about a different thing.

Rules:
- NEVER touch data-scio-id or data-scio-package attributes. They are how a user \
points at code, and losing one breaks the whole product for every project that \
uses this.
- Keep the code working. Same imports, same exports, same behaviour.
- Replace user-visible copy that names a business ("Bistro Nord", "our salon") \
with neutral wording built from __ENTITY_TITLE__ / __ENTITY_PLURAL__.
- Remove hard-coded URLs, emails, keys, prices and addresses.
- Do not add features, comments about Scio, or TODOs.

Return ONLY a JSON object: {"files": {"path": "full file content", ...}, \
"description": "one sentence: what this builds, in general terms"}. Every path you \
were given must appear exactly once."""

SUGGEST_SYSTEM = """You label components for Scio's library. Answer with ONE line of \
JSON and nothing else: {"category": "<one of the listed categories, or the single \
word new>", "hashtags": ["...", "..."], "description": "one sentence"}.

The category MUST be one of the listed names unless none of them fits at all, in \
which case answer exactly "new". Hashtags are lowercase, one or two words, for a \
person browsing — three to six of them."""


class Generalization(BaseModel):
    """The generalized files, plus what the model suggested calling them."""

    files: dict[str, str] = Field(default_factory=dict)
    description: str = ""
    category: str = ""
    proposed_category: str = ""
    hashtags: list[str] = Field(default_factory=list)
    used_model: bool = False
    notes: list[str] = Field(default_factory=list)


def blank_entity(text: str, entity: str) -> str:
    """Every spelling of the project's entity, replaced with the placeholders.

    Done here rather than asked of a model because it is exactly the kind of
    mechanical, total substitution a model does *almost* completely — and one
    missed occurrence is a project's own word shipped to everyone else.

    Two boundaries, not one. Before the word: not a letter or digit. After it:
    not a lowercase letter or digit — which lets `BookingForm` generalise to
    `__ENTITY_PASCAL__Form` instead of surviving intact because `Form` follows
    with no separator. Camel case is how a project's word hides.
    """
    forms = entity_forms(entity)
    if not forms:
        return text

    def replace(word: str, placeholder: str, subject: str) -> str:
        return re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(word)}(?![a-z0-9])", placeholder, subject
        )

    # Longest and most-specific first, always: replacing "booking" before
    # "bookings" would leave a stray "s", and lowercase before title case would
    # leave "Booking" untouched.
    for form in forms:
        plural = form if form.endswith("s") else f"{form}s"
        for word, placeholder in (
            (plural.title(), ENTITY_PLURAL_TITLE),
            (plural, ENTITY_PLURAL),
            (form.title(), ENTITY_TITLE),
            (_pascal(form), ENTITY_PASCAL),
            (form, ENTITY),
        ):
            text = replace(word, placeholder, text)
    return text


def _pascal(term: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", term) if part)


_PACKAGE_ATTRIBUTE = re.compile(r'\s*data-scio-package="[^"]*"')


def strip_package_tags(text: str) -> str:
    """Remove `data-scio-package` — it belongs to a project, not to an entry.

    The ids are the entry's: they are how any project's user points at this
    code. The package tag says which build package owns the element in ONE app,
    and the assembler stamps it fresh (`core/stamping.py`). Carrying it into the
    library would ship `pkg_feature_booking` into an app that has no such
    package, and the instrumentation verifier would reject the build — which is
    exactly what re-verification caught the first time this was tried.
    """
    return _PACKAGE_ATTRIBUTE.sub("", text)


def blank_files(files: dict[str, str], entity: str) -> dict[str, str]:
    """The deterministic half of generalization: paths and bodies."""
    return {
        blank_entity(path, entity): strip_package_tags(blank_entity(body, entity))
        for path, body in files.items()
    }


def _extract_json(text: str) -> dict | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw = fenced.group(1) if fenced else text
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _keeps_the_ids(before: str, after: str) -> bool:
    """Every data-scio-id in the original is still there afterwards."""
    ids = re.findall(r'data-scio-id="([^"]+)"', before)
    return all(f'data-scio-id="{i}"' in after for i in ids)


async def generalize(
    files: dict[str, str],
    *,
    entity: str,
    registry: ProviderRegistry,
    categories: CategoryRegistry | None = None,
    project_terms: list[str] | None = None,
) -> Generalization:
    """Prepare one package's files for the library."""
    blanked = blank_files(files, entity)
    result = Generalization(files=blanked)

    if registry.is_fake:
        # No model: the deterministic pass stands alone. It covers the case that
        # matters, and the gate refuses whatever it could not reach.
        result.notes.append("no model available — deterministic generalization only")
        return result

    listing = "\n\n".join(
        f"FILE: {path}\n```\n{body}\n```" for path, body in sorted(blanked.items())
    )
    terms = ", ".join(t for t in (project_terms or []) if t.strip())
    prompt = (
        f"## Files\n\n{listing}\n\n"
        + (f"## This project's own words, which must not survive\n{terms}\n\n" if terms else "")
        + "Return the JSON object described in your instructions."
    )

    try:
        reply = await run_relay(
            "codegen",
            prompt,
            registry=registry,
            options=RelayOptions(
                passes=1,
                system=GENERALIZE_SYSTEM,
                max_tokens=GENERALIZE_MAX_TOKENS,
                timeout_s=GENERALIZE_TIMEOUT_S,
            ),
        )
    except Exception as exc:
        result.notes.append(f"generalization model call failed ({type(exc).__name__}) — "
                            "kept the deterministic result")
        return result

    parsed = _extract_json(reply.final_text)
    proposed = (parsed or {}).get("files")
    if not isinstance(proposed, dict) or set(proposed) != set(blanked):
        result.notes.append(
            "the model returned a different set of files — kept the deterministic result"
        )
        return result

    lost = [
        path
        for path, body in blanked.items()
        if not _keeps_the_ids(body, str(proposed.get(path, "")))
    ]
    if lost:
        # A lost id is a failed build (B039). Here it would be worse: every
        # future project assembling this entry would inherit the hole.
        result.notes.append(f"the model dropped instrumentation in {', '.join(lost)} — "
                            "kept the deterministic result")
        return result

    result.files = {path: str(body) for path, body in proposed.items()}
    result.description = str((parsed or {}).get("description", "")).strip()
    result.used_model = True
    return result


async def suggest_labels(
    description: str,
    files: dict[str, str],
    *,
    registry: ProviderRegistry,
    categories: CategoryRegistry | None = None,
) -> tuple[str, str, list[str]]:
    """(category, proposed_category, hashtags) — asked only when it is ambiguous.

    The deterministic mapping is tried first by the caller. This runs when it
    found nothing, and even then the answer is constrained: a category must come
    from the registry's list, or the model says "new" and a PROPOSAL is
    recorded for a person rather than a category being invented.
    """
    book = categories or default_registry()
    names = book.names()
    listing = ", ".join(names)
    sample = "\n\n".join(
        f"FILE: {path}\n{body[:1200]}" for path, body in sorted(files.items())[:4]
    )
    prompt = (
        f"## Categories\n{listing}\n\n## What this is\n{description}\n\n## Code\n{sample}\n"
    )
    try:
        reply = await run_relay(
            "spec_extraction",
            prompt,
            registry=registry,
            options=RelayOptions(passes=1, system=SUGGEST_SYSTEM, max_tokens=400),
        )
    except Exception:
        return "", "", []

    parsed = _extract_json(reply.final_text) or {}
    raw = str(parsed.get("category", "")).strip().lower()
    hashtags = [
        str(t).strip().lower().replace(" ", "-")
        for t in parsed.get("hashtags", [])
        if str(t).strip()
    ][:6]

    if raw and raw != "new":
        # Resolved through the registry, never taken at face value: a model
        # answering "logins" must land on `auth`, not create a category.
        resolved = book.resolve(raw)
        if resolved:
            return resolved, "", hashtags
    # Nothing recognised: propose a NAME, and only a name. Letting a sentence
    # through here would end up in an entry id.
    return "", normalise(raw) if raw and raw != "new" else "", hashtags
