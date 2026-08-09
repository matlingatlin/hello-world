"""Engine configuration. Keys come from the environment (Azure secrets manager in
production, ADR-0004) — never from committed files."""

from __future__ import annotations

import os

from .execution.provider import ProviderRegistry


def use_fake_providers() -> bool:
    """True when no real key is configured, or when explicitly forced.

    Keeps the engine runnable (and demoable) with zero keys: the relay still
    executes end to end, it just runs against the deterministic FakeProvider.
    """
    if os.getenv("SCIO_FAKE_PROVIDERS", "").lower() in {"1", "true", "yes"}:
        return True
    return not any(
        os.getenv(key) for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY")
    )


def build_registry() -> ProviderRegistry:
    return ProviderRegistry.fake() if use_fake_providers() else ProviderRegistry.real()
