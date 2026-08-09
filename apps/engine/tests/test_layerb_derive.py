"""Deterministic backbone — every assertion here runs without any LLM."""

from conftest import make_booking_spec as booking_spec
from scio_engine.intake.schema import DataSensitivity, FieldMeta, Source
from scio_engine.layerb.architecture import AuthMode
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerb.vocabulary import Vocabulary, canonical_name


class TestVocabulary:
    def test_plurals_and_case_collapse_to_one_name(self):
        assert canonical_name("Bookings") == "booking"
        assert canonical_name("booking") == "booking"
        assert canonical_name("BOOKING") == "booking"

    def test_synonyms_collapse_to_one_name(self):
        assert canonical_name("reservations") == "booking"
        assert canonical_name("appointment") == "booking"
        assert canonical_name("customers") == "guest"

    def test_irregular_plurals(self):
        assert canonical_name("people") == "person"
        assert canonical_name("children") == "child"

    def test_ies_and_ches_plurals(self):
        assert canonical_name("categories") == "category"
        assert canonical_name("batches") == "batch"

    def test_words_ending_in_ss_are_not_stripped(self):
        assert canonical_name("address") == "address"

    def test_multiword_terms_become_snake_case(self):
        assert canonical_name("Table reservations!") == "table_reservation"

    def test_vocabulary_keeps_the_user_terms_as_aliases(self):
        vocab = Vocabulary.from_terms(["Bookings", "reservation", "Tables"])
        assert vocab.names() == ["booking", "table"]
        assert "Bookings" in vocab.canonical["booking"]
        assert "reservation" in vocab.canonical["booking"]


class TestDataModel:
    def test_entities_become_singular_canonical_tables(self):
        arch = derive_architecture(booking_spec())
        assert arch.data_model.table_names() == {"booking", "table", "guest"}

    def test_every_table_has_id_and_timestamps_with_rls_on(self):
        arch = derive_architecture(booking_spec())
        for table in arch.data_model.tables:
            assert {"id", "created_at", "updated_at"} <= table.column_names()
            assert table.row_level_security is True

    def test_booking_relates_to_guest_and_table(self):
        arch = derive_architecture(booking_spec())
        booking = arch.data_model.get("booking")
        targets = {r.to_table for r in booking.relations}
        assert targets == {"guest", "table"}
        for relation in booking.relations:
            assert relation.from_column in booking.column_names()

    def test_variant_terms_do_not_create_duplicate_tables(self):
        arch = derive_architecture(
            booking_spec(entities=FieldMeta(value=["bookings", "Booking", "reservations"]))
        )
        assert arch.data_model.table_names() == {"booking"}


class TestAuthAccess:
    def test_no_sign_in_means_no_auth_provider_and_contact_identity(self):
        arch = derive_architecture(booking_spec())
        assert arch.auth_access.mode is AuthMode.none
        assert arch.auth_access.identifies_users is False
        assert arch.auth_access.provider == ""
        assert arch.auth_access.identity_fields == ["name", "phone"]

    def test_email_link_sign_in_enables_the_auth_provider(self):
        arch = derive_architecture(booking_spec(sign_in=FieldMeta(value="email link")))
        assert arch.auth_access.mode is AuthMode.email_link
        assert arch.auth_access.identifies_users is True
        assert arch.auth_access.provider == "supabase-auth"
        assert arch.auth_access.identity_fields == []

    def test_google_sign_in_is_oauth(self):
        arch = derive_architecture(booking_spec(sign_in=FieldMeta(value="Google sign-in")))
        assert arch.auth_access.mode is AuthMode.oauth

    def test_roles_become_rbac_with_staff_scoped_to_all(self):
        arch = derive_architecture(
            booking_spec(
                users_and_roles=FieldMeta(value=["guests", "staff"]),
                sign_in=FieldMeta(value="email link"),
            )
        )
        assert arch.auth_access.role_names() == {"guest", "staff"}
        staff = [p for p in arch.auth_access.permissions if p.role == "staff"]
        guest = [p for p in arch.auth_access.permissions if p.role == "guest"]
        assert staff and all(p.scope == "all" for p in staff)
        assert guest and all(p.scope == "own" for p in guest)

    def test_single_role_needs_no_permission_matrix(self):
        arch = derive_architecture(booking_spec())
        assert arch.auth_access.permissions == []


class TestOperationsAndScreens:
    def test_actions_become_typed_operations_on_real_entities(self):
        arch = derive_architecture(booking_spec())
        names = arch.operation_names()
        assert "cancel_booking" in names
        for op in arch.operations:
            assert op.outputs
            assert op.inputs

    def test_a_verb_naming_its_own_object_wins_over_an_incidental_noun(self):
        """"book a table" creates a booking, not a table."""
        arch = derive_architecture(booking_spec())
        create = next(op for op in arch.operations if op.verb == "create")
        assert create.entity == "booking"
        assert create.name == "create_booking"

    def test_list_operations_take_a_filter_and_return_a_collection(self):
        arch = derive_architecture(
            booking_spec(key_actions=FieldMeta(value=["see today's bookings"]))
        )
        op = next(op for op in arch.operations if op.verb == "list")
        assert op.entity == "booking"
        assert [c.name for c in op.inputs] == ["filter"]
        assert op.outputs == ["booking[]"]

    def test_screens_cover_the_operations_and_include_home(self):
        arch = derive_architecture(booking_spec())
        routes = arch.screens_routing.routes()
        assert "/" in routes
        covered = {op for screen in arch.screens_routing.screens for op in screen.operations}
        assert covered == arch.operation_names()

    def test_an_action_with_no_known_entity_still_becomes_an_operation(self):
        arch = derive_architecture(
            booking_spec(key_actions=FieldMeta(value=["export the monthly report"]))
        )
        assert arch.operations
        assert arch.operations[0].entity == ""


class TestConnectorsSecurityTokens:
    def test_no_conditional_fields_means_no_connectors(self):
        assert derive_architecture(booking_spec()).connectors == []

    def test_payment_notifications_and_media_become_connectors(self):
        arch = derive_architecture(
            booking_spec(
                payment=FieldMeta(value="Stripe, per booking"),
                notifications=FieldMeta(value="email on confirmation"),
                media=FieldMeta(value="guests upload photos"),
            )
        )
        kinds = {c.kind for c in arch.connectors}
        assert kinds == {"payment", "notifications", "storage"}
        payment = next(c for c in arch.connectors if c.kind == "payment")
        assert payment.secrets  # secrets are named, never inlined

    def test_security_posture_is_secure_by_default(self):
        posture = derive_architecture(booking_spec()).security_posture
        assert posture.row_level_security is True
        assert posture.input_validation is True
        assert posture.secrets_in_env_only is True
        assert posture.sensitive is False

    def test_sensitive_data_adds_compliance_notes(self):
        arch = derive_architecture(
            booking_spec(
                data_ownership_sensitivity=FieldMeta(
                    value=DataSensitivity(owner="you", sensitive=True, kinds=["personal"])
                )
            )
        )
        assert arch.security_posture.sensitive is True
        assert arch.security_posture.sensitive_kinds == ["personal"]
        assert arch.security_posture.compliance_notes

    def test_design_tokens_flag_the_scio_default(self):
        arch = derive_architecture(booking_spec())
        assert arch.design_tokens.source == "scio_default"
        assert arch.design_tokens.palette and arch.design_tokens.typography

    def test_stated_look_is_not_marked_default(self):
        arch = derive_architecture(
            booking_spec(look=FieldMeta(value="warm and rustic", source=Source.stated))
        )
        assert arch.design_tokens.source == "stated"


class TestScopeAndTraceability:
    def test_non_goals_become_the_scope_guard(self):
        arch = derive_architecture(booking_spec())
        assert arch.scope_guard == ["no payments for now"]

    def test_nodes_record_the_spec_field_they_came_from(self):
        arch = derive_architecture(booking_spec())
        assert arch.data_model.tables[0].source_field == "entities"
        assert arch.auth_access.source_field == "sign_in"
        assert arch.operations[0].source_field == "key_actions"
        assert arch.security_posture.source_field == "data_ownership_sensitivity"

    def test_derivation_is_deterministic(self):
        a = derive_architecture(booking_spec())
        b = derive_architecture(booking_spec())
        assert a.model_dump_json() == b.model_dump_json()
