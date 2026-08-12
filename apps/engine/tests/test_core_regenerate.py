"""Directed regeneration, isolation, and persistence."""

import json
import shutil
from pathlib import Path

import pytest

from scio_engine.core.instrumentation import Manifest
from scio_engine.core.manifest_builder import build_manifest
from scio_engine.core.persistence import CouplingRecord, ManifestStore, ProjectCoupling
from scio_engine.core.regenerate import (
    IsolationViolation,
    MechanicalRegenerator,
    PackageRegenerator,
    directed_regenerate,
    regenerate_or_raise,
    snapshot,
    verify_isolation,
)
from scio_engine.core.resolver import ElementHit
from scio_engine.core.sandbox import LocalProcessSandbox, SandboxError, choose_sandbox
from scio_engine.core.verifier import InstrumentationError

FIXTURE = Path(__file__).parent / "fixtures" / "booking_app"
PACKAGE_FILES = {
    k: v for k, v in json.loads((FIXTURE / "PACKAGES.json").read_text()).items()
    if not k.startswith("$")
}

SUBMIT = ElementHit(
    scio_id="booking-submit", scio_package="pkg_feature_booking", tag="button", text="Book table"
)
HEADER = ElementHit(
    scio_id="site-header", scio_package="pkg_foundation", tag="header", text="Bistro Nord"
)


@pytest.fixture
def app(tmp_path) -> Path:
    work = tmp_path / "app"
    shutil.copytree(FIXTURE, work)
    return work


@pytest.fixture
def manifest(app) -> Manifest:
    return build_manifest(app, PACKAGE_FILES)


class TestDirectedRegeneration:
    def test_it_touches_only_the_marked_package(self, app, manifest):
        result = directed_regenerate(
            app,
            SUBMIT,
            "rename the button",
            manifest=manifest,
            regenerator=MechanicalRegenerator("Book table", "Reserve my table"),
            package_files=PACKAGE_FILES,
        )
        assert result.accepted
        assert result.package == "pkg_feature_booking"
        assert result.edited_files == ["components/booking-form.tsx"]
        assert result.isolation.isolated
        assert result.isolation.violations == []
        assert len(result.isolation.unchanged_files) == 2  # the shell files
        assert "Reserve my table" in (app / "components/booking-form.tsx").read_text()
        assert "Bistro Nord" in (app / "components/site-header.tsx").read_text()

    def test_marking_the_shell_targets_the_shell(self, app, manifest):
        result = directed_regenerate(
            app,
            HEADER,
            "rename the restaurant",
            manifest=manifest,
            regenerator=MechanicalRegenerator("Bistro Nord", "Bistro Syd"),
            package_files=PACKAGE_FILES,
        )
        assert result.package == "pkg_foundation"
        assert result.edited_files == ["components/site-header.tsx"]
        assert result.accepted

    def test_it_re_verifies_instrumentation_after_the_change(self, app, manifest):
        result = directed_regenerate(
            app,
            SUBMIT,
            "rename the button",
            manifest=manifest,
            regenerator=MechanicalRegenerator("Book table", "Reserve my table"),
            package_files=PACKAGE_FILES,
        )
        assert result.instrumentation.valid
        assert result.manifest.elements["booking-submit"].package == "pkg_feature_booking"

    def test_a_regeneration_that_drops_an_id_is_rejected_and_rolled_back(self, app, manifest):
        """The spike's failure, now caught before anyone can click on it."""
        before = (app / "components/booking-form.tsx").read_text()

        result = directed_regenerate(
            app,
            SUBMIT,
            "restructure the button",
            manifest=manifest,
            regenerator=MechanicalRegenerator(' data-scio-id="booking-submit"', ""),
            package_files=PACKAGE_FILES,
        )

        assert not result.accepted
        assert result.rolled_back
        assert "instrumentation" in result.rejection
        assert (app / "components/booking-form.tsx").read_text() == before

    def test_a_regenerator_reaching_outside_its_package_is_refused(self, app, manifest):
        class Sloppy(PackageRegenerator):
            def regenerate(self, app_dir, package, files, marking, instruction):
                return {
                    "components/booking-form.tsx": "// edited\n",
                    "components/site-header.tsx": "// leaked\n",  # not this package's
                }

        with pytest.raises(IsolationViolation, match="site-header"):
            directed_regenerate(
                app,
                SUBMIT,
                "do something",
                manifest=manifest,
                regenerator=Sloppy(),
                package_files=PACKAGE_FILES,
            )

    def test_a_marking_that_cannot_resolve_never_reaches_the_regenerator(self, app, manifest):
        from scio_engine.core.resolver import MarkingResolutionError

        class MustNotRun(PackageRegenerator):
            def regenerate(self, *args, **kwargs):
                raise AssertionError("the regenerator ran on an unresolved marking")

        lost = ElementHit(
            scio_id=None, scio_package=None, tag="button", ancestor_id="main",
            ancestor_package="pkg_foundation",
        )
        with pytest.raises(MarkingResolutionError):
            directed_regenerate(
                app, lost, "x", manifest=manifest, regenerator=MustNotRun(),
                package_files=PACKAGE_FILES,
            )

    def test_regenerate_or_raise_stops_a_forgetful_caller(self, app, manifest):
        with pytest.raises(InstrumentationError):
            regenerate_or_raise(
                app,
                SUBMIT,
                "restructure",
                manifest=manifest,
                regenerator=MechanicalRegenerator(' data-scio-id="booking-submit"', ""),
                package_files=PACKAGE_FILES,
            )


class TestIsolationProof:
    def test_an_untouched_tree_shows_no_change(self, app, manifest):
        before = snapshot(app, manifest.all_files())
        proof = verify_isolation(app, before, "pkg_feature_booking", manifest)
        assert proof.changed_files == []
        assert not proof.isolated  # nothing changed is not a successful change

    def test_a_leak_into_another_package_is_a_violation(self, app, manifest):
        before = snapshot(app, manifest.all_files())
        stray = app / "components/site-header.tsx"
        stray.write_text(stray.read_text().replace("Bistro Nord", "Leaked"))
        proof = verify_isolation(app, before, "pkg_feature_booking", manifest)
        assert "components/site-header.tsx" in proof.violations
        assert not proof.isolated


class TestPersistence:
    def test_the_manifest_round_trips_through_the_working_tree(self, app, manifest):
        store = ManifestStore(app)
        store.save(manifest)
        assert store.exists()
        loaded = store.load()
        assert loaded.elements.keys() == manifest.elements.keys()
        assert loaded.resolve("booking-submit").package == "pkg_feature_booking"
        assert loaded.resolve("booking-slot-18:00").matched_by == "pattern"

    def test_a_missing_manifest_says_to_regenerate_not_to_hand_write(self, app):
        with pytest.raises(FileNotFoundError, match="build artifact"):
            ManifestStore(app).load()

    def test_the_coupling_record_points_at_the_build_version(self, manifest):
        record = CouplingRecord.for_manifest(
            manifest, project_id="p1", build_version=4, git_sha="abc123"
        )
        assert record.element_count == len(manifest.elements)
        assert record.package_count == 2
        assert record.git_sha == "abc123"

    def test_a_project_resumes_with_its_coupling_intact(self, app, manifest):
        """Months later: the manifest is beside the code, so a marking still lands."""
        ProjectCoupling(
            record=CouplingRecord.for_manifest(manifest, project_id="p1", build_version=1),
            manifest=manifest,
        ).save(app)

        resumed = ProjectCoupling.load(app, project_id="p1", build_version=1, git_sha="deadbee")
        assert resumed.record.git_sha == "deadbee"
        assert resumed.manifest.resolve("booking-submit").file == "components/booking-form.tsx"

    def test_a_regenerated_manifest_persists_and_reloads(self, app, manifest):
        result = directed_regenerate(
            app,
            SUBMIT,
            "rename",
            manifest=manifest,
            regenerator=MechanicalRegenerator("Book table", "Reserve"),
            package_files=PACKAGE_FILES,
        )
        ManifestStore(app).save(result.manifest)
        assert ManifestStore(app).load().ids() == result.manifest.ids()


class TestSandboxSelection:
    def test_it_picks_something_runnable_and_reports_isolation_honestly(self):
        sandbox = choose_sandbox()
        assert sandbox.name in {"local-docker", "local-process"}
        if sandbox.name == "local-process":
            assert sandbox.isolated is False  # never mistake this for a boundary

    def test_starting_without_installed_dependencies_fails_clearly(self, app):
        """The spike's boot failure: deps must be complete before start."""
        with pytest.raises(SandboxError, match="node_modules"):
            LocalProcessSandbox().start(app)

    def test_a_change_cannot_escape_the_sandbox_directory(self, app):
        from scio_engine.core.sandbox import SandboxHandle

        handle = SandboxHandle(url="http://x", workdir=app, kind="test")
        with pytest.raises(SandboxError, match="outside the sandbox"):
            LocalProcessSandbox().apply_change(handle, {"../escaped.txt": "nope"})

    def test_the_aca_provider_is_wired_but_refuses_to_pretend(self):
        from scio_engine.core.aca_sandbox import AcaSandbox

        aca = AcaSandbox(pool_endpoint="")
        assert aca.isolated is True
        assert not aca.is_available()
        with pytest.raises(SandboxError, match="never run"):
            aca.start(Path("/tmp"))
