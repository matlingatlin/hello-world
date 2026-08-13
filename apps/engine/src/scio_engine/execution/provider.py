"""Model-provider abstraction (ADR-0006).

Everything in the engine calls models through `ModelProvider`; the concrete SDKs
live only in this package. That keeps the matrix multi-provider (Anthropic /
OpenAI / Google) and lets tests run the whole relay deterministically with
`FakeProvider` — no API keys needed.
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel, Field


class Vendor(StrEnum):
    anthropic = "anthropic"
    openai = "openai"
    google = "google"
    fake = "fake"


class Message(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class Completion(BaseModel):
    """One model call's structured result."""

    text: str
    model: str
    vendor: Vendor
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str | None = None


class ProviderError(RuntimeError):
    """Raised when a provider call fails (missing key, API error, timeout)."""


class ModelProvider(ABC):
    """One vendor's API behind a uniform async call."""

    vendor: Vendor

    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        """Run one completion. Raises ProviderError on failure."""


class FakeProvider(ModelProvider):
    """Deterministic stand-in for tests and key-less local runs.

    The reply is a stable digest of (model, messages) so relay ordering and
    hand-off can be asserted exactly, without pretending to be model output.
    """

    vendor = Vendor.fake

    def __init__(self, label: str = "fake") -> None:
        self.label = label
        self.calls: list[tuple[str, list[Message]]] = []

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        self.calls.append((model, messages))
        joined = "\n".join(f"{m.role}:{m.content}" for m in messages)
        digest = hashlib.sha256(f"{model}\n{joined}".encode()).hexdigest()[:12]
        return Completion(
            text=f"[{self.label}:{model}] pass-output {digest}",
            model=model,
            vendor=Vendor.fake,
            input_tokens=len(joined.split()),
            output_tokens=8,
            stop_reason="end_turn",
        )


class ScriptedProvider(ModelProvider):
    """Returns prepared replies in order — a stand-in for a model that must
    produce *real* output (code, a critique verdict) rather than a digest.

    FakeProvider proves the plumbing; this proves what the plumbing carries.
    Tests script exactly what the model "says", so a loop that generates, fails,
    fixes and passes is reproducible to the character.
    """

    vendor = Vendor.fake

    def __init__(self, replies: list[str], *, loop_last: bool = True) -> None:
        if not replies:
            raise ValueError("ScriptedProvider needs at least one reply")
        self.replies = list(replies)
        self.loop_last = loop_last
        self.calls: list[tuple[str, list[Message]]] = []

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        index = len(self.calls)
        self.calls.append((model, messages))
        if index < len(self.replies):
            text = self.replies[index]
        elif self.loop_last:
            text = self.replies[-1]
        else:
            raise ProviderError(f"ScriptedProvider ran out of replies at call {index + 1}")
        return Completion(
            text=text,
            model=model,
            vendor=Vendor.fake,
            input_tokens=sum(len(m.content.split()) for m in messages),
            output_tokens=len(text.split()),
            stop_reason="end_turn",
        )


class AnthropicProvider(ModelProvider):
    """Claude models via the Anthropic SDK. Imported lazily so the engine runs
    (and tests pass) without the SDK or a key present."""

    vendor = Vendor.anthropic

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        if not self.api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ProviderError("anthropic SDK not installed (pip install '.[providers]')") from exc

        client = AsyncAnthropic(api_key=self.api_key, timeout=timeout_s)
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        turns = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        # Omit `system` entirely when there is none: the SDK sends an explicit
        # None as `"system": null`, which the API rejects with
        # "system: Input should be a valid array". Not passing the key is not
        # the same as passing None here.
        extra = {"system": system} if system else {}

        # `temperature` is deliberately NOT sent. Current Claude models (Sonnet 5,
        # Opus 5 / 4.8 / 4.7) reject sampling parameters with a 400 — behaviour is
        # steered by prompting instead. The argument stays in the interface
        # because other vendors still honour it; determinism for this vendor comes
        # from the instruction, not the knob (and temperature=0 never guaranteed
        # identical output anyway).
        # Streamed, always. A codegen pass writes several complete files and can
        # run for minutes; a non-streaming request that long is what the SDK
        # warns about and what times out client-side. Streaming keeps the
        # connection alive and yields the same final message.
        try:
            async with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                messages=turns,
                **extra,
            ) as stream:
                res = await stream.get_final_message()
        except Exception as exc:  # pragma: no cover - network path
            raise ProviderError(f"Anthropic call failed: {exc}") from exc

        text = "".join(block.text for block in res.content if block.type == "text")
        return Completion(
            text=text,
            model=model,
            vendor=self.vendor,
            input_tokens=res.usage.input_tokens,
            output_tokens=res.usage.output_tokens,
            stop_reason=res.stop_reason,
        )


class OpenAIProvider(ModelProvider):
    """GPT models. Points at Azure OpenAI when AZURE_OPENAI_ENDPOINT is set
    (ADR-0004), otherwise the public API."""

    vendor = Vendor.openai

    def __init__(self, api_key: str | None = None, azure_endpoint: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not set")
        try:
            from openai import AsyncAzureOpenAI, AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ProviderError("openai SDK not installed (pip install '.[providers]')") from exc

        client = (
            AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.azure_endpoint,
                api_version="2024-10-21",
                timeout=timeout_s,
            )
            if self.azure_endpoint
            else AsyncOpenAI(api_key=self.api_key, timeout=timeout_s)
        )
        try:
            res = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
        except Exception as exc:  # pragma: no cover - network path
            raise ProviderError(f"OpenAI call failed: {exc}") from exc

        choice = res.choices[0]
        return Completion(
            text=choice.message.content or "",
            model=model,
            vendor=self.vendor,
            input_tokens=res.usage.prompt_tokens if res.usage else 0,
            output_tokens=res.usage.completion_tokens if res.usage else 0,
            stop_reason=choice.finish_reason,
        )


class GoogleProvider(ModelProvider):
    """Gemini models via the Google GenAI SDK."""

    vendor = Vendor.google

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        if not self.api_key:
            raise ProviderError("GOOGLE_API_KEY is not set")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ProviderError(
                "google-genai SDK not installed (pip install '.[providers]')"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        contents = "\n\n".join(m.content for m in messages if m.role != "system")
        try:
            res = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
        except Exception as exc:  # pragma: no cover - network path
            raise ProviderError(f"Google call failed: {exc}") from exc

        usage = getattr(res, "usage_metadata", None)
        return Completion(
            text=res.text or "",
            model=model,
            vendor=self.vendor,
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
        )


class ProviderRegistry(BaseModel):
    """Resolves a vendor to its provider. Injected, so tests bind every vendor
    to a FakeProvider and production binds the real SDKs."""

    model_config = {"arbitrary_types_allowed": True}

    providers: dict[Vendor, ModelProvider] = Field(default_factory=dict)

    @property
    def is_fake(self) -> bool:
        """True when nothing here can produce real prose.

        Callers whose output is shown to the user (the whole at the spec gate)
        use this to fall back to a deterministic text: a digest like
        "[fake:...] pass-output 8067fd" is not a narrative, and showing one as
        the thing a user approves would be worse than showing nothing.
        ScriptedProvider is deliberately not counted — its replies are real text.
        """
        return bool(self.providers) and all(
            type(p) is FakeProvider for p in self.providers.values()
        )

    def get(self, vendor: Vendor) -> ModelProvider:
        provider = self.providers.get(vendor)
        if provider is None:
            raise ProviderError(f"No provider registered for vendor '{vendor}'")
        return provider

    @classmethod
    def real(cls) -> ProviderRegistry:
        return cls(
            providers={
                Vendor.anthropic: AnthropicProvider(),
                Vendor.openai: OpenAIProvider(),
                Vendor.google: GoogleProvider(),
            }
        )

    @classmethod
    def fake(cls) -> ProviderRegistry:
        shared = FakeProvider()
        return cls(
            providers={
                Vendor.anthropic: shared,
                Vendor.openai: shared,
                Vendor.google: shared,
                Vendor.fake: shared,
            }
        )

    @classmethod
    def scripted(cls, replies: list[str], *, loop_last: bool = True) -> ProviderRegistry:
        """Every vendor answers from one script, so relay passes consume it in order."""
        shared = ScriptedProvider(replies, loop_last=loop_last)
        return cls(
            providers={
                Vendor.anthropic: shared,
                Vendor.openai: shared,
                Vendor.google: shared,
                Vendor.fake: shared,
            }
        )
