"""A missing optional extra must not kill a build.

Playwright is optional — the docstring said so, `is_available()` existed to ask,
and the build path imported it anyway. A design build on a machine without it
died with `No module named 'playwright'`, which is a true sentence and a useless
one: the app had been built and was being served, and the only impossible thing
was looking at it.
"""

from __future__ import annotations

from pathlib import Path

from scio_engine.core.preview import Observation, PreviewInspector


def test_a_blind_observation_says_it_never_happened() -> None:
    blind = Observation.blind()
    assert blind.observed is False
    assert blind.screenshot_path is None


def test_an_empty_console_is_not_evidence_of_a_clean_one() -> None:
    """`clean` is about what was seen; `observed` is about whether anyone looked.

    Both are needed: the caller reads `observed` first and records an unjudged
    remainder, so no gate ever passes on evidence nobody gathered.
    """
    blind = Observation.blind()
    assert blind.clean is True
    assert blind.observed is False


def test_the_live_preview_returns_blind_instead_of_raising(monkeypatch) -> None:
    from scio_engine.builder import loop

    monkeypatch.setattr(PreviewInspector, "is_available", staticmethod(lambda: False))

    preview = loop.SandboxPreview.__new__(loop.SandboxPreview)
    preview._handle = object()
    preview._ensure_started = lambda app_dir: preview._handle  # type: ignore[method-assign]

    observation = loop.SandboxPreview.observe(preview, Path("."), attempt=0)
    assert observation.observed is False


def test_a_preview_never_sees_the_platforms_secrets(monkeypatch) -> None:
    """The generated app is code a MODEL wrote, running as a child process.

    It used to be started with `**os.environ`, which holds ANTHROPIC_API_KEY and
    the catalog database's URL. `process.env.ANTHROPIC_API_KEY` was one line of
    generated code away.
    """
    from scio_engine.core.sandbox import child_environment

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    monkeypatch.setenv("SCIO_CATALOG_DB", "postgresql://scio:pw@db/scio")
    monkeypatch.setenv("PATH", "/usr/bin")

    env = child_environment(4321, {"SCIO_PREVIEW_MODE": "1"})

    assert "ANTHROPIC_API_KEY" not in env
    assert "SCIO_CATALOG_DB" not in env
    assert not any("sk-ant" in value for value in env.values())
    # and it still gets what it legitimately needs
    assert env["PATH"] == "/usr/bin"
    assert env["PORT"] == "4321"
    assert env["SCIO_PREVIEW_MODE"] == "1"


def test_production_refuses_a_sandbox_that_shares_the_host(monkeypatch) -> None:
    """The local provider disqualifies itself in its own docstring.

    Until now nothing enforced it, so a misconfigured production would happily
    run model-authored code beside the engine. Same fence dev auth already has.
    """
    import pytest

    from scio_engine.core.sandbox import LocalDockerSandbox, SandboxError, choose_sandbox

    monkeypatch.setattr(LocalDockerSandbox, "is_available", lambda self: False)
    monkeypatch.setenv("SCIO_ENV", "production")

    with pytest.raises(SandboxError, match="must not"):
        choose_sandbox()


def test_development_still_gets_the_local_one(monkeypatch) -> None:
    from scio_engine.core.sandbox import LocalDockerSandbox, LocalProcessSandbox, choose_sandbox

    monkeypatch.setattr(LocalDockerSandbox, "is_available", lambda self: False)
    monkeypatch.delenv("SCIO_ENV", raising=False)

    assert isinstance(choose_sandbox(), LocalProcessSandbox)
