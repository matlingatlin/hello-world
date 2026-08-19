"""Going back, and the one way a conflict stops being one.

Gate 2b makes two promises the backend has to keep:

1. **A design version can be returned to.** The versions panel is otherwise a
   list of things that happened, which is not the same as being able to undo
   them — and "you can keep asking without fear" is the whole reason someone
   marks a fifth thing.
2. **A conflict is answered once, in writing.** A security decision the spec
   derived (ADR-0001) is never quietly undone. It can be allowed — but only by
   an allowance quoting the exact sentence the question asked about, which the
   api freezes into a spec version.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scio_engine.builder.persistence import ensure_repo, git
from scio_engine.builder.standin import standin_registry
from scio_engine.core.instrumentation import Manifest
from scio_engine.core.manifest_builder import build_manifest
from scio_engine.design import (
    ChangeBatch,
    Marking,
    apply_change,
    detect_conflicts,
    restore_version,
)
from scio_engine.execution.provider import ProviderRegistry
from test_design_change import (
    FORM,
    LAYOUT,
    LIST,
    PACKAGE_FILES,
    architecture,
    files,
    marking,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def app(tmp_path: Path) -> Path:
    (tmp_path / "app").mkdir()
    (tmp_path / "components").mkdir()
    (tmp_path / "app" / "layout.tsx").write_text(LAYOUT)
    (tmp_path / "components" / "booking-form.tsx").write_text(FORM)
    (tmp_path / "components" / "booking-list.tsx").write_text(LIST)
    return tmp_path


@pytest.fixture
def manifest(app: Path) -> Manifest:
    return build_manifest(app, PACKAGE_FILES)


@pytest.fixture
def repo(app: Path) -> Path:
    """The same little app, as it actually exists: a git repo from its first build."""
    ensure_repo(app)
    git(app, "add", "-A")
    git(app, "commit", "-q", "-m", "build: the first preview")
    return app


RESERVE = FORM.replace("Book a table", "Reserve our table")


def sha(app: Path) -> str:
    return git(app, "rev-parse", "HEAD")


def scripted(*replies: str) -> ProviderRegistry:
    return ProviderRegistry.scripted(list(replies), loop_last=False)


class TestAChangeCanBeReturnedTo:
    async def test_an_applied_change_is_a_commit(self, repo: Path, manifest: Manifest):
        before = sha(repo)

        result = await apply_change(
            repo,
            ChangeBatch(markings=[marking("booking-form-submit", "say Reserve our table")]),
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(files({"components/booking-form.tsx": RESERVE})),
            package_files=PACKAGE_FILES,
        )

        assert result.applied
        assert result.git_sha and result.git_sha != before
        assert not result.persistence_error
        # The coupling is in the same commit as the code it describes.
        assert "scio-manifest.json" in git(repo, "show", "--name-only", "--format=", result.git_sha)

    async def test_returning_puts_the_old_code_back_without_losing_the_new(
        self, repo: Path, manifest: Manifest
    ):
        first = sha(repo)

        await apply_change(
            repo,
            ChangeBatch(markings=[marking("booking-form-submit", "say Reserve our table")]),
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(files({"components/booking-form.tsx": RESERVE})),
            package_files=PACKAGE_FILES,
        )
        changed = sha(repo)
        assert "Reserve our table" in (repo / "components" / "booking-form.tsx").read_text()

        result = restore_version(repo, first, package_files=PACKAGE_FILES)

        assert result.restored, result.error
        assert (repo / "components" / "booking-form.tsx").read_text() == FORM
        # Forward, not backward: the version we came from is still a commit, so
        # "actually I preferred the new one" is another restore, not a recovery job.
        assert git(repo, "cat-file", "-t", changed) == "commit"
        assert result.head != first

    async def test_the_restored_manifest_is_rebuilt_from_the_restored_source(
        self, repo: Path, manifest: Manifest
    ):
        first = sha(repo)
        (repo / "components" / "booking-list.tsx").write_text(
            LIST.replace('data-scio-id="booking-list-empty"', 'data-scio-id="booking-list-nothing"')
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "design: rename an id")

        result = restore_version(repo, first, package_files=PACKAGE_FILES)

        assert result.restored, result.error
        assert result.manifest is not None
        assert "booking-list-empty" in result.manifest.elements
        assert "booking-list-nothing" not in result.manifest.elements


class TestARestoreIsAWrite:
    async def test_a_version_that_no_longer_verifies_is_refused_and_undone(self, repo: Path):
        """Two elements with one id: a marking could not say which it meant."""
        broken = LIST.replace('data-scio-id="booking-list-empty"', 'data-scio-id="booking-list"')
        (repo / "components" / "booking-list.tsx").write_text(broken)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "design: a version with a duplicate id")
        bad = sha(repo)

        (repo / "components" / "booking-list.tsx").write_text(LIST)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "design: put the id back")
        good = (repo / "components" / "booking-list.tsx").read_text()

        result = restore_version(repo, bad, package_files=PACKAGE_FILES)

        assert result.restored is False
        assert "no longer matches its instrumentation" in result.error
        # Undone, not left half-restored.
        assert (repo / "components" / "booking-list.tsx").read_text() == good

    async def test_an_unknown_version_is_reported_not_raised(self, repo: Path):
        result = restore_version(repo, "deadbeef", package_files=PACKAGE_FILES)

        assert result.restored is False
        assert result.error

    async def test_a_workspace_that_is_not_a_repo_is_reported(self, app: Path):
        result = restore_version(app, "HEAD", package_files=PACKAGE_FILES)

        assert result.restored is False
        assert "not a git repository" in result.error


class TestAnAllowanceSilencesOnlyWhatItAnswered:
    def test_without_one_the_question_is_still_asked(self):
        batch = ChangeBatch(markings=[marking("booking-form", "make the bookings public")])

        conflicts = detect_conflicts(batch, architecture())

        assert [c.kind for c in conflicts] == ["access"]

    def test_the_exact_sentence_the_question_quoted_silences_it(self):
        batch = ChangeBatch(markings=[marking("booking-form", "make the bookings public")])
        asked = detect_conflicts(batch, architecture())[0]

        after = detect_conflicts(batch, architecture(), allowances=[asked.spec_says])

        assert after == []

    def test_a_different_allowance_does_not(self):
        """An allowance is not a switch that turns the questions off."""
        batch = ChangeBatch(
            markings=[
                marking("booking-form", "make the bookings public"),
                marking("app-shell", "remove the login"),
            ]
        )
        access = next(c for c in detect_conflicts(batch, architecture()) if c.kind == "access")

        after = detect_conflicts(batch, architecture(), allowances=[access.spec_says])

        assert [c.kind for c in after] == ["auth"]

    async def test_an_allowed_conflict_is_actually_built(self, repo: Path, manifest: Manifest):
        batch = ChangeBatch(markings=[Marking(scio_id="booking-list", note="make it public")])
        asked = detect_conflicts(batch, architecture())
        assert asked, "the fixture must produce a conflict for this test to mean anything"

        result = await apply_change(
            repo,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(
                files({"components/booking-list.tsx": LIST.replace("No bookings", "Every booking")})
            ),
            package_files=PACKAGE_FILES,
            allowances=[asked[0].spec_says],
        )

        assert result.conflicts == []
        assert result.applied


class TestTheFreePathCanActuallyDoThis:
    """Without keys, gate 2 has to still round-trip — or it breaks unnoticed.

    The ordinary fake provider returns a digest, so extraction fails and the
    design window stops dead with "No FILE blocks in the reply". That is what
    the stand-in exists to prevent for the builder, and it now covers the
    directed change too.
    """

    async def test_a_change_applies_and_commits_with_no_model_at_all(
        self, repo: Path, manifest: Manifest
    ):
        result = await apply_change(
            repo,
            ChangeBatch(markings=[marking("booking-form-submit", "say Reserve our table")]),
            manifest=manifest,
            architecture=architecture(),
            registry=standin_registry(),
            package_files=PACKAGE_FILES,
        )

        assert result.applied, result.summary()
        assert result.git_sha
        changed = (repo / "components" / "booking-form.tsx").read_text()
        # It says what it is, rather than pretending a model wrote it.
        assert "scio stand-in" in changed
        assert "say Reserve our table" in changed
        # And every id is exactly where it was — the coupling is the one thing
        # a stand-in must not damage.
        assert 'data-scio-id="booking-form-submit"' in changed
        assert 'data-scio-id="booking-form"' in changed
        assert result.packages[0].isolated

    async def test_a_second_change_does_not_stack_up_notes(
        self, repo: Path, manifest: Manifest
    ):
        for note in ("say Reserve", "say Book now"):
            result = await apply_change(
                repo,
                ChangeBatch(markings=[marking("booking-form-submit", note)]),
                manifest=manifest,
                architecture=architecture(),
                registry=standin_registry(),
                package_files=PACKAGE_FILES,
            )
            assert result.applied, result.summary()
            manifest = result.manifest or manifest

        changed = (repo / "components" / "booking-form.tsx").read_text()
        assert changed.count("scio stand-in") == 1
        assert "say Book now" in changed
