from scio_engine.intake.gate import (
    assumed_fields,
    downstream_tags,
    is_buildable,
    triggered_conditionals,
)
from scio_engine.intake.schema import (
    AppSpec,
    Contradiction,
    DataSensitivity,
    DownstreamTag,
    FieldMeta,
    Source,
    TriggerSignals,
)


def full_spec(**overrides) -> AppSpec:
    """A fully-answered single-role booking app (the doc's running example)."""
    base = dict(
        purpose=FieldMeta(value="Guests book a table and get a confirmation."),
        users_and_roles=FieldMeta(value=["guests"]),
        entities=FieldMeta(value=["bookings", "tables", "guests"]),
        key_actions=FieldMeta(value=["book", "cancel"]),
        sign_in=FieldMeta(value="none — name + phone"),
        data_ownership_sensitivity=FieldMeta(value=DataSensitivity(owner="you", sensitive=False)),
        non_goals=FieldMeta(value=["no payments for now"]),
    )
    base.update(overrides)
    return AppSpec(**base)


class TestIsBuildable:
    def test_fully_answered_spec_is_buildable(self):
        result = is_buildable(full_spec())
        assert result.buildable
        assert result.missing_core == []
        assert result.unresolved_conditionals == []
        assert result.contradictions == []

    def test_missing_core_field_blocks(self):
        result = is_buildable(full_spec(entities=None))
        assert not result.buildable
        assert result.missing_core == ["entities"]

    def test_triggered_but_unresolved_conditional_blocks(self):
        spec = full_spec(users_and_roles=FieldMeta(value=["guests", "staff"]))
        result = is_buildable(spec)
        assert not result.buildable
        assert result.unresolved_conditionals == ["role_permissions"]

    def test_resolved_conditional_unblocks(self):
        spec = full_spec(
            users_and_roles=FieldMeta(value=["guests", "staff"]),
            role_permissions=FieldMeta(value="staff see today's list; guests only their own"),
        )
        assert is_buildable(spec).buildable

    def test_defaulted_and_flagged_core_field_counts_as_satisfied(self):
        spec = full_spec(
            sign_in=FieldMeta(value="none — name + phone", source=Source.default)
        )
        result = is_buildable(spec)
        assert result.buildable
        assert "sign_in" in assumed_fields(spec)

    def test_unresolved_contradiction_blocks_and_is_reported(self):
        spec = full_spec()
        spec.contradictions.append(
            Contradiction(
                fields=["sign_in", "role_permissions"],
                description="No sign-in, but staff-only views require identifying staff.",
            )
        )
        result = is_buildable(spec)
        assert not result.buildable
        assert len(result.contradictions) == 1

    def test_resolved_contradiction_does_not_block(self):
        spec = full_spec()
        spec.contradictions.append(
            Contradiction(fields=["sign_in"], description="resolved earlier", resolved=True)
        )
        assert is_buildable(spec).buildable


class TestTriggers:
    def test_multiple_roles_triggers_role_permissions(self):
        spec = full_spec(users_and_roles=FieldMeta(value=["guests", "staff"]))
        assert "role_permissions" in triggered_conditionals(spec)

    def test_single_role_does_not_trigger(self):
        assert "role_permissions" not in triggered_conditionals(full_spec())

    def test_signals_fire_their_branches(self):
        spec = full_spec()
        spec.signals = TriggerSignals(
            charges_money=True,
            mentions_notifications=True,
            external_integrations=True,
            uploads_media=True,
            public_content=True,
            multi_language=True,
            scheduling_logic=True,
        )
        triggered = triggered_conditionals(spec)
        assert set(triggered) == {
            "payment",
            "notifications",
            "integrations",
            "media",
            "visibility_seo",
            "localization",
            "scheduling",
        }

    def test_sensitive_data_answer_derives_compliance_trigger(self):
        spec = full_spec(
            data_ownership_sensitivity=FieldMeta(
                value=DataSensitivity(owner="you", sensitive=True, kinds=["personal"])
            )
        )
        assert "compliance" in triggered_conditionals(spec)

    def test_untriggered_conditionals_never_block(self):
        # payment etc. unresolved but never triggered -> buildable
        assert is_buildable(full_spec()).buildable


class TestDownstreamTags:
    def test_core_field_mapping_matches_the_doc(self):
        tags = downstream_tags(full_spec())
        assert "entities" in tags[DownstreamTag.data_model]
        assert "key_actions" in tags[DownstreamTag.functions_routing]
        assert "sign_in" in tags[DownstreamTag.auth]
        assert "users_and_roles" in tags[DownstreamTag.access_rules]
        assert "data_ownership_sensitivity" in tags[DownstreamTag.security_compliance]
        assert "non_goals" in tags[DownstreamTag.scope]
        assert "look" in tags[DownstreamTag.design_tokens]

    def test_unfilled_fields_are_not_tagged(self):
        tags = downstream_tags(full_spec())
        # payment is not filled -> must not appear anywhere
        assert all("payment" not in fields for fields in tags.values())

    def test_filled_conditional_is_tagged(self):
        spec = full_spec(payment=FieldMeta(value="Stripe; charges per booking"))
        tags = downstream_tags(spec)
        assert "payment" in tags[DownstreamTag.connectors]
        assert "payment" in tags[DownstreamTag.security_compliance]


class TestAssumedFields:
    def test_defaults_are_flagged_assumed(self):
        assumed = assumed_fields(full_spec())
        for name in ("platform", "data_owner", "look", "publishing", "security_and_a11y", "scale"):
            assert name in assumed

    def test_stated_fields_are_not_assumed(self):
        assert "purpose" not in assumed_fields(full_spec())
