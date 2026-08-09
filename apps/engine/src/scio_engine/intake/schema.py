"""Layer A — the intake schema for the app type, from docs/INTAKE-SCHEMA.md (ADR-0010).

Typed slots the wizard/extraction (4.3, later) fills. Every field carries metadata
(value, source, confidence, provenance) and maps to the downstream build area(s) it
feeds. This module is schema only — no extraction, no LLM calls.
"""

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Source(StrEnum):
    stated = "stated"
    derived = "derived"
    default = "default"


class Confidence(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class DownstreamTag(StrEnum):
    data_model = "data_model"
    functions_routing = "functions_routing"
    auth = "auth"
    access_rules = "access_rules"
    security_compliance = "security_compliance"
    connectors = "connectors"
    design_tokens = "design_tokens"
    scope = "scope"


class FieldMeta(BaseModel, Generic[T]):
    """A filled intake slot: the value plus where it came from and how sure we are.

    Powers the spec gate's "assumed" tags (source == default), surgical
    single-field edits, and provenance back to wizard messages.
    """

    value: T
    source: Source = Source.stated
    confidence: Confidence = Confidence.medium
    provenance: list[str] = Field(default_factory=list)  # wizard message ids

    @property
    def is_assumed(self) -> bool:
        return self.source == Source.default


class DataSensitivity(BaseModel):
    """Structured value for data_ownership_sensitivity."""

    owner: str = "you"
    sensitive: bool = False
    kinds: list[str] = Field(default_factory=list)  # e.g. ["payment", "personal", "health"]


class Contradiction(BaseModel):
    """Detected conflict between answers; blocks the gate until resolved."""

    fields: list[str]
    description: str
    resolved: bool = False


class TriggerSignals(BaseModel):
    """Signals that fire conditional follow-ups.

    Extraction (4.3) will set these from the conversation; until then callers set
    them explicitly. multiple_roles and sensitive_data are ALSO derived from the
    core answers (users_and_roles, data_ownership_sensitivity) — see gate.py.
    """

    charges_money: bool = False
    mentions_notifications: bool = False
    external_integrations: bool = False
    uploads_media: bool = False
    sensitive_data: bool = False
    public_content: bool = False
    multi_language: bool = False
    scheduling_logic: bool = False


class AppSpec(BaseModel):
    """The intake spec for one app project. All wizard-filled slots optional (None =
    not yet provided); defaulted-and-flagged slots come pre-filled with source=default."""

    # --- core fields (required unless defaulted-and-flagged) ---
    purpose: FieldMeta[str] | None = None
    users_and_roles: FieldMeta[list[str]] | None = None
    entities: FieldMeta[list[str]] | None = None
    key_actions: FieldMeta[list[str]] | None = None
    sign_in: FieldMeta[str] | None = None
    data_ownership_sensitivity: FieldMeta[DataSensitivity] | None = None

    # --- conditional follow-ups (asked only when a trigger fires) ---
    role_permissions: FieldMeta[str] | None = None
    payment: FieldMeta[str] | None = None
    notifications: FieldMeta[str] | None = None
    integrations: FieldMeta[str] | None = None
    media: FieldMeta[str] | None = None
    compliance: FieldMeta[str] | None = None
    visibility_seo: FieldMeta[str] | None = None
    localization: FieldMeta[str] | None = None
    scheduling: FieldMeta[str] | None = None

    # --- non-goals (always asked; empty list is a valid answer) ---
    non_goals: FieldMeta[list[str]] | None = None

    # --- defaulted-and-flagged (assumed unless stated; shown as "assumed") ---
    platform: FieldMeta[str] = FieldMeta(value="responsive web app", source=Source.default)
    data_owner: FieldMeta[str] = FieldMeta(value="you", source=Source.default)
    look: FieldMeta[str] = FieldMeta(value="Scio default", source=Source.default)
    publishing: FieldMeta[str] = FieldMeta(value="Scio URL first", source=Source.default)
    security_and_a11y: FieldMeta[str] = FieldMeta(
        value="secure defaults + accessible by default", source=Source.default
    )
    scale: FieldMeta[str] = FieldMeta(value="small-to-moderate", source=Source.default)

    # --- extraction bookkeeping ---
    signals: TriggerSignals = Field(default_factory=TriggerSignals)
    contradictions: list[Contradiction] = Field(default_factory=list)


CORE_FIELDS: tuple[str, ...] = (
    "purpose",
    "users_and_roles",
    "entities",
    "key_actions",
    "sign_in",
    "data_ownership_sensitivity",
)

CONDITIONAL_FIELDS: tuple[str, ...] = (
    "role_permissions",
    "payment",
    "notifications",
    "integrations",
    "media",
    "compliance",
    "visibility_seo",
    "localization",
    "scheduling",
)

DEFAULTED_FIELDS: tuple[str, ...] = (
    "platform",
    "data_owner",
    "look",
    "publishing",
    "security_and_a11y",
    "scale",
)

# Downstream tag map from docs/INTAKE-SCHEMA.md ("Downstream tag -> build area").
# media maps to connectors + access_rules (the doc says "storage + access";
# storage rides with connectors in the tag enum). Defaulted fields not listed in
# the doc's map are tagged with the closest area (interpolations, marked below).
FIELD_TAGS: dict[str, tuple[DownstreamTag, ...]] = {
    "purpose": (DownstreamTag.scope,),
    "users_and_roles": (DownstreamTag.access_rules, DownstreamTag.functions_routing),
    "entities": (DownstreamTag.data_model,),
    "key_actions": (DownstreamTag.functions_routing,),
    "sign_in": (DownstreamTag.auth,),
    "data_ownership_sensitivity": (DownstreamTag.security_compliance,),
    "role_permissions": (DownstreamTag.access_rules,),
    "payment": (DownstreamTag.connectors, DownstreamTag.security_compliance),
    "notifications": (DownstreamTag.functions_routing, DownstreamTag.connectors),
    "integrations": (DownstreamTag.connectors,),
    "media": (DownstreamTag.connectors, DownstreamTag.access_rules),
    "compliance": (DownstreamTag.security_compliance,),
    "visibility_seo": (DownstreamTag.functions_routing, DownstreamTag.design_tokens),
    "localization": (DownstreamTag.functions_routing,),
    "scheduling": (DownstreamTag.functions_routing, DownstreamTag.data_model),
    "non_goals": (DownstreamTag.scope,),
    "look": (DownstreamTag.design_tokens,),
    # interpolated (not in the doc's map):
    "platform": (DownstreamTag.functions_routing,),
    "data_owner": (DownstreamTag.security_compliance,),
    "publishing": (DownstreamTag.connectors,),
    "security_and_a11y": (DownstreamTag.security_compliance,),
    "scale": (DownstreamTag.data_model,),
}
