"""The workspace: the locked stack on disk, with its dependencies installed.

The rule being protected is an ordering one. The sandbox refuses to start a
directory without `node_modules` because a dev server that installs on first boot
dies mid-startup (the spike proved it), so installing has to be its own explicit,
blocking step that fails with npm's error rather than a mysterious dead server.

The real `npm install` is not exercised here — it needs a network and takes
~35s — but everything around it is, including the cache-hit path that every build
after the first one takes. See docs/RUNBOOK-FIRST-RUN.md for how the operator
verifies the install itself.
"""

import json
import os

import pytest

from scio_engine.builder.workspace import (
    DEPENDENCIES,
    DEV_DEPENDENCIES,
    WorkspaceUnavailable,
    deps_key,
    discard_workspace,
    install_dependencies,
    package_json,
    prepare_workspace,
    stack_files,
    workspace_root,
)
from scio_engine.core.sandbox import LocalProcessSandbox, SandboxError


@pytest.fixture(autouse=True)
def isolated_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("SCIO_WORKSPACE_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SCIO_DEPS_CACHE", str(tmp_path / "deps"))
    monkeypatch.delenv("SCIO_SCAFFOLD_DIR", raising=False)


def seed_cache(tmp_path, manifest: dict) -> None:
    """Pretend a previous build already installed this dependency set."""
    cache = tmp_path / "deps" / deps_key(manifest)
    (cache / "node_modules" / "next").mkdir(parents=True)
    (cache / "package-lock.json").write_text("{}\n")


class TestTheLockedStack:
    def test_package_json_is_the_stack_adr_0011_locks(self):
        manifest = json.loads(package_json("booking"))
        assert manifest["dependencies"] == DEPENDENCIES
        assert manifest["devDependencies"] == DEV_DEPENDENCIES
        assert "next" in manifest["dependencies"]
        assert "@supabase/supabase-js" in manifest["dependencies"]
        assert "tailwindcss" in manifest["devDependencies"]

    def test_versions_are_pinned(self):
        # A locked stack is only a reliability multiplier if it is the same
        # stack every time — no ^ or ~ ranges.
        for version in {**DEPENDENCIES, **DEV_DEPENDENCIES}.values():
            assert version[0].isdigit(), version

    def test_the_npm_name_survives_an_awkward_project_id(self):
        assert json.loads(package_json("Booking App!"))["name"] == "scio-booking-app"

    def test_tailwind_is_wired_up_end_to_end(self):
        files = stack_files("booking")
        assert "tailwindcss" in files["postcss.config.js"]
        assert "export default config" in files["tailwind.config.ts"]
        assert "@tailwind base" in files["app/globals.css"]

    def test_generated_tests_do_not_break_the_app_build(self):
        # tests/ files use a test runner's globals; type-checking them as part
        # of the app would fail a build for a reason the user cannot act on.
        tsconfig = json.loads(stack_files("booking")["tsconfig.json"])
        assert "tests" in tsconfig["exclude"]


class TestPreparingAWorkspace:
    def test_it_writes_a_compiling_project_before_any_package_runs(self, tmp_path):
        workspace = prepare_workspace("booking", install=False)
        for name in ("package.json", "tsconfig.json", "next.config.js", "postcss.config.js"):
            assert (workspace / name).exists()
        assert (workspace / "app" / "globals.css").exists()

    def test_fresh_clears_a_previous_build(self, tmp_path):
        workspace = prepare_workspace("booking", install=False)
        (workspace / "app" / "stale.tsx").write_text("stale\n")
        again = prepare_workspace("booking", install=False)
        assert not (again / "app" / "stale.tsx").exists()

    def test_a_prepared_scaffold_short_circuits_generation(self, tmp_path, monkeypatch):
        scaffold = tmp_path / "prepared"
        (scaffold / "node_modules").mkdir(parents=True)
        (scaffold / "package.json").write_text('{"name": "prepared"}\n')
        monkeypatch.setenv("SCIO_SCAFFOLD_DIR", str(scaffold))

        workspace = prepare_workspace("booking")
        assert json.loads((workspace / "package.json").read_text())["name"] == "prepared"
        assert (workspace / "node_modules").is_symlink()

    def test_a_scaffold_without_dependencies_is_refused(self, tmp_path, monkeypatch):
        scaffold = tmp_path / "empty"
        scaffold.mkdir()
        monkeypatch.setenv("SCIO_SCAFFOLD_DIR", str(scaffold))
        with pytest.raises(WorkspaceUnavailable, match="node_modules"):
            prepare_workspace("booking")


class TestInstalling:
    def test_a_cached_dependency_set_is_linked_not_reinstalled(self, tmp_path):
        seed_cache(tmp_path, json.loads(package_json("booking")))
        workspace = prepare_workspace("booking")  # would need npm without the cache

        modules = workspace / "node_modules"
        assert modules.is_symlink()
        assert (modules / "next").exists()
        assert (workspace / "package-lock.json").exists()

    def test_the_cache_key_follows_the_dependency_set(self):
        base = json.loads(package_json("booking"))
        same = json.loads(package_json("a-different-project"))
        bumped = {**base, "dependencies": {**base["dependencies"], "next": "15.0.0"}}

        assert deps_key(base) == deps_key(same)
        assert deps_key(base) != deps_key(bumped)

    def test_installing_without_a_manifest_is_an_honest_failure(self, tmp_path):
        with pytest.raises(WorkspaceUnavailable, match="package.json"):
            install_dependencies(tmp_path)

    def test_the_sandbox_still_refuses_to_install_at_startup(self, tmp_path):
        """The ordering guard, restated: prepare -> install -> serve."""
        app = tmp_path / "uninstalled"
        app.mkdir()
        with pytest.raises(SandboxError, match="installed BEFORE"):
            LocalProcessSandbox().start(app)


class TestDiscarding:
    """B100: deleting a project has to delete the project.

    It used to set a timestamp on a row. The code, the git history and the
    screenshots stayed on disk, which makes "deleted" mean "hidden".
    """

    def test_it_removes_the_workspace_and_its_screenshots(self):
        workspace = prepare_workspace("doomed", install=False)
        shots = workspace_root() / "doomed-shots"
        shots.mkdir(parents=True, exist_ok=True)
        (shots / "attempt-1.png").write_bytes(b"x")

        outcome = discard_workspace("doomed")

        assert not workspace.exists()
        assert not shots.exists()
        assert len(outcome["removed"]) == 2
        assert outcome["problems"] == []

    def test_a_project_with_nothing_on_disk_is_not_a_failure(self):
        # Deleting a project that was never built must not report a problem —
        # there is nothing to remove, and that is the correct outcome.
        outcome = discard_workspace("never-built")

        assert outcome == {"removed": [], "problems": []}

    def test_it_cannot_be_walked_out_of_the_workspace_root(self, tmp_path):
        # A project id is data. It arrives from the api, which got it from a
        # database, and one that walks upwards must not take a neighbour with it.
        workspace_root().mkdir(parents=True, exist_ok=True)
        outside = tmp_path / "not-ours"
        outside.mkdir(parents=True, exist_ok=True)
        (outside / "keep.txt").write_text("still here")
        walk_up = os.path.relpath(outside, workspace_root())

        outcome = discard_workspace(walk_up)

        assert (outside / "keep.txt").exists()
        assert outcome["removed"] == []
        assert outcome["problems"]
