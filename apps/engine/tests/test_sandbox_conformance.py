"""One set of assertions, run against every sandbox provider.

`SandboxProvider.start` declares `env: dict[str, str] | None` in its abstract
signature, and for a long time only one of the two implementations honoured it.
`LocalDockerSandbox.start` accepted the argument and dropped it — the word `env`
appeared exactly once in the whole method, as the parameter — while the builder
delivers the marking bridge ONLY through that argument, and `choose_sandbox()`
*prefers* Docker. So the design window was silently dead on every Docker host,
and nothing said why, because the flag was never delivered rather than rejected.

An abstract method whose contract one implementation ignores is worse than no
abstraction: every caller is written against the promise. These tests are the
promise, written down once and checked against everybody.
"""

from __future__ import annotations

import subprocess

import pytest

from scio_engine.core.sandbox import (
    LocalDockerSandbox,
    LocalProcessSandbox,
    SandboxProvider,
    close_all_previews,
)

PROVIDERS = [LocalProcessSandbox, LocalDockerSandbox]


@pytest.fixture(autouse=True)
def _empty_registries():
    """The registries are class-level on purpose — a preview belongs to the host,
    not to a provider object — which also means they leak between tests unless
    somebody empties them."""
    LocalProcessSandbox._live.clear()
    LocalDockerSandbox._live.clear()
    yield
    LocalProcessSandbox._live.clear()
    LocalDockerSandbox._live.clear()


@pytest.mark.parametrize("provider", PROVIDERS, ids=lambda p: p.name)
def test_every_provider_declares_the_interface(provider: type[SandboxProvider]) -> None:
    assert issubclass(provider, SandboxProvider)
    for method in ("start", "apply_change", "stop"):
        assert callable(getattr(provider, method))


@pytest.mark.parametrize("provider", PROVIDERS, ids=lambda p: p.name)
def test_every_provider_passes_the_callers_env_to_the_app(
    provider: type[SandboxProvider], monkeypatch, tmp_path
) -> None:
    """The one the Docker provider failed for a long time.

    We do not need a running app to check it: what matters is that the value the
    caller handed over reaches the process being started.
    """
    seen: dict[str, str] = {}

    if provider is LocalProcessSandbox:
        (tmp_path / "node_modules").mkdir()

        class FakePopen:
            def __init__(self, *args, **kwargs):
                seen.update(kwargs.get("env") or {})
                self.stdout = None

            def poll(self):
                return None

        monkeypatch.setattr(subprocess, "Popen", FakePopen)
        monkeypatch.setattr(
            LocalProcessSandbox, "_wait_until_ready", lambda self, handle, process: None
        )
        provider().start(tmp_path, port=4321, env={"SCIO_PREVIEW_MODE": "1"})
    else:

        class Done:
            returncode = 0
            stdout = "container-id"
            stderr = ""

        def fake_run(command, **kwargs):
            if "run" in command:
                for index, item in enumerate(command):
                    if item == "-e":
                        name, _, value = command[index + 1].partition("=")
                        seen[name] = value
            return Done()

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(LocalDockerSandbox, "is_available", lambda self: True)
        monkeypatch.setattr(
            LocalDockerSandbox, "_wait_until_ready", lambda self, handle, **kw: None
        )
        provider().start(tmp_path, port=4321, env={"SCIO_PREVIEW_MODE": "1"})

    assert seen.get("SCIO_PREVIEW_MODE") == "1", (
        "the marking bridge arrives only through env — a provider that drops it "
        "produces a preview where clicking does nothing, and says nothing"
    )


@pytest.mark.parametrize("provider", PROVIDERS, ids=lambda p: p.name)
def test_no_provider_leaks_the_platforms_secrets(
    provider: type[SandboxProvider], monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    seen: dict[str, str] = {}

    if provider is LocalProcessSandbox:
        (tmp_path / "node_modules").mkdir()

        class FakePopen:
            def __init__(self, *args, **kwargs):
                seen.update(kwargs.get("env") or {})
                self.stdout = None

            def poll(self):
                return None

        monkeypatch.setattr(subprocess, "Popen", FakePopen)
        monkeypatch.setattr(
            LocalProcessSandbox, "_wait_until_ready", lambda self, handle, process: None
        )
    else:

        class Done:
            returncode = 0
            stdout = "container-id"
            stderr = ""

        def fake_run(command, **kwargs):
            if "run" in command:
                for index, item in enumerate(command):
                    if item == "-e":
                        name, _, value = command[index + 1].partition("=")
                        seen[name] = value
            return Done()

        monkeypatch.setattr(subprocess, "run", fake_run)
        monkeypatch.setattr(LocalDockerSandbox, "is_available", lambda self: True)
        monkeypatch.setattr(
            LocalDockerSandbox, "_wait_until_ready", lambda self, handle, **kw: None
        )

    provider().start(tmp_path, port=4321, env={})

    assert "ANTHROPIC_API_KEY" not in seen
    assert not any("sk-ant" in value for value in seen.values())


def test_shutdown_reaches_both_kinds(monkeypatch) -> None:
    """The first version of this walked only the local registry, so on the host
    `choose_sandbox` prefers it reported success and leaked every container."""
    removed: list[list[str]] = []
    monkeypatch.setattr(
        subprocess, "run", lambda command, **kw: removed.append(command) or type("R", (), {})()
    )
    LocalDockerSandbox._live["http://127.0.0.1:9001"] = "abc123"

    stopped = close_all_previews()

    assert stopped == 1
    assert any("rm" in command and "abc123" in command for command in removed)
    assert LocalDockerSandbox._live == {}
