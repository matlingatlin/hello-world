"""Architecture validation — run BEFORE anything is generated (docs/LAYER-B.md).

These rule checks catch design errors for the price of a function call, where the
vision loop would catch them for the price of a full build. An unresolved
violation is a signal to go back to the wizard surgically, naming the exact spec
field at fault.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from .architecture import Architecture, AuthMode


class Severity(StrEnum):
    error = "error"  # blocks generation
    warning = "warning"  # generation may proceed; surfaced honestly


class Violation(BaseModel):
    rule: str
    severity: Severity = Severity.error
    message: str
    spec_field: str = ""  # which Layer A field to reopen in the wizard
    subject: str = ""  # the offending node


class ValidationResult(BaseModel):
    valid: bool
    violations: list[Violation] = Field(default_factory=list)

    @property
    def errors(self) -> list[Violation]:
        return [v for v in self.violations if v.severity is Severity.error]

    @property
    def fields_to_revisit(self) -> list[str]:
        """Spec fields the wizard should reopen — the surgical edit list."""
        seen: list[str] = []
        for violation in self.errors:
            if violation.spec_field and violation.spec_field not in seen:
                seen.append(violation.spec_field)
        return seen


def _check_operations_hit_valid_entities(arch: Architecture) -> list[Violation]:
    tables = arch.data_model.table_names()
    out: list[Violation] = []
    for op in arch.operations:
        if not op.entity:
            out.append(
                Violation(
                    rule="action_references_entity",
                    message=(
                        f"Operation '{op.name}' ({op.description!r}) doesn't act on any known "
                        "entity — the data model has nothing for it to work with."
                    ),
                    spec_field="entities",
                    subject=op.name,
                )
            )
        elif op.entity not in tables:
            out.append(
                Violation(
                    rule="action_references_entity",
                    message=(
                        f"Operation '{op.name}' acts on '{op.entity}', which is not a table "
                        f"in the data model ({', '.join(sorted(tables)) or 'no tables'})."
                    ),
                    spec_field="entities",
                    subject=op.name,
                )
            )
    return out


def _check_permissions_map_to_operations(arch: Architecture) -> list[Violation]:
    operations = arch.operation_names()
    roles = arch.auth_access.role_names()
    out: list[Violation] = []
    for perm in arch.auth_access.permissions:
        if perm.operation not in operations:
            out.append(
                Violation(
                    rule="permission_maps_to_operation",
                    message=(
                        f"Permission for role '{perm.role}' grants '{perm.operation}', "
                        "which is not an operation in the architecture."
                    ),
                    spec_field="role_permissions",
                    subject=f"{perm.role}:{perm.operation}",
                )
            )
        if perm.role not in roles:
            out.append(
                Violation(
                    rule="permission_maps_to_role",
                    message=(
                        f"Permission references role '{perm.role}', which is not "
                        "one of the app's roles."
                    ),
                    spec_field="users_and_roles",
                    subject=f"{perm.role}:{perm.operation}",
                )
            )
    return out


def _check_no_login_conflict(arch: Architecture) -> list[Violation]:
    """"No sign-in" plus per-user data or multiple roles cannot both hold: the app
    would have to tell users apart without ever identifying them."""
    if arch.auth_access.mode is not AuthMode.none:
        return []

    out: list[Violation] = []
    if len(arch.auth_access.roles) > 1:
        out.append(
            Violation(
                rule="no_login_vs_roles",
                message=(
                    "The app has no sign-in, but defines several roles "
                    f"({', '.join(sorted(arch.auth_access.role_names()))}). Without accounts "
                    "there is no way to tell those users apart."
                ),
                spec_field="sign_in",
                subject="auth_access",
            )
        )

    owner_scoped = [p for p in arch.auth_access.permissions if p.scope == "own"]
    if owner_scoped:
        out.append(
            Violation(
                rule="no_login_vs_user_specific_data",
                message=(
                    "The app has no sign-in, but grants access to users' own records. "
                    "Owning a record requires an identified user."
                ),
                spec_field="sign_in",
                subject="auth_access",
            )
        )
    return out


def _check_relations_resolve(arch: Architecture) -> list[Violation]:
    tables = arch.data_model.table_names()
    out: list[Violation] = []
    for table in arch.data_model.tables:
        for relation in table.relations:
            if relation.to_table not in tables:
                out.append(
                    Violation(
                        rule="relation_resolves",
                        message=(
                            f"Table '{table.name}' has a foreign key '{relation.from_column}' "
                            f"pointing at '{relation.to_table}', which does not exist."
                        ),
                        spec_field="entities",
                        subject=f"{table.name}.{relation.from_column}",
                    )
                )
                continue
            if relation.from_column not in table.column_names():
                out.append(
                    Violation(
                        rule="relation_column_exists",
                        message=(
                            f"Table '{table.name}' declares a relation on column "
                            f"'{relation.from_column}', which the table does not have."
                        ),
                        spec_field="entities",
                        subject=f"{table.name}.{relation.from_column}",
                    )
                )
                continue
            target = arch.data_model.get(relation.to_table)
            if target and relation.to_column not in target.column_names():
                out.append(
                    Violation(
                        rule="relation_target_column_exists",
                        message=(
                            f"'{table.name}.{relation.from_column}' points at "
                            f"'{relation.to_table}.{relation.to_column}', which does not exist."
                        ),
                        spec_field="entities",
                        subject=f"{table.name}.{relation.from_column}",
                    )
                )
    return out


def _check_screens_reference_real_operations(arch: Architecture) -> list[Violation]:
    operations = arch.operation_names()
    return [
        Violation(
            rule="screen_references_operation",
            severity=Severity.warning,
            message=(
                f"Screen '{screen.name}' lists operation '{op}', which is not in the "
                "architecture."
            ),
            spec_field="key_actions",
            subject=screen.name,
        )
        for screen in arch.screens_routing.screens
        for op in screen.operations
        if op not in operations
    ]


def _check_something_to_build(arch: Architecture) -> list[Violation]:
    out: list[Violation] = []
    if not arch.data_model.tables:
        out.append(
            Violation(
                rule="has_entities",
                message="The architecture has no tables — there is nothing to build.",
                spec_field="entities",
                subject="data_model",
            )
        )
    if not arch.operations:
        out.append(
            Violation(
                rule="has_operations",
                message="The architecture has no operations — the app would do nothing.",
                spec_field="key_actions",
                subject="operations",
            )
        )
    return out


def validate_architecture(arch: Architecture) -> ValidationResult:
    """All rule checks. `valid` is False when any error-severity rule fires."""
    violations = [
        *_check_something_to_build(arch),
        *_check_operations_hit_valid_entities(arch),
        *_check_permissions_map_to_operations(arch),
        *_check_no_login_conflict(arch),
        *_check_relations_resolve(arch),
        *_check_screens_reference_real_operations(arch),
    ]
    has_error = any(v.severity is Severity.error for v in violations)
    return ValidationResult(valid=not has_error, violations=violations)
