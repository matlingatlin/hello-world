"""The whole (via the relay, fake-provided), the playbook, and the service."""

import pytest
from fastapi.testclient import TestClient

from conftest import make_booking_spec as booking_spec
from scio_engine.execution.provider import ProviderRegistry, Vendor
from scio_engine.intake.schema import FieldMeta
from scio_engine.layerb.playbook import assemble_build_context, default_playbook
from scio_engine.layerb.service import NotBuildableError, run_layer_b
from scio_engine.layerb.whole import build_prompt, generate_whole, grounding_facts
from scio_engine.main import app

client = TestClient(app)


class TestWholeGrounding:
    def test_grounding_facts_cover_the_answered_fields(self):
        facts = grounding_facts(booking_spec())
        assert "purpose" in facts
        assert "entities" in facts
        assert "guests" in facts["users_and_roles"]

    def test_assumed_fields_are_marked_in_the_grounding(self):
        facts = grounding_facts(booking_spec())
        assert "[assumed]" in facts["look"]  # defaulted-and-flagged
        assert "[assumed]" not in facts["purpose"]  # stated

    def test_the_prompt_only_contains_grounding_facts(self):
        spec = booking_spec()
        prompt = build_prompt(spec)
        assert "Guests book a table" in prompt
        assert "invented feature" not in prompt

    @pytest.mark.asyncio
    async def test_whole_is_generated_through_the_relay(self):
        registry = ProviderRegistry.fake()
        whole = await generate_whole(booking_spec(), registry=registry, passes=2)
        assert whole.generated is True
        assert whole.narrative
        assert len(whole.models_used) == 2
        # the relay actually ran: the fake provider saw both passes
        assert len(registry.get(Vendor.anthropic).calls) == 2

    @pytest.mark.asyncio
    async def test_whole_is_deterministic_with_the_fake_provider(self):
        a = await generate_whole(booking_spec(), registry=ProviderRegistry.fake())
        b = await generate_whole(booking_spec(), registry=ProviderRegistry.fake())
        assert a.narrative == b.narrative

    @pytest.mark.asyncio
    async def test_assumptions_come_from_layer_a_metadata(self):
        whole = await generate_whole(booking_spec(), registry=ProviderRegistry.fake())
        assert "look" in whole.assumptions
        assert "purpose" not in whole.assumptions

    @pytest.mark.asyncio
    async def test_falls_back_to_a_grounded_narrative_when_no_model_answers(self):
        """No provider registered at all — the spec gate still gets something true."""
        whole = await generate_whole(booking_spec(), registry=ProviderRegistry(providers={}))
        assert whole.generated is False
        assert "Guests book a table" in whole.narrative
        assert whole.models_used == []


class TestPlaybook:
    def test_playbook_locks_the_adr_0011_stack(self):
        book = default_playbook()
        assert "Next.js" in book.stack.name
        assert "Supabase" in book.stack.name
        assert book.stack.adr == "ADR-0011"

    def test_playbook_carries_the_house_rules(self):
        book = default_playbook()
        assert book.secure_by_default and book.tests and book.accessibility
        section = book.as_prompt_section()
        assert "Row-level security" in section
        assert "House rules" in section

    def test_build_context_carries_playbook_architecture_and_scope(self):
        from scio_engine.layerb.derive import derive_architecture

        arch = derive_architecture(booking_spec())
        context = assemble_build_context(arch, whole="You are building a booking app.")
        prompt = context.as_prompt()
        assert "House rules" in prompt
        assert "booking" in prompt
        assert "You are building a booking app." in prompt
        assert "no payments for now" in prompt  # the scope guard
        assert "Canonical vocabulary" in prompt


class TestService:
    @pytest.mark.asyncio
    async def test_run_layer_b_returns_all_three_outputs_plus_validation(self):
        result = await run_layer_b(booking_spec(), registry=ProviderRegistry.fake())
        assert result.whole.narrative
        assert result.architecture.data_model.tables
        assert result.playbook.stack.adr == "ADR-0011"
        assert result.validation.valid
        assert result.revisit_fields == []
        assert result.build_context.as_prompt()

    @pytest.mark.asyncio
    async def test_a_non_buildable_spec_is_refused(self):
        spec = booking_spec(entities=None)
        with pytest.raises(NotBuildableError) as err:
            await run_layer_b(spec, registry=ProviderRegistry.fake())
        assert "entities" in err.value.result.missing_core

    @pytest.mark.asyncio
    async def test_validation_failure_names_the_fields_to_reopen(self):
        spec = booking_spec()
        spec.users_and_roles.value = ["guests", "staff"]
        spec.role_permissions = FieldMeta(value="staff see everything")
        result = await run_layer_b(spec, registry=ProviderRegistry.fake())
        assert not result.validation.valid
        assert "sign_in" in result.revisit_fields


class TestArchitectureEndpoint:
    def test_happy_path_returns_the_four_sections(self):
        res = client.post(
            "/architecture",
            json={
                "spec": {
                    "purpose": {"value": "Guests book a table."},
                    "users_and_roles": {"value": ["guests"]},
                    "entities": {"value": ["bookings", "tables"]},
                    "key_actions": {"value": ["book a table", "cancel a booking"]},
                    "sign_in": {"value": "no account — name and phone"},
                    "data_ownership_sensitivity": {"value": {"owner": "you", "sensitive": False}},
                    "non_goals": {"value": []},
                }
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert set(body) >= {"whole", "architecture", "playbook", "validation"}
        assert body["validation"]["valid"] is True
        assert {t["name"] for t in body["architecture"]["data_model"]["tables"]} == {
            "booking",
            "table",
        }
        assert body["architecture"]["auth_access"]["mode"] == "none"

    def test_a_non_buildable_spec_is_a_422_listing_what_is_missing(self):
        res = client.post(
            "/architecture",
            json={"spec": {"purpose": {"value": "Something vague."}}},
        )
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert "entities" in detail["missing_core"]
