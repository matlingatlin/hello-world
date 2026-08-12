"""The field guide — one place that knows what each intake slot is and how to ask for it.

Straight out of docs/INTAKE-SCHEMA.md, including the doc's own examples. Both the
extractor (what may be filled, and in what shape) and the question writer (what to
ask, with an example) read from here, so the two can never drift apart — and so a
question still has an example when the model's answer is unusable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import CONDITIONAL_FIELDS, CORE_FIELDS


@dataclass(frozen=True)
class FieldGuide:
    """What a slot holds, and how a person would be asked for it."""

    name: str
    kind: str  # "text" | "list" | "sensitivity"
    question: str
    example: str

    @property
    def shape(self) -> str:
        return {
            "text": "a single sentence (string)",
            "list": "a list of short strings",
            "sensitivity": '{"owner": string, "sensitive": bool, "kinds": [string]}',
        }[self.kind]


GUIDES: dict[str, FieldGuide] = {
    "purpose": FieldGuide(
        name="purpose",
        kind="text",
        question="What does the app do?",
        example="Guests book a table and get a confirmation.",
    ),
    "users_and_roles": FieldGuide(
        name="users_and_roles",
        kind="list",
        question="Who uses it — and is there more than one kind of user?",
        example="Guests, and staff who see today's list.",
    ),
    "entities": FieldGuide(
        name="entities",
        kind="list",
        question="What are the core things the app manages?",
        example="Bookings, tables, guests.",
    ),
    "key_actions": FieldGuide(
        name="key_actions",
        kind="list",
        question="What should users be able to do?",
        example="Book a table, cancel a booking; staff see today's list.",
    ),
    "sign_in": FieldGuide(
        name="sign_in",
        kind="text",
        question="Do users sign in, and how?",
        example="No account — just name and phone. Or: an email link. Or: Google.",
    ),
    "data_ownership_sensitivity": FieldGuide(
        name="data_ownership_sensitivity",
        kind="sensitivity",
        question="Who owns the data, and is any of it sensitive (payment, personal, health)?",
        example="I own it; no payment data, but guests' phone numbers are personal.",
    ),
    "non_goals": FieldGuide(
        name="non_goals",
        kind="list",
        question="Is there anything you deliberately want to skip, for now?",
        example="No payments yet; no mobile app.",
    ),
    "role_permissions": FieldGuide(
        name="role_permissions",
        kind="text",
        question="What should each kind of user be able to see and do?",
        example="Guests see only their own booking; staff see every booking for today.",
    ),
    "payment": FieldGuide(
        name="payment",
        kind="text",
        question="What gets charged, and through which provider?",
        example="A deposit per booking, through Stripe.",
    ),
    "notifications": FieldGuide(
        name="notifications",
        kind="text",
        question="What should trigger a notification, and on which channel?",
        example="An email confirmation when a booking is made.",
    ),
    "integrations": FieldGuide(
        name="integrations",
        kind="text",
        question="Which outside service should it connect to, and what data moves?",
        example="Google Calendar — each booking becomes an event.",
    ),
    "media": FieldGuide(
        name="media",
        kind="text",
        question="What files get uploaded, and who may see them?",
        example="Dish photos, uploaded by staff, visible to everyone.",
    ),
    "compliance": FieldGuide(
        name="compliance",
        kind="text",
        question="Does the sensitive data need consent or any extra care?",
        example="Guests tick a consent box; delete phone numbers after 90 days.",
    ),
    "visibility_seo": FieldGuide(
        name="visibility_seo",
        kind="text",
        question="What is public, and should it be findable in search?",
        example="The menu is public and should rank on Google; bookings are private.",
    ),
    "localization": FieldGuide(
        name="localization",
        kind="text",
        question="Which languages or regions does it need to cover?",
        example="Swedish and English.",
    ),
    "scheduling": FieldGuide(
        name="scheduling",
        kind="text",
        question="What are the rules for time — opening hours, slots, timezones?",
        example="Sittings every 30 minutes, 17:00-22:00, Stockholm time.",
    ),
}

EXTRACTABLE_FIELDS: tuple[str, ...] = (*CORE_FIELDS, "non_goals", *CONDITIONAL_FIELDS)
"""Every slot extraction may fill. The defaulted-and-flagged fields (platform,
look, scale, ...) are deliberately absent: they are assumptions the product makes
out loud, and letting extraction quietly overwrite one would erase the "assumed"
tag that makes it honest. A user who states a preference gets it captured when
those fields become editable at the review screen."""

SIGNAL_HINTS: dict[str, str] = {
    "charges_money": "the app takes payment, deposits, fees or subscriptions",
    "mentions_notifications": "email, SMS, push or any other message is sent",
    "external_integrations": "an outside service is involved (calendar, CRM, maps, ...)",
    "uploads_media": "users upload files, images or video",
    "sensitive_data": "personal, health, financial or otherwise sensitive data is handled",
    "public_content": "some content is public / meant to be found",
    "multi_language": "more than one language or region",
    "scheduling_logic": "times, slots, availability or timezones matter",
}


def guide_for(field: str) -> FieldGuide:
    return GUIDES[field]


def field_catalogue() -> str:
    """The extractable slots, as the extractor sees them."""
    lines = []
    for name in EXTRACTABLE_FIELDS:
        guide = GUIDES[name]
        lines.append(f"- {name} ({guide.shape}) — {guide.question} e.g. {guide.example}")
    return "\n".join(lines)


def signal_catalogue() -> str:
    return "\n".join(f"- {name}: true when {why}" for name, why in SIGNAL_HINTS.items())
