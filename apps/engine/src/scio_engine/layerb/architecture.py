"""Output 2 of Layer B — the machine-readable architecture graph (docs/LAYER-B.md).

Not prose: a typed graph whose nodes are each sliceable, because Layer C
decomposes it into build packages and the vision loop checks generated code
against it. Every node records which spec field it came from, so a change
upstream can be traced to the parts of the architecture it touches.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class FieldType(StrEnum):
    uuid = "uuid"
    text = "text"
    integer = "integer"
    decimal = "decimal"
    boolean = "boolean"
    timestamp = "timestamp"
    date = "date"
    json = "json"
    enum = "enum"


class Column(BaseModel):
    name: str
    type: FieldType
    nullable: bool = False
    description: str = ""


class Relation(BaseModel):
    """A foreign key. `to_table` must resolve to a table in the graph —
    validation checks exactly that."""

    from_column: str
    to_table: str
    to_column: str = "id"
    kind: str = "many_to_one"


class Table(BaseModel):
    name: str  # canonical, singular
    columns: list[Column] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    row_level_security: bool = True
    source_field: str = "entities"

    def column_names(self) -> set[str]:
        return {c.name for c in self.columns}


class DataModel(BaseModel):
    tables: list[Table] = Field(default_factory=list)

    def table_names(self) -> set[str]:
        return {t.name for t in self.tables}

    def get(self, name: str) -> Table | None:
        return next((t for t in self.tables if t.name == name), None)


class AuthMode(StrEnum):
    none = "none"  # no accounts — identify by contact details
    email_link = "email_link"
    password = "password"
    oauth = "oauth"


class Role(BaseModel):
    name: str
    description: str = ""


class Permission(BaseModel):
    """Who may run which operation. `operation` must name a real operation."""

    role: str
    operation: str
    scope: str = "own"  # "own" | "all"


class AuthAccess(BaseModel):
    mode: AuthMode = AuthMode.none
    provider: str = ""  # e.g. "supabase-auth" (ADR-0011)
    identifies_users: bool = False
    identity_fields: list[str] = Field(default_factory=list)  # when mode == none
    roles: list[Role] = Field(default_factory=list)
    permissions: list[Permission] = Field(default_factory=list)
    source_field: str = "sign_in"

    def role_names(self) -> set[str]:
        return {r.name for r in self.roles}


class Operation(BaseModel):
    """A typed unit of behaviour derived from a key action: what it does, to
    which entity, and what it takes and returns. Layer C turns these into
    routes/handlers; the vision loop checks them."""

    name: str  # canonical, snake_case, e.g. "create_booking"
    verb: str
    entity: str  # must resolve to a table
    inputs: list[Column] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    description: str = ""
    source_field: str = "key_actions"


class Screen(BaseModel):
    name: str
    route: str
    purpose: str = ""
    operations: list[str] = Field(default_factory=list)
    requires_role: str | None = None
    source_field: str = "key_actions"


class ScreensRouting(BaseModel):
    screens: list[Screen] = Field(default_factory=list)

    def routes(self) -> set[str]:
        return {s.route for s in self.screens}


class Connector(BaseModel):
    """An outside system the app talks to (payment, notifications, storage,
    integrations)."""

    name: str
    kind: str  # "payment" | "notifications" | "storage" | "integration"
    detail: str = ""
    secrets: list[str] = Field(default_factory=list)
    source_field: str = ""


class SecurityPosture(BaseModel):
    """Secure-by-default settings, derived rather than left to the LLM — this is
    the wedge (ADR-0001), so it must not depend on a model remembering."""

    row_level_security: bool = True
    data_owner: str = "you"
    sensitive: bool = False
    sensitive_kinds: list[str] = Field(default_factory=list)
    input_validation: bool = True
    secrets_in_env_only: bool = True
    accessibility_baseline: bool = True
    compliance_notes: list[str] = Field(default_factory=list)
    source_field: str = "data_ownership_sensitivity"


class DesignTokens(BaseModel):
    """The look. Reference RAG (4.6) later replaces the defaults with extracted
    palette/font values; the shape stays the same."""

    source: str = "scio_default"
    palette: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    radius: dict[str, str] = Field(default_factory=dict)
    notes: str = ""
    source_field: str = "look"


class Architecture(BaseModel):
    """The whole graph. Sliceable: Layer C takes one node (or one table +
    its operations) plus the relevant "why" as a build package's context."""

    data_model: DataModel = Field(default_factory=DataModel)
    auth_access: AuthAccess = Field(default_factory=AuthAccess)
    screens_routing: ScreensRouting = Field(default_factory=ScreensRouting)
    operations: list[Operation] = Field(default_factory=list)
    connectors: list[Connector] = Field(default_factory=list)
    security_posture: SecurityPosture = Field(default_factory=SecurityPosture)
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)
    vocabulary: dict[str, list[str]] = Field(default_factory=dict)
    scope_guard: list[str] = Field(default_factory=list)  # non_goals

    def operation_names(self) -> set[str]:
        return {op.name for op in self.operations}
