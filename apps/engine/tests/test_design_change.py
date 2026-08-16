"""Gate 2a: the design window's backend.

Three promises, and each has a way of being quietly broken:

1. **The bridge is a preview feature.** It must be in the preview build and
   absent from delivery — not present-and-disabled, absent.
2. **A batch changes only what it touches.** Several markings across several
   packages, and every other file byte-identical afterwards.
3. **A conflict with the approved spec is a question, not a build.** The one
   thing that must never happen quietly is undoing a decision the user made at
   gate 1.

The model is scripted here. What is under test is the targeting, the guardrails
and the refusals — not whether a model writes good code.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scio_engine.builder import preview_bridge as PB
from scio_engine.builder.workspace import stack_files
from scio_engine.core.instrumentation import Manifest, SourceLocation
from scio_engine.core.manifest_builder import build_manifest
from scio_engine.design import (
    ChangeBatch,
    Marking,
    apply_change,
    detect_conflicts,
    resolve_batch,
)
from scio_engine.execution.provider import ProviderRegistry
from scio_engine.layerb.architecture import (
    Architecture,
    AuthAccess,
    AuthMode,
    Column,
    DataModel,
    FieldType,
    Operation,
    SecurityPosture,
    Table,
)

# --------------------------------------------------------------------------
# A tiny app with two packages, so "only what you touched" is observable
# --------------------------------------------------------------------------

PACKAGE_FILES = {
    "pkg_foundation": ["app/layout.tsx"],
    "pkg_feature_booking": ["components/booking-form.tsx", "components/booking-list.tsx"],
}

LAYOUT = """export default function RootLayout({ children }) {
  return (
    <html><body data-scio-id="app-shell" data-scio-package="pkg_foundation">{children}</body></html>
  );
}
"""

FORM = """export function BookingForm() {
  return (
    <form data-scio-id="booking-form" data-scio-package="pkg_feature_booking">
      <button data-scio-id="booking-form-submit" data-scio-package="pkg_feature_booking">
        Book a table
      </button>
    </form>
  );
}
"""

LIST = """export function BookingList() {
  return (
    <ul data-scio-id="booking-list" data-scio-package="pkg_feature_booking">
      <li data-scio-id="booking-list-empty" data-scio-package="pkg_feature_booking">
        No bookings yet
      </li>
    </ul>
  );
}
"""


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


def architecture(**overrides) -> Architecture:
    base = Architecture(
        data_model=DataModel(
            tables=[
                Table(
                    name="booking",
                    columns=[
                        Column(name="id", type=FieldType.uuid),
                        Column(name="guest_name", type=FieldType.text),
                    ],
                )
            ]
        ),
        auth_access=AuthAccess(mode=AuthMode.email_link, provider="supabase-auth"),
        operations=[Operation(name="create_booking", verb="create", entity="booking")],
        security_posture=SecurityPosture(
            row_level_security=True, sensitive=True, sensitive_kinds=["personal"]
        ),
        scope_guard=["no payments for now", "no mobile app"],
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def marking(scio_id: str, note: str, package: str = "") -> Marking:
    return Marking(scio_id=scio_id, scio_package=package, note=note, tag="button")


def files(reply: dict[str, str]) -> str:
    """A model reply in the builder's own FILE-block format."""
    return "\n\n".join(f"FILE: {path}\n```tsx\n{body}```" for path, body in reply.items())


# --------------------------------------------------------------------------
# 1. The bridge is a preview feature
# --------------------------------------------------------------------------


class TestTheBridgeIsPreviewOnly:
    def test_a_delivery_build_never_registers_it(self):
        """Absent from the bundle, not disabled inside it."""
        config = stack_files("booking")["next.config.js"]

        assert PB.PREVIEW_FLAG in config
        assert "previewing && !isServer" in config
        # The registration is inside the conditional, so a build without the
        # flag never reaches it.
        after_flag = config.split("if (previewing")[1]
        assert PB.BRIDGE_FILE in after_flag

    def test_the_preview_env_names_who_the_bridge_may_talk_to(self):
        env = PB.preview_env("http://127.0.0.1:5173")

        assert env[PB.PREVIEW_FLAG] == "1"
        assert env[PB.SHELL_ORIGIN_ENV] == "http://127.0.0.1:5173"
        # NEXT_PUBLIC_, or Next would not inline it into the client bundle and
        # the bridge would have no origin to post to.
        assert PB.SHELL_ORIGIN_ENV.startswith("NEXT_PUBLIC_")

    def test_it_is_written_into_scio_not_into_the_users_code(self, app: Path):
        PB.prepare(app)

        assert (app / PB.BRIDGE_FILE).exists()
        assert PB.BRIDGE_FILE.startswith(".scio/")
        assert (app / ".scio" / ".gitignore").read_text().strip() == "*"
        # The generated files are untouched: the manifest maps ids to source
        # lines, and injecting into layout.tsx would move every one of them.
        assert (app / "app" / "layout.tsx").read_text() == LAYOUT

    def test_the_bridge_reports_the_ancestor_but_never_substitutes_it(self):
        """B039's bug, on the far side of an origin boundary where the
        guardrail cannot see it."""
        source = PB.BRIDGE_SOURCE.read_text()

        assert "scio_id: node.getAttribute(ID)" in source
        assert "ancestor_id:" in source
        assert "|| ancestor" not in source

    def test_the_bridge_posts_only_to_the_shell_origin(self):
        source = PB.BRIDGE_SOURCE.read_text()

        assert "window.parent.postMessage(message, SHELL_ORIGIN)" in source
        assert "event.origin !== SHELL_ORIGIN" in source

    def test_the_bridge_does_nothing_outside_an_iframe(self):
        """Belt and braces: even if a delivery build somehow served it."""
        source = PB.BRIDGE_SOURCE.read_text()

        assert "window.top === window.self" in source
        assert source.index("window.top === window.self") < source.index("addEventListener")

    def test_preview_mode_is_off_unless_asked_for(self):
        assert PB.preview_enabled({}) is False
        assert PB.preview_enabled({PB.PREVIEW_FLAG: "0"}) is False
        assert PB.preview_enabled({PB.PREVIEW_FLAG: "1"}) is True


# --------------------------------------------------------------------------
# 2. Resolution: per marking, never per batch
# --------------------------------------------------------------------------


class TestResolvingABatch:
    def test_it_groups_by_package(self, manifest: Manifest):
        batch = ChangeBatch(
            markings=[
                marking("booking-form-submit", "say Reserve"),
                marking("booking-list-empty", "mention the date"),
                marking("app-shell", "more padding"),
            ]
        )

        resolved = resolve_batch(batch, manifest)

        assert resolved.packages == ["pkg_feature_booking", "pkg_foundation"]
        assert len(resolved.by_package()["pkg_feature_booking"]) == 2

    def test_one_unaddressable_marking_does_not_spoil_the_others(self, manifest: Manifest):
        """Otherwise people learn to mark one thing at a time."""
        batch = ChangeBatch(
            markings=[
                marking("booking-form-submit", "say Reserve"),
                Marking(scio_id=None, ancestor_id="booking-form", note="this bit", tag="div"),
            ]
        )

        resolved = resolve_batch(batch, manifest)

        assert len(resolved.addressable) == 1
        assert len(resolved.unaddressable) == 1
        assert "no data-scio-id" in resolved.unaddressable[0].error
        # The ancestor is named as evidence and is not the answer.
        assert "booking-form" in resolved.unaddressable[0].error
        assert resolved.unaddressable[0].package == ""

    def test_the_instruction_carries_the_users_own_words_and_the_source_line(
        self, manifest: Manifest
    ):
        batch = ChangeBatch(
            markings=[marking("booking-form-submit", "should say Reserve our table")],
            prompt="warmer wording throughout",
        )

        instruction = resolve_batch(batch, manifest).instruction_for("pkg_feature_booking")

        assert "warmer wording throughout" in instruction
        assert "should say Reserve our table" in instruction
        assert "components/booking-form.tsx" in instruction


# --------------------------------------------------------------------------
# 3. Conflicts are questions, not builds
# --------------------------------------------------------------------------


class TestConflicts:
    def test_asking_for_something_the_spec_excluded_is_a_conflict(self):
        batch = ChangeBatch(markings=[marking("booking-form-submit", "add payments here")])

        conflicts = detect_conflicts(batch, architecture())

        assert len(conflicts) == 1
        assert conflicts[0].kind == "non_goal"
        assert "no payments for now" in conflicts[0].spec_says
        assert "?" in conflicts[0].question  # it asks; it does not refuse

    def test_the_batch_prompt_counts_too(self):
        """"Make it all public" in the box is the same request as on an element."""
        batch = ChangeBatch(prompt="make the bookings public so anyone can see them")

        conflicts = detect_conflicts(batch, architecture())

        assert [c.kind for c in conflicts] == ["access"]

    def test_removing_sign_in_the_spec_requires_is_a_conflict(self):
        batch = ChangeBatch(markings=[marking("app-shell", "remove the login, nobody needs it")])

        conflicts = detect_conflicts(batch, architecture())

        assert [c.kind for c in conflicts] == ["auth"]

    def test_an_app_with_no_sign_in_is_not_nagged_about_removing_it(self):
        arch = architecture()
        arch.auth_access = AuthAccess(mode=AuthMode.none)
        batch = ChangeBatch(markings=[marking("app-shell", "remove the login prompt")])

        assert detect_conflicts(batch, arch) == []

    def test_an_ordinary_change_is_not_a_conflict(self):
        batch = ChangeBatch(
            markings=[
                marking("booking-form-submit", "should say Reserve our table"),
                marking("booking-list-empty", "add the date to each row"),
            ],
            prompt="warmer wording",
        )

        assert detect_conflicts(batch, architecture()) == []

    def test_it_matches_the_projects_own_vocabulary_not_the_literal_string(self):
        """Layer B collapses "reservations" and "booking" to one name; a check
        that only matched the literal string would miss the common case."""
        arch = architecture()
        arch.scope_guard = ["no reservations by phone"]
        batch = ChangeBatch(markings=[marking("booking-form", "add booking by phone")])

        assert [c.kind for c in detect_conflicts(batch, arch)] == ["non_goal"]


# --------------------------------------------------------------------------
# 4. The round trip: only what was touched
# --------------------------------------------------------------------------


def scripted(*replies: str) -> ProviderRegistry:
    return ProviderRegistry.scripted(list(replies), loop_last=False)


class TestTheRoundTrip:
    async def test_a_batch_changes_only_the_packages_it_touches(
        self, app: Path, manifest: Manifest
    ):
        before = (app / "app" / "layout.tsx").read_text()
        batch = ChangeBatch(
            markings=[
                marking("booking-form-submit", "say Reserve our table"),
                marking("booking-list-empty", "say Nothing booked yet"),
            ]
        )

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(
                files(
                    {
                        "components/booking-form.tsx": FORM.replace(
                            "Book a table", "Reserve our table"
                        ),
                        "components/booking-list.tsx": LIST.replace(
                            "No bookings yet", "Nothing booked yet"
                        ),
                    }
                )
            ),
            package_files=PACKAGE_FILES,
        )

        assert result.applied
        assert result.changed_packages == ["pkg_feature_booking"]
        assert "Reserve our table" in (app / "components" / "booking-form.tsx").read_text()
        assert "Nothing booked yet" in (app / "components" / "booking-list.tsx").read_text()
        # The proof, not the intention: the other package is byte-identical.
        assert (app / "app" / "layout.tsx").read_text() == before
        assert result.packages[0].isolated
        assert result.packages[0].unchanged_files == 1

    async def test_a_conflict_stops_the_change_before_a_token_is_spent(
        self, app: Path, manifest: Manifest
    ):
        before = (app / "components" / "booking-form.tsx").read_text()
        batch = ChangeBatch(
            markings=[
                marking("booking-form-submit", "say Reserve"),
                marking("booking-form", "and add payments"),
            ]
        )

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            # Would raise if it were ever called: nothing may be generated.
            registry=scripted("this reply must never be used"),
            package_files=PACKAGE_FILES,
        )

        assert result.applied is False
        assert [c.kind for c in result.conflicts] == ["non_goal"]
        assert result.packages == []
        assert result.total_cost_usd == 0.0
        assert (app / "components" / "booking-form.tsx").read_text() == before
        assert "need your call" in result.summary()

    async def test_a_change_that_loses_an_id_is_rolled_back(
        self, app: Path, manifest: Manifest
    ):
        """The guardrail that makes marking trustworthy at all (B039): a lost id
        means the next marking resolves somewhere else."""
        before = (app / "components" / "booking-form.tsx").read_text()
        batch = ChangeBatch(markings=[marking("booking-form-submit", "say Reserve")])

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(
                files(
                    {
                        "components/booking-form.tsx": FORM.replace(
                            'data-scio-id="booking-form-submit" ', ""
                        ).replace("Book a table", "Reserve our table")
                    }
                )
            ),
            package_files=PACKAGE_FILES,
        )

        assert result.applied is False
        assert result.packages[0].rolled_back
        assert "instrumentation" in result.packages[0].rejection
        assert (app / "components" / "booking-form.tsx").read_text() == before

    async def test_an_unaddressable_marking_is_reported_and_skipped(
        self, app: Path, manifest: Manifest
    ):
        batch = ChangeBatch(
            markings=[
                marking("booking-form-submit", "say Reserve our table"),
                Marking(scio_id=None, ancestor_id="booking-form", note="this too", tag="div"),
            ]
        )

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(
                files({"components/booking-form.tsx": FORM.replace("Book a table", "Reserve")})
            ),
            package_files=PACKAGE_FILES,
        )

        assert result.applied
        assert len(result.unaddressable) == 1
        assert "could not be addressed" in result.summary()

    async def test_a_batch_with_nothing_addressable_changes_nothing(
        self, app: Path, manifest: Manifest
    ):
        batch = ChangeBatch(
            markings=[Marking(scio_id=None, note="this thing", tag="div")],
        )

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted("never used"),
            package_files=PACKAGE_FILES,
        )

        assert result.applied is False
        assert result.packages == []
        assert "no marking could be addressed" in result.summary().lower()

    async def test_a_model_that_edits_a_file_the_package_does_not_own_is_refused(
        self, app: Path, manifest: Manifest
    ):
        before = (app / "app" / "layout.tsx").read_text()
        batch = ChangeBatch(markings=[marking("booking-form-submit", "say Reserve")])

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(files({"app/layout.tsx": LAYOUT.replace("html", "html lang=en")})),
            package_files=PACKAGE_FILES,
        )

        assert result.applied is False
        assert (app / "app" / "layout.tsx").read_text() == before

    async def test_the_manifest_comes_back_so_the_next_marking_resolves(
        self, app: Path, manifest: Manifest
    ):
        batch = ChangeBatch(markings=[marking("booking-form-submit", "say Reserve our table")])

        result = await apply_change(
            app,
            batch,
            manifest=manifest,
            architecture=architecture(),
            registry=scripted(
                files(
                    {
                        "components/booking-form.tsx": FORM.replace(
                            "Book a table", "Reserve our table"
                        )
                    }
                )
            ),
            package_files=PACKAGE_FILES,
        )

        assert result.manifest is not None
        assert "booking-form-submit" in result.manifest.elements
        location: SourceLocation = result.manifest.elements["booking-form-submit"]
        assert location.package == "pkg_feature_booking"


class TestTheRequestShape:
    def test_a_batch_serialises_the_way_the_bridge_sends_it(self):
        """The payload is core.resolver.ElementHit plus the note — so the api
        has nothing to translate, and no place to soften a refusal."""
        payload = json.loads(
            Marking(
                scio_id="booking-form-submit",
                scio_package="pkg_feature_booking",
                tag="button",
                ancestor_id="booking-form",
                note="say Reserve",
            ).model_dump_json()
        )

        assert set(payload) >= {
            "scio_id",
            "scio_package",
            "tag",
            "ancestor_id",
            "ancestor_package",
            "note",
        }
