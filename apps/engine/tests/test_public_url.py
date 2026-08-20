"""The preview URL we publish is not always the one we dial.

A Codespace reaches every port through its own forwarded https origin, so the
loopback URL the sandbox runs on is useless to the browser that has to embed it.
These pin the translation and, more importantly, what it refuses to touch.
"""

from __future__ import annotations

import pytest

from scio_engine.core.public_url import PUBLIC_URL_TEMPLATE, public_url

TEMPLATE = "https://curly-space-fishstick-abc123-{port}.app.github.dev"


def test_a_loopback_url_becomes_the_forwarded_one() -> None:
    assert (
        public_url("http://127.0.0.1:41337", TEMPLATE)
        == "https://curly-space-fishstick-abc123-41337.app.github.dev"
    )


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "0.0.0.0"])
def test_every_way_of_writing_loopback_is_translated(host: str) -> None:
    assert public_url(f"http://{host}:3000", TEMPLATE).endswith("-3000.app.github.dev")


def test_a_path_survives_the_translation() -> None:
    assert public_url("http://127.0.0.1:5173/projects/7", TEMPLATE) == (
        "https://curly-space-fishstick-abc123-5173.app.github.dev/projects/7"
    )


def test_without_a_template_nothing_changes() -> None:
    """The local case, and the default: no config, no rewrite."""
    assert public_url("http://127.0.0.1:41337", "") == "http://127.0.0.1:41337"


def test_a_url_that_is_already_public_is_left_alone() -> None:
    """Rewriting one would invent a port that is not ours to forward."""
    already = "https://preview.example.com/app"
    assert public_url(already, TEMPLATE) == already


def test_an_empty_url_stays_empty() -> None:
    """A build that never started a preview has no URL — not a broken one."""
    assert public_url("", TEMPLATE) == ""


def test_the_template_is_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PUBLIC_URL_TEMPLATE, TEMPLATE)
    assert public_url("http://127.0.0.1:8080").endswith("-8080.app.github.dev")


def test_the_environment_is_not_consulted_when_a_template_is_passed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit beats ambient — including an explicit 'do not rewrite'."""
    monkeypatch.setenv(PUBLIC_URL_TEMPLATE, TEMPLATE)
    assert public_url("http://127.0.0.1:8080", "") == "http://127.0.0.1:8080"
