"""The engine reads the file the runbook told the operator to write.

`docs/RUNBOOK-FIRST-RUN.md` has said since it was written that
`apps/engine/.env` is "the whole configuration for a real run". Nothing read it.
`config.py` looked only at `os.environ`, so a correctly filled `.env` produced a
stand-in build and a `/health` reporting `fake`, with nothing to say why — the
one failure the runbook's own troubleshooting table points at.

The rules that keep this from being "configuration from a committed file"
(ADR-0004) are what these tests are actually about: the real environment always
wins, and only names — never values — are ever reported.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scio_engine.config import load_env_file, use_fake_providers


@pytest.fixture
def env_file(tmp_path: Path):
    def write(body: str) -> Path:
        target = tmp_path / ".env"
        target.write_text(body)
        return target

    return write


class TestReadingTheEnvFile:
    def test_a_key_in_the_file_reaches_the_process(self, env_file, monkeypatch):
        # Both cleared: this process may already have loaded the operator's own
        # .env at import, and "already set" is exactly what the loader skips.
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("SCIO_MODEL", raising=False)
        path = env_file("ANTHROPIC_API_KEY=sk-ant-test\nSCIO_MODEL=claude-sonnet-5\n")

        applied = load_env_file(path)

        assert applied == ["ANTHROPIC_API_KEY", "SCIO_MODEL"]
        assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
        # …which is the whole point: this is the switch between a real build and
        # a placeholder one.
        assert use_fake_providers() is False

    def test_the_real_environment_always_wins(self, env_file, monkeypatch):
        """A file somebody left in a checkout must never shadow a deployment's
        secret — that is what makes this compatible with ADR-0004."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "from-the-environment")
        path = env_file("ANTHROPIC_API_KEY=from-the-file\n")

        applied = load_env_file(path)

        assert applied == []
        assert os.environ["ANTHROPIC_API_KEY"] == "from-the-environment"

    def test_comments_blanks_exports_and_quotes(self, env_file, monkeypatch):
        monkeypatch.delenv("SCIO_MODEL", raising=False)
        monkeypatch.delenv("SCIO_ONLY_PROVIDER", raising=False)
        path = env_file(
            "\n# the model to use\nexport SCIO_MODEL='claude-sonnet-5'\n"
            'SCIO_ONLY_PROVIDER="anthropic"\nnot a pair\n'
        )

        load_env_file(path)

        assert os.environ["SCIO_MODEL"] == "claude-sonnet-5"
        assert os.environ["SCIO_ONLY_PROVIDER"] == "anthropic"

    def test_a_missing_file_is_not_an_error(self, tmp_path: Path):
        assert load_env_file(tmp_path / "nothing-here") == []

    def test_health_reports_names_and_never_values(self, env_file, monkeypatch):
        """The listing exists so an operator can see the key arrived. It must
        never be a way to read the key back out."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        path = env_file("ANTHROPIC_API_KEY=sk-ant-secret-value\n")

        applied = load_env_file(path)

        assert applied == ["ANTHROPIC_API_KEY"]
        assert "sk-ant-secret-value" not in str(applied)
