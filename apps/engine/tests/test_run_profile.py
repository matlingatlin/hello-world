"""The run profile: which models run, and how many passes (B053).

The rule this file exists to protect is the one from STRATEGY.md section E:
**setting 1 does not mean one raw pass.** It means one model, run twice —
generate, then review its own work. It is the cheapest honest configuration, and
it is what the first real run against Claude uses, so it needs a test that fails
loudly if someone "simplifies" it back to a single call.
"""

import pytest

from scio_engine.execution.matrix import default_matrix
from scio_engine.execution.profile import (
    MAX_SETTING,
    MODEL_ENV,
    PROVIDER_ENV,
    SETTING_ENV,
    active_matrix,
    relay_passes,
    run_profile,
    single_model_matrix,
)
from scio_engine.execution.provider import ProviderRegistry, Vendor
from scio_engine.execution.relay import RelayOptions, run_relay


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """The profile is read from the environment, so every test starts unset."""
    for name in (SETTING_ENV, MODEL_ENV, PROVIDER_ENV):
        monkeypatch.delenv(name, raising=False)


def one_plus_claude(monkeypatch, model: str = "claude-sonnet-5") -> None:
    monkeypatch.setenv(PROVIDER_ENV, "anthropic")
    monkeypatch.setenv(MODEL_ENV, model)
    monkeypatch.setenv(SETTING_ENV, "1")


class TestSettingToPasses:
    def test_one_means_two_passes(self):
        assert relay_passes(1) == 2

    def test_zero_and_negatives_cannot_produce_a_single_pass(self):
        # A bad value must not silently become the cheapest possible run.
        assert relay_passes(0) == 2
        assert relay_passes(-3) == 2

    def test_other_settings_pass_through_up_to_the_cap(self):
        assert [relay_passes(n) for n in (2, 3, 4)] == [2, 3, 4]
        assert relay_passes(9) == MAX_SETTING


class TestProfileFromEnv:
    def test_unset_is_the_full_relay_over_the_ranked_matrix(self):
        profile = run_profile()
        assert profile.single_model is False
        assert profile.passes == MAX_SETTING
        assert profile.matrix.top_n("codegen") == default_matrix().top_n("codegen")

    def test_one_plus_claude_narrows_every_task_to_that_model(self, monkeypatch):
        one_plus_claude(monkeypatch)
        profile = run_profile()
        assert profile.only_model == "claude-sonnet-5"
        assert profile.passes == 2
        for task in profile.matrix.task_types:
            assert [m.id for m in profile.matrix.top_n(task)] == ["claude-sonnet-5"]

    def test_a_known_model_keeps_its_real_cost_and_context(self, monkeypatch):
        one_plus_claude(monkeypatch, "claude-haiku-4-5")
        card = run_profile().matrix.models["claude-haiku-4-5"]
        shipped = default_matrix().models["claude-haiku-4-5"]
        assert (card.cost_per_mtok, card.context_limit) == (
            shipped.cost_per_mtok,
            shipped.context_limit,
        )

    def test_a_model_the_matrix_has_not_caught_up_with_still_runs(self, monkeypatch):
        # An operator must not have to edit YAML to point at a newer model.
        one_plus_claude(monkeypatch, "claude-something-6")
        matrix = run_profile().matrix
        assert [m.id for m in matrix.top_n("codegen")] == ["claude-something-6"]
        assert matrix.models["claude-something-6"].vendor is Vendor.anthropic

    def test_a_nonsense_setting_falls_back_to_the_default(self, monkeypatch):
        monkeypatch.setenv(SETTING_ENV, "lots")
        assert run_profile().setting == MAX_SETTING

    def test_active_matrix_reads_the_environment_per_call(self, monkeypatch):
        assert len(active_matrix().models) > 1
        one_plus_claude(monkeypatch)
        assert list(active_matrix().models) == ["claude-sonnet-5"]

    def test_describe_says_what_will_run(self, monkeypatch):
        one_plus_claude(monkeypatch)
        described = run_profile().describe()
        assert "claude-sonnet-5" in described and "2 passes" in described


class TestOneModelRunsTwice:
    """The behaviour the first real run depends on."""

    @pytest.mark.asyncio
    async def test_setting_one_generates_then_reviews_itself(self, monkeypatch):
        one_plus_claude(monkeypatch)
        profile = run_profile()

        result = await run_relay(
            "codegen",
            "Build a booking form",
            registry=ProviderRegistry.fake(),
            matrix=profile.matrix,
            options=RelayOptions(passes=profile.passes),
        )

        assert [p.model for p in result.passes] == ["claude-sonnet-5", "claude-sonnet-5"]
        assert [p.role for p in result.passes] == ["draft", "final"]

    @pytest.mark.asyncio
    async def test_the_second_pass_actually_sees_the_first(self, monkeypatch):
        """Twice is only worth paying for if the second call is a review."""
        one_plus_claude(monkeypatch)
        registry = ProviderRegistry.scripted(["first answer", "reviewed answer"])
        provider = registry.get(Vendor.anthropic)

        result = await run_relay(
            "codegen",
            "Build a booking form",
            registry=registry,
            matrix=run_profile().matrix,
            options=RelayOptions(passes=2),
        )

        second_prompt = provider.calls[1][1][-1].content
        assert "first answer" in second_prompt
        assert "Build a booking form" in second_prompt
        assert result.final_text == "reviewed answer"

    @pytest.mark.asyncio
    async def test_a_caller_asking_for_one_pass_still_gets_one(self, monkeypatch):
        """The doubling belongs to the setting, not to the relay: a critique that
        asks for a single pass must not quietly cost twice as much."""
        one_plus_claude(monkeypatch)
        result = await run_relay(
            "codegen",
            "x",
            registry=ProviderRegistry.fake(),
            matrix=run_profile().matrix,
            options=RelayOptions(passes=1),
        )
        assert len(result.passes) == 1


class TestSingleModelMatrix:
    def test_it_keeps_every_task_the_shipped_matrix_knows(self):
        narrowed = single_model_matrix("claude-opus-5")
        assert set(narrowed.task_types) == set(default_matrix().task_types)
