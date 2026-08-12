"""SPIKE tests — the parts of the mechanic that need no browser.

The live proof (sandbox boot, screenshot, console, click resolution) is
run_spike.py; these lock the logic that decides *what to touch*, which is the
part a regression would silently break.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from sandbox.directed_change import (  # noqa: E402
    ChangeRequest,
    plan_directed_change,
    snapshot,
    verify_isolation,
)
from sandbox.inspector import ConsoleMessage, Observation, is_noise  # noqa: E402
from sandbox.resolver import Manifest, UnknownElementError  # noqa: E402

APP_DIR = ROOT / "example-app"


@pytest.fixture
def manifest() -> Manifest:
    return Manifest.load(APP_DIR / "scio-manifest.json")


class TestResolver:
    def test_an_element_resolves_to_its_package_and_source(self, manifest):
        location = manifest.resolve("booking-submit")
        assert location.package == "pkg_feature_booking"
        assert location.file == "components/booking-form.tsx"
        assert location.component == "BookingForm"
        assert location.matched_by == "exact"

    def test_shell_elements_resolve_to_the_foundation_package(self, manifest):
        assert manifest.resolve("site-header").package == "pkg_foundation"

    def test_loop_rendered_elements_resolve_by_pattern(self, manifest):
        """Every time slot shares one source location; the id carries the key."""
        for slot in ("booking-slot-18:00", "booking-slot-19:30"):
            location = manifest.resolve(slot)
            assert location.package == "pkg_feature_booking"
            assert location.matched_by == "pattern"

    def test_an_unknown_element_cannot_be_addressed(self, manifest):
        with pytest.raises(UnknownElementError):
            manifest.resolve("something-the-builder-never-emitted")

    def test_every_manifest_file_exists_on_disk(self, manifest):
        for relative in manifest.all_files():
            assert (APP_DIR / relative).exists(), relative

    def test_every_element_belongs_to_a_declared_package(self, manifest):
        for scio_id in manifest.elements:
            assert manifest.resolve(scio_id).package in manifest.packages


class TestDirectedChange:
    def test_a_change_targets_only_the_resolved_packages_files(self, manifest):
        package, edits = plan_directed_change(
            ChangeRequest(
                scio_id="booking-submit",
                instruction="rename the button",
                find="Book table",
                replace="Reserve my table",
            ),
            manifest,
            APP_DIR,
        )
        assert package == "pkg_feature_booking"
        assert set(edits) <= set(manifest.files_for(package))
        assert "components/site-header.tsx" not in edits

    def test_a_change_that_would_match_nothing_is_refused(self, manifest):
        with pytest.raises(ValueError, match="would touch nothing"):
            plan_directed_change(
                ChangeRequest(
                    scio_id="booking-submit",
                    instruction="change text that isn't there",
                    find="THIS STRING DOES NOT EXIST",
                    replace="x",
                ),
                manifest,
                APP_DIR,
            )

    def test_a_marking_on_the_shell_targets_the_shell_package(self, manifest):
        package, edits = plan_directed_change(
            ChangeRequest(
                scio_id="site-header",
                instruction="rename the restaurant",
                find="Bistro Nord",
                replace="Bistro Syd",
            ),
            manifest,
            APP_DIR,
        )
        assert package == "pkg_foundation"
        assert "components/booking-form.tsx" not in edits


class TestIsolationProof:
    def test_an_untouched_tree_reports_no_change(self, manifest):
        before = snapshot(APP_DIR, manifest.all_files())
        proof = verify_isolation(APP_DIR, before, "pkg_feature_booking", manifest)
        assert proof.changed_files == []
        assert not proof.violations
        assert not proof.isolated  # nothing changed: not a successful directed change

    def test_a_change_inside_the_package_is_isolated(self, manifest, tmp_path):
        """Copy the app, edit one file of the target package, and check the proof."""
        import shutil

        work = tmp_path / "app"
        shutil.copytree(
            APP_DIR, work, ignore=shutil.ignore_patterns("node_modules", ".next")
        )
        before = snapshot(work, manifest.all_files())

        target = work / "components/booking-form.tsx"
        target.write_text(target.read_text().replace("Book table", "Reserve"))

        proof = verify_isolation(work, before, "pkg_feature_booking", manifest)
        assert proof.changed_files == ["components/booking-form.tsx"]
        assert proof.violations == []
        assert proof.isolated
        assert len(proof.unchanged_files) == len(manifest.all_files()) - 1

    def test_a_change_outside_the_package_is_caught_as_a_violation(self, manifest, tmp_path):
        """The proof must fail loudly when a change leaks into another package —
        that is the whole promise of directed regeneration."""
        import shutil

        work = tmp_path / "app"
        shutil.copytree(
            APP_DIR, work, ignore=shutil.ignore_patterns("node_modules", ".next")
        )
        before = snapshot(work, manifest.all_files())

        stray = work / "components/site-header.tsx"
        stray.write_text(stray.read_text().replace("Bistro Nord", "Leaked"))

        proof = verify_isolation(work, before, "pkg_feature_booking", manifest)
        assert "components/site-header.tsx" in proof.violations
        assert not proof.isolated


class TestConsoleNoise:
    def test_a_missing_favicon_is_classified_as_noise(self):
        """The exact message this spike observed — text names nothing, so the
        URL is what makes it classifiable."""
        message = ConsoleMessage(
            type="error",
            text="Failed to load resource: the server responded with a status of 404 (Not Found)",
            url="http://127.0.0.1:41407/favicon.ico",
        )
        assert is_noise(message)

    def test_the_same_text_from_an_app_resource_is_not_noise(self):
        message = ConsoleMessage(
            type="error",
            text="Failed to load resource: the server responded with a status of 404 (Not Found)",
            url="http://127.0.0.1:41407/api/bookings",
        )
        assert not is_noise(message)

    def test_an_observation_with_only_noise_reads_as_clean(self, tmp_path):
        observation = Observation(
            screenshot_path=tmp_path / "s.png",
            console=[
                ConsoleMessage("error", "Failed to load resource: 404", "/favicon.ico"),
                ConsoleMessage("info", "Download the React DevTools", ""),
            ],
        )
        assert observation.errors  # a naive agent would see a failure
        assert observation.app_errors == []  # the filtered signal is clean
        assert observation.clean

    def test_a_real_app_error_survives_the_filter(self, tmp_path):
        observation = Observation(
            screenshot_path=tmp_path / "s.png",
            console=[ConsoleMessage("error", "TypeError: booking is undefined", "/page.js")],
            page_errors=["ReferenceError: slot is not defined"],
        )
        assert len(observation.app_errors) == 2
        assert not observation.clean
