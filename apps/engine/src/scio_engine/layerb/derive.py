"""Deterministic derivation: AppSpec (Layer A) -> architecture graph.

"Deterministic-first; LLM only for judgment" (docs/LAYER-B.md). Everything rules
can guarantee is done here — schema from entities, auth from sign_in, RBAC from
roles, screens/operations from actions, security posture from sensitivity. No
model call happens in this module, which is exactly why the backbone is testable
and reproducible.
"""

from __future__ import annotations

import re

from ..intake.schema import AppSpec
from .architecture import (
    Architecture,
    AuthAccess,
    AuthMode,
    Column,
    Connector,
    DataModel,
    DesignTokens,
    FieldType,
    Operation,
    Permission,
    Relation,
    Role,
    Screen,
    ScreensRouting,
    SecurityPosture,
    Table,
)
from .vocabulary import Vocabulary, canonical_name, slugify

# Verbs we recognise in a key action, mapped to the operation verb.
_VERB_SYNONYMS: dict[str, str] = {
    "book": "create",
    "create": "create",
    "add": "create",
    "make": "create",
    "register": "create",
    "submit": "create",
    "cancel": "cancel",
    "delete": "delete",
    "remove": "delete",
    "edit": "update",
    "update": "update",
    "change": "update",
    "reschedule": "update",
    "see": "list",
    "view": "list",
    "list": "list",
    "browse": "list",
    "search": "search",
    "find": "search",
    "approve": "approve",
    "confirm": "approve",
    "pay": "pay",
    "upload": "upload",
    "export": "export",
}

# Verbs that name the thing they produce: "book a table" creates a *booking*.
# Without this the incidental noun ("table") would be read as the target entity.
_VERB_IMPLIES_ENTITY: dict[str, str] = {
    "book": "booking",
    "reserve": "booking",
    "order": "order",
    "pay": "payment",
    "review": "review",
    "message": "message",
    "comment": "comment",
    "rate": "rating",
}

_STOPWORDS = {
    "a", "an", "the", "their", "his", "her", "its", "our", "your", "my",
    "for", "of", "to", "in", "on", "at", "with", "and", "or", "own",
    "all", "any", "some", "today", "todays", "new", "up",
}

# Columns every table gets — the shape generated code can rely on.
def _base_columns() -> list[Column]:
    return [
        Column(name="id", type=FieldType.uuid, description="Primary key"),
        Column(name="created_at", type=FieldType.timestamp, description="Row created"),
        Column(name="updated_at", type=FieldType.timestamp, description="Row last changed"),
    ]


def _guess_columns(entity: str) -> list[Column]:
    """A small, honest starting shape per entity.

    Rules only guess what the name clearly implies; the LLM pass and the design
    stage refine the rest. Guessing less is better than guessing wrong.
    """
    columns = _base_columns()
    if entity in {"booking", "order", "appointment"}:
        columns += [
            Column(name="starts_at", type=FieldType.timestamp, description="When it starts"),
            Column(name="party_size", type=FieldType.integer, nullable=True),
            Column(
                name="status",
                type=FieldType.enum,
                description="pending | confirmed | cancelled",
            ),
        ]
    elif entity in {"guest", "user", "person", "staff", "customer"}:
        columns += [
            Column(name="name", type=FieldType.text),
            Column(name="email", type=FieldType.text, nullable=True),
            Column(name="phone", type=FieldType.text, nullable=True),
        ]
    else:
        columns += [
            Column(name="name", type=FieldType.text),
            Column(name="description", type=FieldType.text, nullable=True),
        ]
    return columns


def derive_data_model(spec: AppSpec, vocab: Vocabulary) -> DataModel:
    """entities -> tables (+ relations between entities the app manages)."""
    entities = spec.entities.value if spec.entities else []
    names = [vocab.add(e) for e in entities]
    names = [n for n in names if n]

    tables = [Table(name=name, columns=_guess_columns(name)) for name in names]

    # A booking-like table references the actor and resource tables when they exist.
    for table in tables:
        if table.name in {"booking", "order", "appointment"}:
            for other in names:
                if other == table.name:
                    continue
                if other in {"guest", "user", "person", "customer", "staff"} or other in {
                    "table",
                    "room",
                    "seat",
                    "resource",
                    "slot",
                }:
                    column = f"{other}_id"
                    table.columns.append(
                        Column(
                            name=column,
                            type=FieldType.uuid,
                            nullable=True,
                            description=f"References {other}",
                        )
                    )
                    table.relations.append(Relation(from_column=column, to_table=other))
    return DataModel(tables=tables)


def _auth_mode(sign_in_value: str) -> AuthMode:
    text = sign_in_value.lower()
    if any(token in text for token in ("no account", "no sign", "no login", "none", "without")):
        return AuthMode.none
    if "google" in text or "github" in text or "oauth" in text or "social" in text:
        return AuthMode.oauth
    if "link" in text or "magic" in text or "email" in text:
        return AuthMode.email_link
    if "password" in text:
        return AuthMode.password
    return AuthMode.email_link


def derive_auth_access(spec: AppSpec, vocab: Vocabulary, operations: list[Operation]) -> AuthAccess:
    """sign_in -> auth mode; roles -> RBAC.

    No sign-in means no auth tables at all: users are identified by the contact
    details they type (name/phone), per docs/LAYER-B.md.
    """
    sign_in = spec.sign_in.value if spec.sign_in else ""
    mode = _auth_mode(sign_in)

    identity_fields: list[str] = []
    if mode is AuthMode.none:
        text = sign_in.lower()
        for candidate, column in (("name", "name"), ("phone", "phone"), ("email", "email")):
            if candidate in text:
                identity_fields.append(column)
        if not identity_fields:
            identity_fields = ["name", "phone"]

    role_terms = spec.users_and_roles.value if spec.users_and_roles else []
    roles = [Role(name=vocab.add(r), description=r) for r in role_terms if canonical_name(r)]

    # Default RBAC skeleton: every role may run every operation, scoped to its own
    # rows unless it is clearly a staff/admin role. Refined at the design stage.
    permissions: list[Permission] = []
    if len(roles) > 1:
        elevated = {"staff", "administrator", "owner", "manager"}
        for role in roles:
            scope = "all" if role.name in elevated else "own"
            for op in operations:
                permissions.append(Permission(role=role.name, operation=op.name, scope=scope))

    return AuthAccess(
        mode=mode,
        provider="supabase-auth" if mode is not AuthMode.none else "",
        identifies_users=mode is not AuthMode.none,
        identity_fields=identity_fields,
        roles=roles,
        permissions=permissions,
    )


def _match_entity(words: list[str], entity_names: list[str], vocab: Vocabulary) -> str | None:
    """Which entity an action is about.

    A verb can name its own object: "book a table" creates a *booking*, not a
    table, even though "table" is the noun in the phrase. So a verb that
    canonicalises to a known entity wins over one merely mentioned later.
    """
    canonical_words = [vocab.resolve(w) for w in words]

    for word in words:
        implied = _VERB_IMPLIES_ENTITY.get(word)
        if implied and implied in entity_names:
            return implied

    for name in entity_names:
        if name in canonical_words:
            return name
    return None


def derive_operations(spec: AppSpec, vocab: Vocabulary, entity_names: list[str]) -> list[Operation]:
    """key_actions -> typed operations with inputs/outputs.

    An action naming no known entity still becomes an operation, with an empty
    entity — validation then reports it, which is the honest outcome: the wizard
    asked for something the data model can't serve.
    """
    actions = spec.key_actions.value if spec.key_actions else []
    operations: list[Operation] = []

    for action in actions:
        words = [w for w in re.split(r"[^A-Za-z0-9]+", action.lower()) if w and w not in _STOPWORDS]
        if not words:
            continue

        verb = next((_VERB_SYNONYMS[w] for w in words if w in _VERB_SYNONYMS), None) or slugify(
            words[0]
        )
        entity = _match_entity(words, entity_names, vocab)
        target = entity or (entity_names[0] if entity_names and not entity else "")

        name = f"{verb}_{entity}" if entity else slugify(action)[:60]
        if any(op.name == name for op in operations):
            continue

        if verb in {"list", "search"}:
            inputs = [Column(name="filter", type=FieldType.json, nullable=True)]
            outputs = [f"{entity or target}[]"]
        elif verb in {"create", "update"}:
            inputs = [Column(name="payload", type=FieldType.json)]
            outputs = [entity or target]
        elif verb in {"cancel", "delete", "approve"}:
            inputs = [Column(name="id", type=FieldType.uuid)]
            outputs = [entity or target]
        else:
            inputs = [Column(name="payload", type=FieldType.json, nullable=True)]
            outputs = [entity or target]

        operations.append(
            Operation(
                name=name,
                verb=verb,
                entity=entity or "",
                inputs=inputs,
                outputs=[o for o in outputs if o],
                description=action,
            )
        )
    return operations


def derive_screens(spec: AppSpec, operations: list[Operation]) -> ScreensRouting:
    """actions -> screens + navigation. One screen per operation group, plus a home."""
    screens: list[Screen] = [
        Screen(name="Home", route="/", purpose="Entry point and orientation", operations=[])
    ]

    by_entity: dict[str, list[Operation]] = {}
    for op in operations:
        by_entity.setdefault(op.entity or "general", []).append(op)

    for entity, ops in by_entity.items():
        if entity == "general":
            for op in ops:
                screens.append(
                    Screen(
                        name=op.name.replace("_", " ").title(),
                        route=f"/{op.name.replace('_', '-')}",
                        purpose=op.description,
                        operations=[op.name],
                    )
                )
            continue

        creates = [op for op in ops if op.verb in {"create", "update"}]
        lists = [op for op in ops if op.verb in {"list", "search"}]
        others = [op for op in ops if op not in creates and op not in lists]

        if creates:
            screens.append(
                Screen(
                    name=f"New {entity}".title(),
                    route=f"/{entity}/new",
                    purpose=f"Create a {entity}",
                    operations=[op.name for op in creates],
                )
            )
        if lists or others:
            screens.append(
                Screen(
                    name=f"{entity} list".title(),
                    route=f"/{entity}",
                    purpose=f"See and manage {entity} records",
                    operations=[op.name for op in [*lists, *others]],
                )
            )
    return ScreensRouting(screens=screens)


def derive_connectors(spec: AppSpec) -> list[Connector]:
    """integrations / payment / notifications / media -> connectors."""
    connectors: list[Connector] = []
    if spec.payment:
        connectors.append(
            Connector(
                name="payment",
                kind="payment",
                detail=spec.payment.value,
                secrets=["PAYMENT_PROVIDER_SECRET_KEY"],
                source_field="payment",
            )
        )
    if spec.notifications:
        connectors.append(
            Connector(
                name="notifications",
                kind="notifications",
                detail=spec.notifications.value,
                secrets=["NOTIFICATIONS_API_KEY"],
                source_field="notifications",
            )
        )
    if spec.integrations:
        connectors.append(
            Connector(
                name="integrations",
                kind="integration",
                detail=spec.integrations.value,
                source_field="integrations",
            )
        )
    if spec.media:
        connectors.append(
            Connector(
                name="storage",
                kind="storage",
                detail=spec.media.value,
                source_field="media",
            )
        )
    return connectors


def derive_security_posture(spec: AppSpec) -> SecurityPosture:
    """sensitivity -> secure defaults. Always on; sensitivity only adds to them."""
    sensitivity = spec.data_ownership_sensitivity.value if spec.data_ownership_sensitivity else None
    notes: list[str] = []
    if spec.compliance:
        notes.append(spec.compliance.value)
    if sensitivity and sensitivity.sensitive:
        notes.append(
            "Sensitive data present — consent, minimal retention and extra access care required."
        )
    return SecurityPosture(
        row_level_security=True,
        data_owner=(sensitivity.owner if sensitivity else spec.data_owner.value),
        sensitive=bool(sensitivity and sensitivity.sensitive),
        sensitive_kinds=list(sensitivity.kinds) if sensitivity else [],
        compliance_notes=notes,
    )


def derive_design_tokens(spec: AppSpec) -> DesignTokens:
    """look / brand -> tokens. Reference RAG (4.6) will replace these defaults
    with values extracted from uploaded colour/font references."""
    look = spec.look.value if spec.look else "Scio default"
    is_default = spec.look.is_assumed if spec.look else True
    return DesignTokens(
        source="scio_default" if is_default else "stated",
        palette={"primary": "#0B5563", "surface": "#F5F7F6", "ink": "#14181C"},
        typography={"display": "Space Grotesk", "body": "IBM Plex Sans", "mono": "IBM Plex Mono"},
        radius={"card": "7px", "control": "5px"},
        notes=look,
    )


def derive_architecture(spec: AppSpec) -> Architecture:
    """The full deterministic backbone. No LLM involved."""
    vocab = Vocabulary()

    data_model = derive_data_model(spec, vocab)
    entity_names = sorted(data_model.table_names())

    operations = derive_operations(spec, vocab, entity_names)
    auth_access = derive_auth_access(spec, vocab, operations)
    screens = derive_screens(spec, operations)

    return Architecture(
        data_model=data_model,
        auth_access=auth_access,
        screens_routing=screens,
        operations=operations,
        connectors=derive_connectors(spec),
        security_posture=derive_security_posture(spec),
        design_tokens=derive_design_tokens(spec),
        vocabulary=vocab.canonical,
        scope_guard=list(spec.non_goals.value) if spec.non_goals else [],
    )
