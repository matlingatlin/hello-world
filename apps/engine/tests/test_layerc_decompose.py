"""The deterministic planner — every assertion here runs without any LLM."""

import pytest

from conftest import make_booking_spec as booking_spec
from scio_engine.intake.schema import FieldMeta
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerc.decompose import (
    AUTH_ID,
    FOUNDATION_ID,
    SCHEMA_ID,
    TOKENS_ID,
    CyclicPlanError,
    architecture_nodes,
    build_plan,
    topological_order,
)
from scio_engine.layerc.plan import BuildPackage, PackageKind


def signed_in_spec():
    """The realistic multi-role app: sign-in, two roles, a connector."""
    return booking_spec(
        users_and_roles=FieldMeta(value=["guests", "staff"]),
        sign_in=FieldMeta(value="email link"),
        role_permissions=FieldMeta(value="staff see all; guests only their own"),
        notifications=FieldMeta(value="email on confirmation"),
    )


class TestPackageSet:
    def test_the_expected_package_kinds_are_produced(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        kinds = {p.kind for p in plan.packages}
        assert kinds == {
            PackageKind.foundation,
            PackageKind.schema,
            PackageKind.auth,
            PackageKind.feature,
            PackageKind.connector,
            PackageKind.design_tokens,
        }

    def test_one_feature_package_per_entity(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        features = [p for p in plan.packages if p.kind is PackageKind.feature]
        assert [p.id for p in features] == ["pkg_feature_booking"]

    def test_schema_package_owns_every_table(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        schema = plan.get(SCHEMA_ID)
        assert {n.name for n in schema.architecture_slice} == arch.data_model.table_names()
        assert schema.interface.tables

    def test_feature_package_owns_its_operations_and_screens(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        feature = plan.get("pkg_feature_booking")
        ops = {n.name for n in feature.architecture_slice if n.kind == "operation"}
        assert ops == {op.name for op in arch.operations if op.entity == "booking"}
        assert any(n.kind == "screen" for n in feature.architecture_slice)

    def test_no_connectors_means_no_connector_packages(self):
        plan = build_plan(derive_architecture(booking_spec()))
        assert not [p for p in plan.packages if p.kind is PackageKind.connector]

    def test_every_package_carries_a_testable_contract(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        for package in plan.packages:
            assert package.goal.strip()
            assert package.acceptance_criteria
            assert package.architecture_slice


class TestAuthPackage:
    def test_no_sign_in_builds_identification_without_auth(self):
        plan = build_plan(derive_architecture(booking_spec()))
        auth = plan.get(AUTH_ID)
        assert "no auth tables" in auth.goal
        assert any("No authentication tables" in c for c in auth.acceptance_criteria)

    def test_sign_in_builds_real_auth_with_isolation_criteria(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        auth = plan.get(AUTH_ID)
        assert "email_link" in auth.goal
        assert any(
            "cannot read or change another user's rows" in c for c in auth.acceptance_criteria
        )


class TestOrdering:
    def test_foundation_is_first(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        assert plan.order[0] == FOUNDATION_ID

    def test_schema_precedes_the_features_that_use_it(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        position = {pid: i for i, pid in enumerate(plan.order)}
        assert position[SCHEMA_ID] < position["pkg_feature_booking"]

    def test_auth_precedes_protected_features(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        position = {pid: i for i, pid in enumerate(plan.order)}
        assert position[AUTH_ID] < position["pkg_feature_booking"]

    def test_tokens_precede_the_screens_that_use_them(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        position = {pid: i for i, pid in enumerate(plan.order)}
        assert position[TOKENS_ID] < position["pkg_feature_booking"]

    def test_every_package_comes_after_all_its_dependencies(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        position = {pid: i for i, pid in enumerate(plan.order)}
        for package in plan.packages:
            for dep in package.dependencies:
                assert position[dep] < position[package.id], f"{package.id} before {dep}"

    def test_order_covers_every_package_exactly_once(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        assert sorted(plan.order) == sorted(p.id for p in plan.packages)

    def test_ordering_is_reproducible(self):
        a = build_plan(derive_architecture(signed_in_spec()))
        b = build_plan(derive_architecture(signed_in_spec()))
        assert a.order == b.order

    def test_a_cycle_is_refused(self):
        packages = [
            BuildPackage(id="a", kind=PackageKind.feature, goal="a", dependencies=["b"]),
            BuildPackage(id="b", kind=PackageKind.feature, goal="b", dependencies=["a"]),
        ]
        with pytest.raises(CyclicPlanError):
            topological_order(packages)

    def test_unknown_dependencies_do_not_block_ordering(self):
        """Validation reports a missing dependency; ordering must not deadlock on it."""
        packages = [
            BuildPackage(id="a", kind=PackageKind.feature, goal="a", dependencies=["ghost"]),
        ]
        assert topological_order(packages) == ["a"]


class TestCoverageAndParallelism:
    def test_every_architecture_node_lands_in_a_package(self):
        arch = derive_architecture(signed_in_spec())
        plan = build_plan(arch)
        covered = set()
        for package in plan.packages:
            covered |= package.slice_ids()
        assert {n.id for n in architecture_nodes(arch)} <= covered

    def test_sibling_connectors_are_marked_parallelizable(self):
        arch = derive_architecture(
            booking_spec(
                notifications=FieldMeta(value="email on confirmation"),
                payment=FieldMeta(value="Stripe, per booking"),
            )
        )
        plan = build_plan(arch)
        connectors = [p for p in plan.packages if p.kind is PackageKind.connector]
        assert len(connectors) == 2
        assert all(p.parallelizable for p in connectors)

    def test_a_lone_connector_is_not_marked_parallelizable(self):
        plan = build_plan(derive_architecture(signed_in_spec()))
        connectors = [p for p in plan.packages if p.kind is PackageKind.connector]
        assert len(connectors) == 1
        assert not connectors[0].parallelizable
