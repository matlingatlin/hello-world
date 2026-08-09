"""Validation catches design errors before a single token is spent."""

from conftest import make_booking_spec as booking_spec
from scio_engine.layerb.architecture import (
    Architecture,
    AuthAccess,
    AuthMode,
    Column,
    DataModel,
    FieldType,
    Operation,
    Permission,
    Relation,
    Role,
    Screen,
    ScreensRouting,
    Table,
)
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerb.validate import Severity, validate_architecture


def table(name: str, extra: list[Column] | None = None) -> Table:
    return Table(
        name=name,
        columns=[
            Column(name="id", type=FieldType.uuid),
            Column(name="created_at", type=FieldType.timestamp),
            *(extra or []),
        ],
    )


def rules_fired(result) -> set[str]:
    return {v.rule for v in result.violations}


class TestHappyPath:
    def test_a_derived_architecture_validates(self):
        result = validate_architecture(derive_architecture(booking_spec()))
        assert result.valid, [v.message for v in result.violations]
        assert result.errors == []


class TestActionsHitValidEntities:
    def test_operation_on_a_missing_entity_is_an_error(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_invoice", verb="create", entity="invoice")],
        )
        result = validate_architecture(arch)
        assert not result.valid
        assert "action_references_entity" in rules_fired(result)
        assert "entities" in result.fields_to_revisit

    def test_operation_with_no_entity_at_all_is_an_error(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="do_something", verb="export", entity="")],
        )
        assert not validate_architecture(arch).valid


class TestPermissionsMapToOperations:
    def test_permission_on_a_non_existent_operation_is_an_error(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
            auth_access=AuthAccess(
                mode=AuthMode.email_link,
                identifies_users=True,
                roles=[Role(name="staff")],
                permissions=[Permission(role="staff", operation="delete_universe", scope="all")],
            ),
        )
        result = validate_architecture(arch)
        assert not result.valid
        assert "permission_maps_to_operation" in rules_fired(result)
        assert "role_permissions" in result.fields_to_revisit

    def test_permission_for_an_unknown_role_is_an_error(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
            auth_access=AuthAccess(
                mode=AuthMode.email_link,
                identifies_users=True,
                roles=[Role(name="staff")],
                permissions=[Permission(role="ghost", operation="create_booking", scope="all")],
            ),
        )
        result = validate_architecture(arch)
        assert "permission_maps_to_role" in rules_fired(result)
        assert "users_and_roles" in result.fields_to_revisit


class TestNoLoginConflicts:
    def test_no_login_plus_several_roles_is_an_error(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
            auth_access=AuthAccess(
                mode=AuthMode.none,
                roles=[Role(name="guest"), Role(name="staff")],
            ),
        )
        result = validate_architecture(arch)
        assert not result.valid
        assert "no_login_vs_roles" in rules_fired(result)
        assert "sign_in" in result.fields_to_revisit

    def test_no_login_plus_user_specific_data_is_an_error(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
            auth_access=AuthAccess(
                mode=AuthMode.none,
                roles=[Role(name="guest")],
                permissions=[Permission(role="guest", operation="create_booking", scope="own")],
            ),
        )
        result = validate_architecture(arch)
        assert not result.valid
        assert "no_login_vs_user_specific_data" in rules_fired(result)

    def test_the_same_shape_with_sign_in_is_fine(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
            auth_access=AuthAccess(
                mode=AuthMode.email_link,
                identifies_users=True,
                roles=[Role(name="guest"), Role(name="staff")],
                permissions=[Permission(role="guest", operation="create_booking", scope="own")],
            ),
        )
        assert validate_architecture(arch).valid

    def test_derived_no_login_with_two_roles_is_caught_end_to_end(self):
        """The realistic version: the wizard says 'no account' but names two roles."""
        spec = booking_spec()
        spec.users_and_roles.value = ["guests", "staff"]
        spec.role_permissions = None
        result = validate_architecture(derive_architecture(spec))
        assert not result.valid
        assert "no_login_vs_roles" in rules_fired(result)


class TestRelationsResolve:
    def test_dangling_foreign_key_is_an_error(self):
        booking = table("booking", [Column(name="venue_id", type=FieldType.uuid)])
        booking.relations = [Relation(from_column="venue_id", to_table="venue")]
        arch = Architecture(
            data_model=DataModel(tables=[booking]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
        )
        result = validate_architecture(arch)
        assert not result.valid
        assert "relation_resolves" in rules_fired(result)

    def test_relation_on_a_column_the_table_lacks_is_an_error(self):
        booking = table("booking")
        booking.relations = [Relation(from_column="guest_id", to_table="guest")]
        arch = Architecture(
            data_model=DataModel(tables=[booking, table("guest")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
        )
        result = validate_architecture(arch)
        assert "relation_column_exists" in rules_fired(result)

    def test_relation_to_a_missing_target_column_is_an_error(self):
        booking = table("booking", [Column(name="guest_id", type=FieldType.uuid)])
        booking.relations = [
            Relation(from_column="guest_id", to_table="guest", to_column="external_ref")
        ]
        arch = Architecture(
            data_model=DataModel(tables=[booking, table("guest")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
        )
        result = validate_architecture(arch)
        assert "relation_target_column_exists" in rules_fired(result)


class TestEmptyAndWarnings:
    def test_an_empty_architecture_has_nothing_to_build(self):
        result = validate_architecture(Architecture())
        assert not result.valid
        assert {"has_entities", "has_operations"} <= rules_fired(result)

    def test_a_screen_referencing_a_ghost_operation_is_only_a_warning(self):
        arch = Architecture(
            data_model=DataModel(tables=[table("booking")]),
            operations=[Operation(name="create_booking", verb="create", entity="booking")],
            screens_routing=ScreensRouting(
                screens=[Screen(name="Ghost", route="/ghost", operations=["nope"])]
            ),
        )
        result = validate_architecture(arch)
        assert result.valid  # warnings don't block
        assert any(v.severity is Severity.warning for v in result.violations)
