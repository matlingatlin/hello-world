import pytest

from scio_engine.execution.matrix import default_matrix
from scio_engine.execution.provider import (
    Completion,
    FakeProvider,
    Message,
    ModelProvider,
    ProviderError,
    ProviderRegistry,
    Vendor,
)
from scio_engine.execution.relay import (
    MAX_PASSES,
    BudgetExceeded,
    RelayOptions,
    clamp_passes,
    run_relay,
    stream_relay,
)


@pytest.fixture
def fake_registry():
    return ProviderRegistry.fake()


def shared_provider(registry: ProviderRegistry) -> FakeProvider:
    return registry.get(Vendor.anthropic)  # fake registry binds one instance to all vendors


class TestRelayOrdering:
    @pytest.mark.asyncio
    async def test_four_pass_relay_runs_models_in_plan_order(self, fake_registry):
        result = await run_relay("codegen", "Build a booking form", registry=fake_registry)
        expected = default_matrix().top_n("codegen", n=3)
        assert [p.model for p in result.passes] == [
            expected[0].id,
            expected[1].id,
            expected[2].id,
            expected[0].id,
        ]
        assert [p.role for p in result.passes] == ["draft", "review", "review", "final"]

    @pytest.mark.asyncio
    async def test_pass_count_is_configurable(self, fake_registry):
        for passes in (1, 2, 3, 4):
            result = await run_relay(
                "codegen", "x", registry=fake_registry, options=RelayOptions(passes=passes)
            )
            assert len(result.passes) == passes

    @pytest.mark.asyncio
    async def test_final_text_is_the_last_pass_output(self, fake_registry):
        result = await run_relay("codegen", "x", registry=fake_registry)
        assert result.final_text == result.passes[-1].text

    @pytest.mark.asyncio
    async def test_deterministic_with_the_fake_provider(self, fake_registry):
        a = await run_relay("codegen", "same prompt", registry=ProviderRegistry.fake())
        b = await run_relay("codegen", "same prompt", registry=ProviderRegistry.fake())
        assert [p.text for p in a.passes] == [p.text for p in b.passes]


class TestStructuredHandoff:
    @pytest.mark.asyncio
    async def test_each_later_pass_receives_prompt_and_previous_answer(self, fake_registry):
        provider = shared_provider(fake_registry)
        await run_relay("codegen", "ORIGINAL-PROMPT", registry=fake_registry)

        first_messages = provider.calls[0][1]
        assert first_messages[-1].content == "ORIGINAL-PROMPT"

        second_messages = provider.calls[1][1]
        body = second_messages[-1].content
        assert "complement what is missing" in body
        assert "ORIGINAL-PROMPT" in body
        assert "PREVIOUS ANSWER" in body

    @pytest.mark.asyncio
    async def test_final_pass_uses_the_final_instruction(self, fake_registry):
        provider = shared_provider(fake_registry)
        await run_relay("codegen", "P", registry=fake_registry)
        last_body = provider.calls[-1][1][-1].content
        assert "Produce the final answer" in last_body

    @pytest.mark.asyncio
    async def test_system_prompt_is_passed_through(self, fake_registry):
        provider = shared_provider(fake_registry)
        await run_relay(
            "codegen", "P", registry=fake_registry, options=RelayOptions(system="HOUSE RULES")
        )
        assert provider.calls[0][1][0].role == "system"
        assert provider.calls[0][1][0].content == "HOUSE RULES"

    @pytest.mark.asyncio
    async def test_pass_results_carry_token_and_cost_metadata(self, fake_registry):
        result = await run_relay("codegen", "P", registry=fake_registry)
        assert all(p.output_tokens > 0 for p in result.passes)
        assert result.total_cost_usd > 0
        assert result.total_tokens > 0


class TestGuardrails:
    def test_pass_count_is_clamped_to_the_cap(self):
        assert clamp_passes(99, 3) == MAX_PASSES
        assert clamp_passes(0, 3) == 1
        assert clamp_passes(-5, 3) == 1
        assert clamp_passes(2, 3) == 2

    @pytest.mark.asyncio
    async def test_relay_never_exceeds_the_cap(self, fake_registry):
        result = await run_relay(
            "codegen", "x", registry=fake_registry, options=RelayOptions(passes=50)
        )
        assert len(result.passes) == MAX_PASSES

    @pytest.mark.asyncio
    async def test_budget_stops_the_relay(self, fake_registry):
        with pytest.raises(BudgetExceeded):
            await run_relay(
                "codegen",
                "x",
                registry=fake_registry,
                options=RelayOptions(budget_usd=0.0000001),
            )

    @pytest.mark.asyncio
    async def test_a_failing_pass_is_retried_then_fails_the_relay(self, fake_registry):
        class AlwaysFails(ModelProvider):
            vendor = Vendor.anthropic

            def __init__(self):
                self.attempts = 0

            async def complete(self, model, messages, **kwargs):
                self.attempts += 1
                raise ProviderError("boom")

        failing = AlwaysFails()
        registry = ProviderRegistry(providers={Vendor.anthropic: failing})
        with pytest.raises(ProviderError):
            await run_relay(
                "codegen", "x", registry=registry, options=RelayOptions(passes=1, retries=2)
            )
        assert failing.attempts == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_transient_failure_recovers_on_retry(self):
        class FlakyOnce(ModelProvider):
            vendor = Vendor.anthropic

            def __init__(self):
                self.attempts = 0

            async def complete(self, model, messages, **kwargs):
                self.attempts += 1
                if self.attempts == 1:
                    raise ProviderError("transient")
                return Completion(text="recovered", model=model, vendor=Vendor.anthropic)

        registry = ProviderRegistry(providers={Vendor.anthropic: FlakyOnce()})
        result = await run_relay(
            "codegen", "x", registry=registry, options=RelayOptions(passes=1, retries=1)
        )
        assert result.final_text == "recovered"


class TestStreaming:
    @pytest.mark.asyncio
    async def test_events_arrive_narration_then_passes_then_result(self, fake_registry):
        events = [
            event
            async for event, _ in stream_relay("codegen", "x", registry=fake_registry)
        ]
        assert events == ["narration", "pass", "pass", "pass", "pass", "result"]


class TestProviders:
    @pytest.mark.asyncio
    async def test_fake_provider_is_deterministic_per_input(self):
        provider = FakeProvider()
        a = await provider.complete("m", [Message(role="user", content="hello")])
        b = await provider.complete("m", [Message(role="user", content="hello")])
        c = await provider.complete("m", [Message(role="user", content="different")])
        assert a.text == b.text
        assert a.text != c.text

    def test_registry_raises_for_an_unregistered_vendor(self):
        with pytest.raises(ProviderError, match="No provider registered"):
            ProviderRegistry(providers={}).get(Vendor.google)

    @pytest.mark.asyncio
    async def test_real_providers_fail_clearly_without_keys(self):
        from scio_engine.execution.provider import (
            AnthropicProvider,
            GoogleProvider,
            OpenAIProvider,
        )

        for provider in (
            AnthropicProvider(api_key=""),
            OpenAIProvider(api_key=""),
            GoogleProvider(api_key=""),
        ):
            with pytest.raises(ProviderError, match="not set"):
                await provider.complete("m", [Message(role="user", content="x")])
