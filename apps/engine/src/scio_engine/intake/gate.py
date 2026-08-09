"""The "buildable enough" gate and wizard helpers (docs/INTAKE-SCHEMA.md, ADR-0010).

Buildable when: every core field is answered or defaulted-and-flagged; every
triggered conditional branch is resolved; no unresolved contradictions.
Momentum over completeness — the rest defaults and is refined later.
"""

from pydantic import BaseModel, Field

from .schema import (
    CONDITIONAL_FIELDS,
    CORE_FIELDS,
    FIELD_TAGS,
    AppSpec,
    Contradiction,
    DownstreamTag,
    FieldMeta,
)


class BuildableResult(BaseModel):
    buildable: bool
    missing_core: list[str] = Field(default_factory=list)
    unresolved_conditionals: list[str] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)


def triggered_conditionals(spec: AppSpec) -> list[str]:
    """Which conditional branches the current answers have triggered — this is
    what tells the wizard what still needs asking. Triggers are explicit signals
    (set by extraction later) plus two derived from core answers: multiple roles
    and sensitive data."""
    triggers: list[str] = []

    roles = spec.users_and_roles.value if spec.users_and_roles else []
    if len(roles) > 1:
        triggers.append("role_permissions")
    if spec.signals.charges_money:
        triggers.append("payment")
    if spec.signals.mentions_notifications:
        triggers.append("notifications")
    if spec.signals.external_integrations:
        triggers.append("integrations")
    if spec.signals.uploads_media:
        triggers.append("media")
    sensitive = spec.signals.sensitive_data or (
        spec.data_ownership_sensitivity is not None
        and spec.data_ownership_sensitivity.value.sensitive
    )
    if sensitive:
        triggers.append("compliance")
    if spec.signals.public_content:
        triggers.append("visibility_seo")
    if spec.signals.multi_language:
        triggers.append("localization")
    if spec.signals.scheduling_logic:
        triggers.append("scheduling")

    return triggers


def is_buildable(spec: AppSpec) -> BuildableResult:
    """The spec-gate rule. A core field counts as satisfied whether stated,
    derived, or explicitly defaulted-and-flagged (source=default) — the flag is
    what makes the assumption honest, not a blocker."""
    missing_core = [name for name in CORE_FIELDS if getattr(spec, name) is None]

    unresolved = [
        name for name in triggered_conditionals(spec) if getattr(spec, name) is None
    ]

    open_contradictions = [c for c in spec.contradictions if not c.resolved]

    return BuildableResult(
        buildable=not missing_core and not unresolved and not open_contradictions,
        missing_core=missing_core,
        unresolved_conditionals=unresolved,
        contradictions=open_contradictions,
    )


def downstream_tags(spec: AppSpec) -> dict[DownstreamTag, list[str]]:
    """Map filled fields -> the downstream build areas they feed. The foundation
    Layer C consumes when decomposing the build."""
    result: dict[DownstreamTag, list[str]] = {}
    for name, tags in FIELD_TAGS.items():
        field = getattr(spec, name, None)
        if not isinstance(field, FieldMeta):
            continue
        for tag in tags:
            result.setdefault(tag, []).append(name)
    return result


def assumed_fields(spec: AppSpec) -> list[str]:
    """Fields currently carried by a flagged default — what the spec gate shows
    with an "assumed" tag."""
    names = [*CORE_FIELDS, *CONDITIONAL_FIELDS, "non_goals", *_defaulted()]
    out: list[str] = []
    for name in names:
        field = getattr(spec, name, None)
        if isinstance(field, FieldMeta) and field.is_assumed:
            out.append(name)
    return out


def _defaulted() -> tuple[str, ...]:
    from .schema import DEFAULTED_FIELDS

    return DEFAULTED_FIELDS
