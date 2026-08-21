"""Multi-pass relay (PROJECT-PLAN 4.2) — Scio's signature way of prompting.

Pass 1 runs in the best model; each later pass hands the *original prompt plus
the previous result* to the next model with instructions to review, rewrite and
complement; the final pass returns to the best model. Hand-off between passes is
structured (PassResult), so results are diffable rather than free text.

The relay is expensive by design, so pass count is configurable per task and
capped — see `RelayOptions` and `MAX_PASSES`.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from pydantic import BaseModel, Field

from .matrix import CapabilityMatrix, ModelCard
from .narration import narrate, plan_models
from .profile import active_matrix
from .provider import Completion, Message, ProviderError, ProviderRegistry

MAX_PASSES = 4
"""Hard cap. The 4-pass relay already multiplies cost and latency; more passes
buy little and spend a lot (PROJECT-PLAN sequencing notes)."""

REVIEW_INSTRUCTION = (
    "Below is the original task and a previous model's answer. Review it: correct "
    "what is wrong, rewrite what is weak, and complement what is missing. Return the "
    "improved answer in full — not a critique of it."
)

FINAL_INSTRUCTION = (
    "Below is the original task and the current best answer after review passes. "
    "Produce the final answer: keep what is right, resolve any remaining "
    "inconsistencies, and return the complete result."
)


class RelayOptions(BaseModel):
    """Per-task knobs. Defaults are the full relay; light edits pass passes=1."""

    passes: int = 4
    system: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.2
    timeout_s: float = 120.0
    retries: int = 1
    budget_usd: float | None = None
    """A ceiling on THIS relay call. Per-invocation by construction — see Spend."""
    spend: Spend | None = None
    """The build's running total, shared across calls. This is the real ceiling."""


class PassResult(BaseModel):
    """One pass's structured output — the hand-off unit between passes."""

    index: int  # 1-based
    role: str  # "draft" | "review" | "final"
    model: str
    vendor: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    stop_reason: str = ""  # "max_tokens" here means the answer is incomplete


class RelayResult(BaseModel):
    task: str
    narration: str
    models: list[str] = Field(default_factory=list)
    passes: list[PassResult] = Field(default_factory=list)
    final_text: str = ""
    total_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return sum(p.input_tokens + p.output_tokens for p in self.passes)

    @property
    def truncated(self) -> bool:
        """The answer ran into max_tokens, so it is cut off mid-sentence.

        Worth its own flag: a truncated codegen reply ends inside a file, and
        "no usable files" is a mystifying way to report "ask for less at a time".
        """
        return bool(self.passes) and self.passes[-1].stop_reason == "max_tokens"


@dataclass
class Spend:
    """What one BUILD has spent, shared across every relay call inside it.

    `RelayOptions.budget_usd` is a ceiling on a single relay invocation, and that
    is all it ever was: `run_relay` creates its `RelayResult` fresh per call, so
    the comparison below only ever saw one call's passes. Handing the same number
    to every codegen and every critique therefore authorised it once per call —
    a seven-package build makes at least fourteen, so a $3.76 "build ceiling"
    licensed something closer to $50.

    This is the object that makes a build-scoped ceiling possible: one instance,
    created where the build starts, incremented by every call, checked before
    each one. Mutable and shared on purpose — that IS the feature.
    """

    ceiling_usd: float | None = None
    spent_usd: float = 0.0

    def would_exceed(self, cost: float) -> bool:
        return self.ceiling_usd is not None and self.spent_usd + cost > self.ceiling_usd

    def add(self, cost: float) -> None:
        self.spent_usd += cost

    @property
    def remaining_usd(self) -> float | None:
        if self.ceiling_usd is None:
            return None
        return max(0.0, self.ceiling_usd - self.spent_usd)


class BudgetExceeded(RuntimeError):
    """Raised when a relay would exceed the task's budget. The metering hook
    (usage_event, ADR-0009) attaches here when full cost controls land (4.5)."""


def clamp_passes(requested: int, available_models: int) -> int:
    """Guardrail: never below 1, never above MAX_PASSES."""
    if requested < 1:
        return 1
    return min(requested, MAX_PASSES)


def _role_for(index: int, total: int) -> str:
    if index == 1:
        return "draft"
    if index == total:
        return "final"
    return "review"


def _build_messages(
    prompt: str, previous: str | None, role: str, system: str | None
) -> list[Message]:
    messages: list[Message] = []
    if system:
        messages.append(Message(role="system", content=system))
    if previous is None:
        messages.append(Message(role="user", content=prompt))
        return messages

    instruction = FINAL_INSTRUCTION if role == "final" else REVIEW_INSTRUCTION
    messages.append(
        Message(
            role="user",
            content=(
                f"{instruction}\n\n"
                f"--- ORIGINAL TASK ---\n{prompt}\n\n"
                f"--- PREVIOUS ANSWER ---\n{previous}"
            ),
        )
    )
    return messages


def _cost(card: ModelCard, completion: Completion) -> float:
    return (completion.output_tokens / 1_000_000) * card.cost_per_mtok


async def _complete_with_retry(
    registry: ProviderRegistry, card: ModelCard, messages: list[Message], opts: RelayOptions
) -> Completion:
    """One pass, with timeout and bounded retry. A pass that keeps failing fails
    the relay — silently dropping it would hand the user a shorter relay than
    the narration promised."""
    provider = registry.get(card.vendor)
    last: str = ""
    for attempt in range(opts.retries + 1):
        try:
            return await asyncio.wait_for(
                provider.complete(
                    card.id,
                    messages,
                    max_tokens=opts.max_tokens,
                    temperature=opts.temperature,
                    timeout_s=opts.timeout_s,
                ),
                timeout=opts.timeout_s,
            )
        except TimeoutError:
            # A bare TimeoutError stringifies to "", which turns the message
            # below into "after 2 attempts:" and tells the operator nothing.
            last = f"no reply within {opts.timeout_s:.0f}s"
        except ProviderError as exc:
            last = str(exc)
        if attempt < opts.retries:
            await asyncio.sleep(0.2 * (attempt + 1))
    raise ProviderError(f"Pass failed on {card.id} after {opts.retries + 1} attempts: {last}")


async def stream_relay(
    task: str,
    prompt: str,
    *,
    registry: ProviderRegistry,
    matrix: CapabilityMatrix | None = None,
    options: RelayOptions | None = None,
) -> AsyncIterator[tuple[str, BaseModel | str]]:
    """Run the relay, yielding (event, payload) as each pass completes.

    Events: "narration" (str), "pass" (PassResult), "result" (RelayResult).
    The API turns these into SSE; tests consume them directly.
    """
    # The active matrix honours the run profile (SCIO_MODEL), so a
    # single-model deployment narrows every relay without threading a
    # matrix through every service.
    matrix = matrix or active_matrix()
    opts = options or RelayOptions()

    models = matrix.top_n(task, n=3)
    passes = clamp_passes(opts.passes, len(models))
    plan = plan_models(models, passes)
    narration = narrate(task, models, passes)

    yield "narration", narration

    result = RelayResult(
        task=task,
        narration=narration,
        models=[m.id for m in plan],
    )

    previous: str | None = None
    for index, card in enumerate(plan, start=1):
        role = _role_for(index, len(plan))
        messages = _build_messages(prompt, previous, role, opts.system)

        started = time.perf_counter()
        completion = await _complete_with_retry(registry, card, messages, opts)
        duration_ms = int((time.perf_counter() - started) * 1000)

        cost = _cost(card, completion)
        if opts.budget_usd is not None and result.total_cost_usd + cost > opts.budget_usd:
            raise BudgetExceeded(
                f"Relay for '{task}' would exceed its budget of ${opts.budget_usd:.2f}"
            )
        if opts.spend is not None and opts.spend.would_exceed(cost):
            raise BudgetExceeded(
                f"This build has spent ${opts.spend.spent_usd:.2f} of its "
                f"${opts.spend.ceiling_usd:.2f} ceiling, and '{task}' would cross it"
            )
        if opts.spend is not None:
            # Recorded even though the pass is about to be counted into `result`
            # too: `result` dies with this call, and the ceiling is about the
            # build. The model has already been paid for the tokens either way.
            opts.spend.add(cost)

        pass_result = PassResult(
            index=index,
            role=role,
            model=card.id,
            vendor=str(completion.vendor),
            text=completion.text,
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
            cost_usd=cost,
            duration_ms=duration_ms,
            stop_reason=completion.stop_reason or "",
        )
        result.passes.append(pass_result)
        result.total_cost_usd += cost
        previous = completion.text

        yield "pass", pass_result

    result.final_text = previous or ""
    yield "result", result


async def run_relay(
    task: str,
    prompt: str,
    *,
    registry: ProviderRegistry,
    matrix: CapabilityMatrix | None = None,
    options: RelayOptions | None = None,
) -> RelayResult:
    """Non-streaming convenience wrapper — runs the same pipeline to completion."""
    final: RelayResult | None = None
    async for event, payload in stream_relay(
        task, prompt, registry=registry, matrix=matrix, options=options
    ):
        if event == "result" and isinstance(payload, RelayResult):
            final = payload
    assert final is not None  # stream_relay always ends with "result"
    return final
