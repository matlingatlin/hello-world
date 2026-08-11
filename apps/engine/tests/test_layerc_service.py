"""Contract assembly, plan validation, judgment, and the /plan endpoint."""

import pytest
from fastapi.testclient import TestClient

from conftest import make_booking_spec as booking_spec
from scio_engine.execution.provider import ProviderRegistry
from scio_engine.intake.schema import FieldMeta
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerc.contract import contract_prompt
from scio_engine.layerc.decompose import FOUNDATION_ID, SCHEMA_ID, build_plan
from scio_engine.layerc.judgment import GroupingAdvice, ambiguous_operations, apply_advice
from scio_engine.layerc.plan import BuildPackage, BuildPlan, NodeRef, PackageKind
from scio_engine.layerc.service import run_layer_c
from scio_engine.layerc.validate import validate_plan
from scio_engine.main import app

client = TestClient(app)


def signed_in_spec():
    return booking_spec(
        users_and_roles=FieldMeta(value=["guests", "staff"]),
        sign_in=FieldMeta(value="email link"),
        role_permissions=FieldMeta(value="staff see all; guests only their own"),
        notifications=FieldMeta(value="email on confirmation"),
    )


def rules_fired(result) -> set[str]:
    return {v.rule for v in result.violations}


class TestValidation:
    def test_a_derived_plan_validates(self):
        arch = derive_architecture(signed_in_spec())
        result = validate_plan(build_plan(arch), arch)
        assert result.valid, [v.message for v in result.violations]

    def test_a_dropped_architecture_node_is_caught(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        schema = plan.get(SCHEMA_ID)
        schema.architecture_slice = schema.architecture_slice[:-1]  # drop one table
        result = validate_plan(plan, arch)
        assert not result.valid
        assert "node_covered" in rules_fired(result)

    def test_a_dependency_cycle_is_caught(self):
        arch = derive_architecture(booking_spec())
        plan = BuildPlan(
            packages=[
                BuildPackage(
                    id="a",
                    kind=PackageKind.feature,
                    goal="a",
                    dependencies=["b"],
                    architecture_slice=[NodeRef(kind="operation", name="x")],
                    acceptance_criteria=["works"],
                ),
                BuildPackage(
                    id="b",
                    kind=PackageKind.feature,
                    goal="b",
                    dependencies=["a"],
                    architecture_slice=[NodeRef(kind="operation", name="y")],
                    acceptance_criteria=["works"],
                ),
            ],
            order=[],  # topological sort produced nothing — the cycle
        )
        result = validate_plan(plan, arch)
        assert not result.valid
        assert "acyclic" in rules_fired(result)

    def test_an_incomplete_contract_is_caught(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        package = plan.get(FOUNDATION_ID)
        package.goal = ""
        package.acceptance_criteria = []
        result = validate_plan(plan, arch)
        assert not result.valid
        assert {"contract_complete", "contract_testable"} <= rules_fired(result)

    def test_a_missing_dependency_is_caught(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        plan.get(SCHEMA_ID).dependencies.append("pkg_ghost")
        result = validate_plan(plan, arch)
        assert "dependency_exists" in rules_fired(result)

    def test_an_order_that_breaks_dependencies_is_caught(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        plan.order = list(reversed(plan.order))
        result = validate_plan(plan, arch)
        assert "order_respects_dependencies" in rules_fired(result)

    def test_duplicate_package_ids_are_caught(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        plan.packages.append(plan.packages[0])
        result = validate_plan(plan, arch)
        assert "unique_package_id" in rules_fired(result)


class TestContractAssembly:
    @pytest.mark.asyncio
    async def test_a_contract_carries_slice_dependencies_why_and_house_rules(self):
        arch = derive_architecture(signed_in_spec())
        result = await run_layer_c(
            arch,
            registry=ProviderRegistry.fake(),
            whole="You are building a booking app for Bistro Nord.",
        )
        prompt = result.prompts["pkg_feature_booking"]

        assert "operation create_booking" in prompt  # its own slice, in detail
        assert "Already built — use these" in prompt  # dependency interfaces
        assert "pkg_schema" in prompt
        assert "Bistro Nord" in prompt  # the why
        assert "House rules" in prompt  # the playbook
        assert "Row-level security" in prompt
        assert "Canonical vocabulary" in prompt
        assert "Done when" in prompt

    @pytest.mark.asyncio
    async def test_the_scope_guard_travels_into_every_package(self):
        arch = derive_architecture(signed_in_spec())
        result = await run_layer_c(arch, registry=ProviderRegistry.fake())
        assert "no payments for now" in result.prompts["pkg_feature_booking"]

    def test_dependencies_contribute_interfaces_not_implementations(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        prompt = contract_prompt(plan.get("pkg_feature_booking"), plan, arch)
        assert "tables: booking" in prompt  # the shape
        assert "CREATE TABLE" not in prompt  # not the code

    def test_the_schema_contract_spells_out_columns_and_keys(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        prompt = contract_prompt(plan.get(SCHEMA_ID), plan, arch)
        assert "row-level security: True" in prompt
        assert "FK guest_id -> guest.id" in prompt


class TestJudgment:
    def test_operations_with_no_entity_are_flagged_as_ambiguous(self):
        arch = derive_architecture(
            booking_spec(key_actions=FieldMeta(value=["export the monthly report"]))
        )
        plan = build_plan(arch)
        assert ambiguous_operations(plan)

    def test_a_clean_architecture_has_nothing_ambiguous(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        assert ambiguous_operations(plan) == []

    @pytest.mark.asyncio
    async def test_judgment_is_not_consulted_when_nothing_is_ambiguous(self):
        result = await run_layer_c(
            derive_architecture(signed_in_spec()), registry=ProviderRegistry.fake()
        )
        assert result.grouping_advice.consulted is False

    @pytest.mark.asyncio
    async def test_judgment_is_consulted_when_something_is_ambiguous(self):
        arch = derive_architecture(
            booking_spec(
                key_actions=FieldMeta(value=["book a table", "export the monthly report"])
            )
        )
        result = await run_layer_c(arch, registry=ProviderRegistry.fake())
        assert result.grouping_advice.consulted is True
        # the fake provider returns a digest, not a valid mapping -> nothing applied
        assert result.grouping_advice.applied is False

    @pytest.mark.asyncio
    async def test_the_plan_stays_deterministic_when_judgment_is_off(self):
        arch = derive_architecture(
            booking_spec(
                key_actions=FieldMeta(value=["book a table", "export the monthly report"])
            )
        )
        result = await run_layer_c(
            arch, registry=ProviderRegistry.fake(), use_judgment=False
        )
        assert result.grouping_advice.consulted is False

    def test_applying_advice_moves_the_operation_and_drops_the_empty_bucket(self):
        arch = derive_architecture(
            booking_spec(
                key_actions=FieldMeta(value=["book a table", "export the monthly report"])
            )
        )
        plan = build_plan(arch)
        loose = ambiguous_operations(plan)
        apply_advice(
            plan,
            GroupingAdvice(applied=True, moves={loose[0]: "pkg_feature_booking"}),
            arch,
        )
        assert plan.get("pkg_feature_general") is None
        booking = plan.get("pkg_feature_booking")
        assert loose[0] in {n.name for n in booking.architecture_slice}
        assert loose[0] in booking.interface.operations

    def test_the_moved_operations_screen_travels_with_it(self):
        arch = derive_architecture(
            booking_spec(
                key_actions=FieldMeta(value=["book a table", "export the monthly report"])
            )
        )
        plan = build_plan(arch)
        loose = ambiguous_operations(plan)
        general_routes = {
            n.name for n in plan.get("pkg_feature_general").architecture_slice if n.kind == "screen"
        }
        apply_advice(
            plan,
            GroupingAdvice(applied=True, moves={loose[0]: "pkg_feature_booking"}),
            arch,
        )
        booking_routes = {
            n.name for n in plan.get("pkg_feature_booking").architecture_slice if n.kind == "screen"
        }
        assert general_routes <= booking_routes


class TestPlanEndpoint:
    def test_happy_path_returns_an_ordered_validated_plan(self):
        arch = derive_architecture(signed_in_spec())
        res = client.post(
            "/plan",
            json={
                "architecture": arch.model_dump(mode="json"),
                "whole": "You are building a booking app for Bistro Nord.",
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["validation"]["valid"] is True
        assert body["plan"]["order"][0] == FOUNDATION_ID
        assert len(body["plan"]["order"]) == len(body["plan"]["packages"])
        assert "pkg_feature_booking" in body["prompts"]

    def test_the_endpoint_rejects_a_malformed_architecture(self):
        res = client.post("/plan", json={"architecture": {"data_model": "not an object"}})
        assert res.status_code == 422
