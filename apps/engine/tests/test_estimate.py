"""The cost + time estimate shown at the spec gate.

Three things have to hold, and they are the three the product promises:

1. **It is free.** Pricing must never call a model — a spec is priced every time
   someone finishes the wizard, and most specs are priced far more often than
   they are built.
2. **The library shows up in the price.** A plan with an assembled part must cost
   less than the same plan generated, or the library's whole argument is
   invisible where it matters most.
3. **It is a range, and it says what it covers.** A single figure would be a
   promise the build cannot keep.
"""

import pytest

from conftest import make_booking_spec
from scio_engine.estimate import (
    HIGH_MULTIPLIER,
    LOW_MULTIPLIER,
    BuildEstimate,
    Composition,
    estimate_plan,
    expected_output_tokens,
)
from scio_engine.execution.provider import ProviderRegistry, Vendor
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerc.decompose import build_plan
from scio_engine.layerc.plan import BuildPackage, BuildPlan, NodeRef, PackageKind
from scio_engine.layerc.service import run_layer_c


def booking_plan(**overrides):
    return build_plan(derive_architecture(make_booking_spec(**overrides)))


class TestItIsFree:
    def test_estimating_calls_no_model(self):
        """The assertion that protects the margin on specs that never build."""
        registry = ProviderRegistry.fake()
        provider = registry.get(Vendor.anthropic)

        estimate_plan(booking_plan())

        assert provider.calls == []

    @pytest.mark.asyncio
    async def test_the_endpoint_prices_without_a_relay_call_for_pricing(self):
        """Layer C itself may consult a model; the pricing step never does."""
        arch = derive_architecture(make_booking_spec())
        result = await run_layer_c(
            arch, registry=ProviderRegistry.fake(), use_judgment=False
        )
        registry = ProviderRegistry.fake()
        provider = registry.get(Vendor.anthropic)

        estimate_plan(result.plan)

        assert provider.calls == []

    def test_it_is_deterministic(self):
        first = estimate_plan(booking_plan())
        second = estimate_plan(booking_plan())

        assert first.cost_usd == second.cost_usd
        assert first.minutes == second.minutes


class TestTheLibraryLowersThePrice:
    def test_an_assembled_part_costs_nothing_to_build(self):
        plan = booking_plan()
        generated = estimate_plan(plan)

        booking = plan.get("pkg_feature_booking")
        booking.source = "assemble"
        booking.catalog_entry = "feature-booking"
        assembled = estimate_plan(plan)

        assert assembled.cost_usd.high < generated.cost_usd.high
        assert assembled.cost_usd.low < generated.cost_usd.low
        assert assembled.minutes.high < generated.minutes.high

    def test_the_assembled_package_is_priced_at_zero(self):
        plan = booking_plan()
        booking = plan.get("pkg_feature_booking")
        booking.source = "assemble"
        booking.catalog_entry = "feature-booking"

        line = next(
            p for p in estimate_plan(plan).per_package if p.package_id == "pkg_feature_booking"
        )
        assert line.assembled is True
        assert line.cost_usd == 0.0
        assert line.output_tokens == 0

    def test_the_composition_shows_reused_versus_built(self):
        plan = booking_plan()
        plan.get("pkg_feature_booking").source = "assemble"
        plan.get("pkg_feature_booking").catalog_entry = "feature-booking"

        composition = estimate_plan(plan).composition
        assert composition.parts_total == 5
        assert composition.assembled == 1
        assert composition.generated == 4
        assert composition.describe() == "5 parts · 1 reused · 4 built"

    def test_a_fully_generated_plan_says_so_plainly(self):
        assert estimate_plan(booking_plan()).composition.describe() == "5 parts · all built"

    @pytest.mark.asyncio
    async def test_the_real_plan_prices_the_library_hit(self):
        """End to end: Layer C matches the blueprint, and the price reflects it."""
        arch = derive_architecture(make_booking_spec())
        result = await run_layer_c(
            arch, registry=ProviderRegistry.fake(), use_judgment=False
        )

        assert result.estimate is not None
        assert result.estimate.composition.assembled == 1
        booking = next(
            p
            for p in result.estimate.per_package
            if p.package_id == "pkg_feature_booking"
        )
        assert booking.cost_usd == 0.0


class TestHonestFraming:
    def test_it_is_always_a_range(self):
        estimate = estimate_plan(booking_plan())

        assert estimate.cost_usd.low < estimate.cost_usd.high
        assert estimate.minutes.low < estimate.minutes.high

    def test_the_range_brackets_the_point_estimate(self):
        estimate = estimate_plan(booking_plan())
        point = sum(p.cost_usd for p in estimate.per_package)

        assert estimate.cost_usd.low == pytest.approx(point * LOW_MULTIPLIER, rel=0.01)
        assert estimate.cost_usd.high == pytest.approx(point * HIGH_MULTIPLIER, rel=0.01)

    def test_it_says_what_it_covers(self):
        assert estimate_plan(booking_plan()).basis == "the base build, without changes"

    def test_the_summary_line_carries_range_composition_and_caveat(self):
        described = estimate_plan(booking_plan()).describe()

        assert "–" in described  # a range, not a figure
        assert "parts" in described
        assert "without changes" in described

    def test_it_names_the_model_it_priced(self):
        estimate = estimate_plan(booking_plan())

        assert estimate.model
        assert estimate.price_per_mtok > 0
        assert estimate.passes >= 1

    def test_an_empty_plan_does_not_pretend(self):
        from scio_engine.layerc.plan import BuildPlan

        estimate = estimate_plan(BuildPlan(packages=[], order=[]))
        assert estimate.cost_usd.high == 0.0
        assert estimate.composition.describe() == "nothing to build"


def plan_of(*, generated: int, assembled: int = 0) -> BuildPlan:
    """A plan of N feature packages, for calibrating against builds we measured.

    Shaped by COUNT rather than rebuilt from a spec on purpose: what was observed
    is "seven generated packages took 45.9 minutes", and reconstructing the exact
    architecture behind them would pin the test to a spec instead of to the
    measurement.
    """
    packages: list[BuildPackage] = []
    for i in range(generated + assembled):
        package = BuildPackage(
            id=f"pkg_feature_thing{i}",
            kind=PackageKind.feature,
            goal="a feature",
            architecture_slice=[
                NodeRef(kind="operation", name=f"create_thing{i}"),
                NodeRef(kind="screen", name=f"/thing{i}"),
            ],
        )
        if i >= generated:
            package.source = "assemble"
            package.catalog_entry = "feature-thing"
        packages.append(package)
    return BuildPlan(packages=packages, order=[p.id for p in packages])


class TestTheHeuristic:
    def test_more_in_a_package_costs_more(self):
        small = BuildPackage(
            id="pkg_feature_a",
            kind=PackageKind.feature,
            goal="one thing",
            architecture_slice=[NodeRef(kind="operation", name="do_a")],
        )
        large = BuildPackage(
            id="pkg_feature_b",
            kind=PackageKind.feature,
            goal="many things",
            architecture_slice=[
                NodeRef(kind="operation", name="do_a"),
                NodeRef(kind="operation", name="do_b"),
                NodeRef(kind="screen", name="/a"),
                NodeRef(kind="screen", name="/b"),
            ],
        )

        assert expected_output_tokens(large) > expected_output_tokens(small)

    def test_the_shell_is_priced_higher_than_a_migration(self):
        """Calibrated against the real runs: foundation cost 2-4x the schema."""
        shell = BuildPackage(
            id="pkg_foundation", kind=PackageKind.foundation, goal="shell",
            architecture_slice=[NodeRef(kind="security", name="security_posture")],
        )
        schema = BuildPackage(
            id="pkg_schema", kind=PackageKind.schema, goal="schema",
            architecture_slice=[NodeRef(kind="table", name="booking")],
        )

        assert expected_output_tokens(shell) > expected_output_tokens(schema)

    def test_the_estimate_brackets_what_the_real_run_actually_cost(self, monkeypatch):
        """The calibration claim, checked against a real invoice.

        The third real run built this exact plan, fully generated, on Sonnet 5 at
        two passes, for $1.4210 — including one repair round on the feature
        package. The range must contain that, priced the way that run was
        configured, or the heuristic is not calibrated to anything.
        """
        monkeypatch.setenv("SCIO_MODEL", "claude-sonnet-5")
        monkeypatch.setenv("SCIO_MODEL_PASSES", "1")  # 1 -> generate + self-review

        estimate = estimate_plan(booking_plan())

        assert estimate.cost_usd.low <= 1.4210 <= estimate.cost_usd.high

    def test_the_range_contains_the_real_builds_it_was_calibrated_on(self, monkeypatch):
        """B077: the top of the range must not be somewhere the real world walks past.

        Two builds were run end to end on Sonnet 5 at two passes:

            5 generated + 1 assembled   took 10.8 min
            7 generated                 took 45.9 min and cost $2.69

        The old range said "up to 33 minutes" for the second and "up to $2.51"
        for its cost — both wrong, and wrong in the direction that matters,
        because the estimate is what someone decides on.
        """
        monkeypatch.setenv("SCIO_MODEL", "claude-sonnet-5")
        monkeypatch.setenv("SCIO_MODEL_PASSES", "1")  # 1 -> generate + self-review

        short = estimate_plan(plan_of(generated=5, assembled=1))
        long = estimate_plan(plan_of(generated=7))

        assert short.minutes.low <= 10.8 <= short.minutes.high, short.minutes
        assert long.minutes.low <= 45.9 <= long.minutes.high, long.minutes
        assert long.cost_usd.low <= 2.688465 <= long.cost_usd.high, long.cost_usd

    def test_the_range_is_not_so_wide_it_says_nothing(self, monkeypatch):
        """A range that spans an order of magnitude is not an estimate."""
        monkeypatch.setenv("SCIO_MODEL", "claude-sonnet-5")
        monkeypatch.setenv("SCIO_MODEL_PASSES", "1")

        estimate = estimate_plan(plan_of(generated=7))

        assert estimate.minutes.high / estimate.minutes.low < 4.5
        assert estimate.cost_usd.high / estimate.cost_usd.low < 4.5

    def test_the_default_profile_is_dearer_than_the_cheap_one(self, monkeypatch):
        """Not a bug when the number looks big: the shipped default is the full
        relay over the ranked matrix, which is Opus at four passes."""
        monkeypatch.setenv("SCIO_MODEL", "claude-sonnet-5")
        monkeypatch.setenv("SCIO_MODEL_PASSES", "1")
        cheap = estimate_plan(booking_plan())

        monkeypatch.delenv("SCIO_MODEL")
        monkeypatch.delenv("SCIO_MODEL_PASSES")
        default = estimate_plan(booking_plan())

        # Compared band to band rather than extreme to extreme. Since B077
        # widened the range to contain the builds we actually measured, a cheap
        # model having a bad day can cost more than an expensive one having a
        # good day — which is true, and not what this test is about.
        assert default.cost_usd.low > cheap.cost_usd.low
        assert default.cost_usd.high > cheap.cost_usd.high

    def test_more_passes_cost_more(self, monkeypatch):
        monkeypatch.setenv("SCIO_MODEL_PASSES", "1")  # 1 -> two passes
        cheap = estimate_plan(booking_plan())
        monkeypatch.setenv("SCIO_MODEL_PASSES", "4")
        dear = estimate_plan(booking_plan())

        assert dear.cost_usd.high > cheap.cost_usd.high

    def test_a_cheaper_model_lowers_the_price(self, monkeypatch):
        monkeypatch.setenv("SCIO_MODEL_PASSES", "1")
        monkeypatch.setenv("SCIO_MODEL", "claude-sonnet-5")
        sonnet = estimate_plan(booking_plan())
        monkeypatch.setenv("SCIO_MODEL", "claude-haiku-4-5")
        haiku = estimate_plan(booking_plan())

        assert haiku.cost_usd.high < sonnet.cost_usd.high
        assert haiku.model == "claude-haiku-4-5"


class TestTheEndpoint:
    def test_post_estimate_returns_a_priced_plan(self):
        from fastapi.testclient import TestClient

        from scio_engine.main import app

        arch = derive_architecture(make_booking_spec())
        response = TestClient(app).post(
            "/estimate", json={"architecture": arch.model_dump(mode="json")}
        )

        assert response.status_code == 200
        estimate = BuildEstimate.model_validate(response.json())
        assert estimate.cost_usd.high > estimate.cost_usd.low
        assert estimate.composition.parts_total == 5
        assert estimate.basis == "the base build, without changes"

    def test_the_plan_endpoint_carries_the_estimate_too(self):
        from fastapi.testclient import TestClient

        from scio_engine.main import app

        arch = derive_architecture(make_booking_spec())
        response = TestClient(app).post(
            "/plan",
            json={"architecture": arch.model_dump(mode="json"), "use_judgment": False},
        )

        assert response.status_code == 200
        assert response.json()["estimate"]["composition"]["parts_total"] == 5


class TestComposition:
    def test_it_reads_as_a_sentence_a_person_would_say(self):
        assert (
            Composition(parts_total=6, assembled=4, generated=2).describe()
            == "6 parts · 4 reused · 2 built"
        )
