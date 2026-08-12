"""Answers that cannot both be true.

Detected by rules, not by judgment: "you said no sign-in, but also that each
guest sees only their own bookings" is a fact about two fields, and a rule that
finds it is reproducible and free.

What happens next is the important part. A contradiction is never resolved by
guessing which answer the user "really" meant — the gate stays shut and the
wizard asks. Guessing here is how an app quietly ends up with an auth system
nobody asked for, or without one it needed.
"""

from __future__ import annotations

import re

from .schema import AppSpec, Contradiction

# "no account", "inget konto", "ingen inloggning" — the phrasings that mean
# there is no sign-in at all. Kept small and literal on purpose.
_NO_SIGN_IN = re.compile(
    r"\b(no|without|none|inget|ingen|utan)\b.{0,20}\b"
    r"(account|sign[- ]?in|login|log[- ]?in|auth|konto|inloggning)\b",
    re.IGNORECASE,
)

_PER_USER = re.compile(
    r"\b(own|only their|per user|per guest|their own|mina|egna|sina egna)\b",
    re.IGNORECASE,
)

_PAYMENT_WORDS = re.compile(
    r"\b(pay|payment|checkout|deposit|invoice|subscription|betal\w*|faktura)\b",
    re.IGNORECASE,
)

_SENSITIVE_KINDS = {"payment", "personal", "health", "financial", "biometric"}


def _text_of(spec: AppSpec, name: str) -> str:
    field = getattr(spec, name, None)
    if field is None:
        return ""
    value = field.value
    if isinstance(value, list):
        return " ; ".join(str(v) for v in value)
    return str(value)


def _has_no_sign_in(spec: AppSpec) -> bool:
    return bool(_NO_SIGN_IN.search(_text_of(spec, "sign_in")))


def detect(spec: AppSpec) -> list[Contradiction]:
    """Every conflict the current answers contain. Pure — no spec mutation."""
    found: list[Contradiction] = []

    if _has_no_sign_in(spec):
        roles = spec.users_and_roles.value if spec.users_and_roles else []
        if len(roles) > 1:
            found.append(
                Contradiction(
                    fields=["sign_in", "users_and_roles"],
                    description=(
                        f"You said there is no sign-in, but also that there are several kinds "
                        f"of user ({', '.join(roles)}). Without sign-in the app cannot tell "
                        "them apart."
                    ),
                )
            )
        per_user = _PER_USER.search(
            " ".join(_text_of(spec, name) for name in ("key_actions", "role_permissions"))
        )
        if per_user:
            found.append(
                Contradiction(
                    fields=["sign_in", "key_actions"],
                    description=(
                        "You said there is no sign-in, but also that people should see their "
                        "own data. Something has to identify them for that to work."
                    ),
                )
            )

    sensitivity = spec.data_ownership_sensitivity
    if sensitivity is not None:
        kinds = {k.strip().lower() for k in sensitivity.value.kinds}
        if not sensitivity.value.sensitive and kinds & _SENSITIVE_KINDS:
            found.append(
                Contradiction(
                    fields=["data_ownership_sensitivity"],
                    description=(
                        f"You said none of the data is sensitive, but also named "
                        f"{', '.join(sorted(kinds & _SENSITIVE_KINDS))} data. Those usually "
                        "count as sensitive."
                    ),
                )
            )

    non_goals = _text_of(spec, "non_goals")
    if _PAYMENT_WORDS.search(non_goals):
        wants_payment = spec.signals.charges_money or _PAYMENT_WORDS.search(
            _text_of(spec, "key_actions")
        )
        if wants_payment:
            found.append(
                Contradiction(
                    fields=["non_goals", "key_actions"],
                    description=(
                        "You listed payments as something to skip for now, but the app is also "
                        "meant to take payment. Which of the two should hold?"
                    ),
                )
            )

    return found


def merge(spec: AppSpec, found: list[Contradiction]) -> list[Contradiction]:
    """Carry resolutions forward: a conflict the user already settled stays settled.

    Matched on the fields involved, so re-detecting the same conflict after a new
    answer does not re-open a question the user has already answered — while a
    genuinely new conflict still surfaces.
    """
    resolved = {tuple(sorted(c.fields)) for c in spec.contradictions if c.resolved}
    merged: list[Contradiction] = [c for c in spec.contradictions if c.resolved]
    for contradiction in found:
        key = tuple(sorted(contradiction.fields))
        if key in resolved:
            continue
        merged.append(contradiction)
    return merged
