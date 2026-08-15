"""What the bridge sends, and what the shell is allowed to make of it.

`run_spike.py` proves the chain in a browser; this covers the seam between them
without one — the shape of the postMessage payload, and the fact that the shell
does not soften any of the resolver's refusals on its way to the screen.

    python3 -m pytest tests/ -q
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE))
sys.path.insert(0, str(SPIKE.parents[1] / "apps" / "engine" / "src"))

from run_spike import PACKAGE_FILES, resolve_payload  # noqa: E402
from scio_engine.core.instrumentation import Manifest, SourceLocation  # noqa: E402

BRIDGE = (SPIKE / "preview" / "bridge.js").read_text()


@pytest.fixture
def manifest() -> Manifest:
    return Manifest(
        elements={
            "booking-form-submit": SourceLocation(
                package="pkg_feature_booking", file="components/booking-form.tsx", line=70
            ),
            "app-shell": SourceLocation(
                package="pkg_foundation", file="app/layout.tsx", line=8
            ),
        },
        packages=PACKAGE_FILES,
    )


def marked(**hit) -> dict:
    """A postMessage the way the bridge actually sends it."""
    return {
        "source": "scio-preview",
        "type": "marked",
        "hit": {"scio_id": None, "scio_package": None, "tag": "div", **hit},
        "coords": {"x": 101, "y": 112, "scroll_y": 0},
        "route": "/booking/new",
    }


class TestResolution:
    def test_an_instrumented_element_resolves_to_its_package_and_line(self, manifest):
        out = resolve_payload(
            marked(scio_id="booking-form-submit", scio_package="pkg_feature_booking", tag="button"),
            manifest,
        )

        assert out["ok"]
        assert out["package"] == "pkg_feature_booking"
        assert (out["file"], out["line"]) == ("components/booking-form.tsx", 70)
        # The coordinates ride along untouched: only the preview can produce them.
        assert out["coords"] == {"x": 101, "y": 112, "scroll_y": 0}

    def test_an_uninstrumented_element_is_refused_not_resolved_to_its_ancestor(self, manifest):
        """The sandbox-marking spike's finding, still enforced across the bridge:
        falling through to an ancestor rewrites the shell instead of the button."""
        out = resolve_payload(
            marked(ancestor_id="app-shell", ancestor_package="pkg_foundation", ancestor_distance=2),
            manifest,
        )

        assert out["ok"] is False
        assert "app-shell" in out["error"]  # named as evidence…
        assert "pkg_foundation" not in out.get("package", "")  # …never as the answer
        assert "package" not in out

    def test_an_id_the_manifest_does_not_know_is_refused(self, manifest):
        out = resolve_payload(marked(scio_id="booking-form-ghost", tag="button"), manifest)

        assert out["ok"] is False
        assert "drifted" in out["error"]

    def test_a_dom_that_disagrees_with_the_manifest_is_refused(self, manifest):
        """The running app says one package, the manifest says another. One of
        them is stale and the spike must not pick."""
        out = resolve_payload(
            marked(scio_id="booking-form-submit", scio_package="pkg_foundation", tag="button"),
            manifest,
        )

        assert out["ok"] is False
        assert "Refusing to guess" in out["error"]


class TestTheBridgeItself:
    def test_it_never_posts_to_a_wildcard_origin(self):
        """postMessage(…, "*") would hand the app's structure to any page that
        managed to frame the preview."""
        calls = re.findall(r"postMessage\((.*)\);", BRIDGE)
        assert calls, "the bridge must postMessage something"
        for call in calls:
            # The target origin is the last argument, and it is never a wildcard.
            assert call.rstrip().endswith("SHELL_ORIGIN"), call

    def test_it_checks_the_origin_of_what_it_receives(self):
        assert "event.origin !== SHELL_ORIGIN" in BRIDGE

    def test_it_reports_the_ancestor_but_never_substitutes_it(self):
        """It must send both, and choose neither — choosing is the resolver's."""
        describe = BRIDGE.split("function describe")[1].split("\n  }")[0]
        assert "scio_id: node.getAttribute(ID)" in describe
        assert "ancestor_id:" in describe
        # No `|| ancestor` fallback anywhere in the reporting.
        assert not re.search(r"scio_id:[^,]*ancestor", describe)

    def test_it_does_nothing_when_the_app_is_not_embedded(self):
        """The delivered app is not in an iframe; even if the script were served
        by mistake, it must not arm, listen or draw."""
        assert "window.top === window.self" in BRIDGE
        assert BRIDGE.index("window.top === window.self") < BRIDGE.index("addEventListener")
