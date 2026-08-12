"""The three guardrails the spike proved necessary.

If any test in this file fails, the failure it describes has come back — each one
maps to something that actually went wrong in spikes/sandbox-marking.
"""

import json
import shutil
from pathlib import Path

import pytest

from scio_engine.core.console import ConsoleEntry, Origin, classify, classify_console
from scio_engine.core.instrumentation import Manifest, SourceLocation
from scio_engine.core.manifest_builder import build_manifest
from scio_engine.core.resolver import ElementHit, MarkingResolutionError, resolve_marking
from scio_engine.core.verifier import (
    InstrumentationError,
    ids_in_source,
    verify_instrumentation,
)

FIXTURE = Path(__file__).parent / "fixtures" / "booking_app"
PACKAGE_FILES = {
    k: v for k, v in json.loads((FIXTURE / "PACKAGES.json").read_text()).items()
    if not k.startswith("$")
}


@pytest.fixture
def app(tmp_path) -> Path:
    """A writable copy — tests that mutate must not touch the fixture."""
    work = tmp_path / "app"
    shutil.copytree(FIXTURE, work)
    return work


@pytest.fixture
def manifest(app) -> Manifest:
    return build_manifest(app, PACKAGE_FILES)


class TestManifestIsGenerated:
    """The manifest is a build artifact, never hand-written."""

    def test_it_is_derived_from_the_source(self, manifest):
        assert manifest.generated_from == "source-scan"
        assert "booking-submit" in manifest.elements
        assert "site-header" in manifest.elements

    def test_each_element_gets_its_package_and_source_line(self, manifest):
        location = manifest.elements["booking-submit"]
        assert location.package == "pkg_feature_booking"
        assert location.file == "components/booking-form.tsx"
        assert location.line > 0
        assert location.component == "BookingForm"

    def test_the_shell_belongs_to_the_foundation_package(self, manifest):
        assert manifest.elements["site-header"].package == "pkg_foundation"
        assert manifest.elements["main"].package == "pkg_foundation"

    def test_loop_rendered_elements_become_one_pattern(self, manifest):
        assert "booking-slot-*" in manifest.patterns
        resolved = manifest.resolve("booking-slot-18:30")
        assert resolved.package == "pkg_feature_booking"
        assert resolved.matched_by == "pattern"

    def test_regenerating_the_manifest_is_stable(self, app, manifest):
        assert build_manifest(app, PACKAGE_FILES).model_dump() == manifest.model_dump()


class TestResolverFailsLoudly:
    """GUARDRAIL: the spike's exact bug — a lost id must NOT resolve to a parent."""

    def test_the_spike_bug_now_raises_instead_of_mis_resolving(self, manifest):
        """Before: this returned pkg_foundation and a directed change rewrote the
        app shell. Now it refuses."""
        hit = ElementHit(
            scio_id=None,  # the id was lost in a regeneration
            scio_package=None,
            tag="button",
            text="Book table",
            ancestor_id="main",  # what a permissive resolver would have used
            ancestor_package="pkg_foundation",
            ancestor_distance=3,
        )
        with pytest.raises(MarkingResolutionError) as err:
            resolve_marking(hit, manifest)

        message = str(err.value)
        assert "has no data-scio-id" in message
        assert "main" in message  # names the ancestor as evidence
        assert "wrong part of the app" in message

    def test_an_uninstrumented_region_says_so_plainly(self, manifest):
        hit = ElementHit(scio_id=None, scio_package=None, tag="div", ancestor_id=None)
        with pytest.raises(MarkingResolutionError, match="cannot be addressed"):
            resolve_marking(hit, manifest)

    def test_an_id_missing_from_the_manifest_is_drift_not_a_guess(self, manifest):
        hit = ElementHit(scio_id="never-generated", scio_package="pkg_feature_booking", tag="div")
        with pytest.raises(MarkingResolutionError, match="drifted"):
            resolve_marking(hit, manifest)

    def test_dom_and_manifest_disagreeing_is_refused(self, manifest):
        """One of them is stale; acting on either would be a coin flip."""
        hit = ElementHit(
            scio_id="booking-submit", scio_package="pkg_foundation", tag="button"
        )
        with pytest.raises(MarkingResolutionError, match="Refusing to guess"):
            resolve_marking(hit, manifest)

    def test_a_good_marking_resolves_exactly(self, manifest):
        hit = ElementHit(
            scio_id="booking-submit", scio_package="pkg_feature_booking", tag="button"
        )
        resolved = resolve_marking(hit, manifest)
        assert resolved.package == "pkg_feature_booking"
        assert resolved.location.file == "components/booking-form.tsx"

    def test_a_loop_instance_resolves_via_its_pattern(self, manifest):
        hit = ElementHit(
            scio_id="booking-slot-19:00", scio_package="pkg_feature_booking", tag="button"
        )
        assert resolve_marking(hit, manifest).package == "pkg_feature_booking"


class TestInstrumentationVerifier:
    """GUARDRAIL: a regeneration that loses an id is a failed build."""

    def test_the_fixture_verifies_clean(self, app, manifest):
        report = verify_instrumentation(app, manifest)
        assert report.valid, [i.message for i in report.issues]
        assert report.element_count > 0

    def test_a_lost_id_fails_the_build(self, app, manifest):
        """The spike scenario, caught at generation time instead of at click time."""
        before = ids_in_source(app, manifest.all_files())

        target = app / "components/booking-form.tsx"
        target.write_text(target.read_text().replace(' data-scio-id="booking-submit"', ""))

        regenerated = build_manifest(app, PACKAGE_FILES)
        report = verify_instrumentation(app, regenerated, expected_ids=before)

        assert not report.valid
        assert "id_survives_regeneration" in {i.rule for i in report.errors}
        assert any("booking-submit" in i.message for i in report.errors)

    def test_raise_for_status_stops_a_caller_continuing(self, app, manifest):
        before = ids_in_source(app, manifest.all_files())
        target = app / "components/booking-form.tsx"
        target.write_text(target.read_text().replace(' data-scio-id="booking-submit"', ""))
        report = verify_instrumentation(
            app, build_manifest(app, PACKAGE_FILES), expected_ids=before
        )
        with pytest.raises(InstrumentationError, match="booking-submit"):
            report.raise_for_status()

    def test_a_duplicate_id_fails(self, app):
        target = app / "components/site-header.tsx"
        target.write_text(target.read_text().replace("site-header", "booking-submit"))
        report = verify_instrumentation(app, build_manifest(app, PACKAGE_FILES))
        assert not report.valid
        assert "unique_id" in {i.rule for i in report.errors}

    def test_a_stale_manifest_entry_fails(self, app, manifest):
        manifest.elements["ghost-element"] = SourceLocation(
            package="pkg_feature_booking", file="components/booking-form.tsx", line=1
        )
        report = verify_instrumentation(app, manifest)
        assert not report.valid
        assert "manifest_consistent" in {i.rule for i in report.errors}

    def test_an_element_missing_from_the_manifest_fails(self, app, manifest):
        del manifest.elements["booking-submit"]
        report = verify_instrumentation(app, manifest)
        assert not report.valid
        assert "manifest_complete" in {i.rule for i in report.errors}

    def test_an_unknown_package_fails(self, app, manifest):
        manifest.elements["booking-submit"].package = "pkg_does_not_exist"
        report = verify_instrumentation(app, manifest)
        assert not report.valid
        assert "package_known" in {i.rule for i in report.errors}

    def test_an_app_with_no_instrumentation_fails(self, app, manifest):
        for relative in manifest.all_files():
            path = app / relative
            path.write_text("export function Empty() { return null; }\n")
        report = verify_instrumentation(app, build_manifest(app, PACKAGE_FILES))
        assert not report.valid
        assert "has_instrumentation" in {i.rule for i in report.errors}

    def test_a_new_id_is_a_warning_not_a_failure(self, app, manifest):
        """Adding an element is normal; losing one is not."""
        before = ids_in_source(app, manifest.all_files())
        target = app / "components/booking-form.tsx"
        target.write_text(
            target.read_text().replace(
                "<h1 data-scio-id=",
                '<p data-scio-id="booking-form-note" data-scio-package="pkg_feature_booking">'
                "note</p>\n      <h1 data-scio-id=",
            )
        )
        report = verify_instrumentation(
            app, build_manifest(app, PACKAGE_FILES), expected_ids=before
        )
        assert report.valid
        assert "new_id_introduced" in {i.rule for i in report.issues}


class TestConsoleClassifier:
    """GUARDRAIL: benign noise must not fail a build; real errors must."""

    def test_the_favicon_404_the_spike_hit_does_not_fail_a_build(self):
        """Its text names nothing — only the URL identifies it."""
        entry = ConsoleEntry(
            type="error",
            text="Failed to load resource: the server responded with a status of 404 (Not Found)",
            url="http://127.0.0.1:41407/favicon.ico",
        )
        result = classify(entry)
        assert result.origin is Origin.browser
        assert not result.fails_build

    def test_the_identical_message_from_an_app_route_does_fail(self):
        entry = ConsoleEntry(
            type="error",
            text="Failed to load resource: the server responded with a status of 404 (Not Found)",
            url="http://127.0.0.1:41407/api/bookings",
        )
        result = classify(entry)
        assert result.origin is Origin.app
        assert result.fails_build

    def test_framework_chatter_is_not_a_failure(self):
        for text in ("Download the React DevTools", "[Fast Refresh] rebuilding"):
            assert not classify(ConsoleEntry(type="info", text=text)).fails_build

    def test_a_real_app_error_fails(self):
        entry = ConsoleEntry(
            type="error", text="TypeError: booking is undefined", url="/_next/static/page.js"
        )
        assert classify(entry).fails_build

    def test_uncaught_page_errors_always_fail(self):
        report = classify_console([], page_errors=["ReferenceError: slot is not defined"])
        assert not report.clean
        assert report.failures == ["ReferenceError: slot is not defined"]

    def test_a_report_of_only_noise_is_clean_but_shows_what_it_suppressed(self):
        report = classify_console(
            [
                ConsoleEntry(type="error", text="404", url="/favicon.ico"),
                ConsoleEntry(type="info", text="Download the React DevTools"),
            ]
        )
        assert report.clean
        assert report.suppressed  # auditable, not silently swallowed

    def test_a_mixed_report_fails_on_the_real_error_only(self):
        report = classify_console(
            [
                ConsoleEntry(type="error", text="404", url="/favicon.ico"),
                ConsoleEntry(type="error", text="TypeError: x", url="/app.js"),
            ]
        )
        assert not report.clean
        assert report.failures == ["TypeError: x (/app.js)"]
