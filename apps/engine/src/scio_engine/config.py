"""Engine configuration. Keys come from the environment (Azure secrets manager in
production, ADR-0004) — never from committed files.

Locally there is one more step, because there is no secrets manager: an
operator-written `apps/engine/.env`, which `docs/RUNBOOK-FIRST-RUN.md` has
documented as the whole configuration for a real run since it was written.
Nothing actually read it — the engine looked only at `os.environ`, so a
correctly-filled `.env` produced a stand-in build and a `/health` saying `fake`,
with no hint as to why. It is loaded here, once, at import.

Two rules keep this from being the "config from a committed file" ADR-0004
rules out: the file is gitignored and never shipped, and a variable already
present in the real environment always wins, so a deployment's secrets are
never shadowed by a stray local file.
"""

from __future__ import annotations

import os
from pathlib import Path

from .execution.provider import ProviderRegistry

ENGINE_ROOT = Path(__file__).resolve().parents[2]
"""apps/engine — where an operator's .env lives."""


SKIP_ENV_FILE = "SCIO_SKIP_ENV_FILE"
"""Set this and the .env is not read at all.

The test suite sets it. Without it, whether the suite passes depends on whether
the person running it happens to have configured a key: the relay's ordering
tests picked up the operator's `SCIO_MODEL` and asserted against the wrong
model, and `test_api.py` started making REAL model calls — a test run that
spends money and takes 100 seconds instead of one. Tests must be hermetic, and
an operator's local file is not part of the code under test.
"""


def load_env_file(path: Path | None = None) -> list[str]:
    """Read `KEY=value` lines into the environment. Returns the names it set.

    Deliberately tiny and dependency-free: `export` prefixes, blank lines,
    `#` comments and surrounding quotes, and nothing else. Anything more and
    this becomes a shell parser nobody audits — in a file that holds a key.
    """
    if os.getenv(SKIP_ENV_FILE, "").lower() in {"1", "true", "yes"}:
        return []
    target = path or ENGINE_ROOT / ".env"
    if not target.exists():
        return []

    applied: list[str] = []
    for raw in target.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.removeprefix("export ").partition("=")
        name = name.strip()
        value = value.strip().strip("\"'")
        # The environment wins: a deployment's real secret must never be
        # shadowed by a file somebody left in a checkout.
        if name and name not in os.environ:
            os.environ[name] = value
            applied.append(name)
    return applied


LOADED_FROM_ENV_FILE = load_env_file()
"""Which names came from the .env — reported by /health, without their values."""


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
