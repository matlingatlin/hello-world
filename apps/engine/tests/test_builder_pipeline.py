"""The whole path in one stream (B052): spec -> Layer B -> Layer C -> running app.

The stages are tested individually elsewhere. What is proven here is the seam —
that an approved spec reaches a built, assembled, persisted app without anyone
hand-carrying anything between the layers, and that the events a build view would
draw are real.
"""

from pathlib import Path

import pytest

from scio_engine.builder.loop import ScriptedPreview
from scio_engine.builder.pipeline import (
    BuildFinished,
    BuildStarted,
    stream_full_build,
    stream_promotion,
)
from scio_engine.builder.plan_store import PLAN_PATH, load_plan
from scio_engine.builder.standin import (
    PASS_VERDICT,
    StandInProvider,
    echo_current_files,
    generate_files,
    standin_registry,
)
from scio_engine.builder.workspace import WorkspaceUnavailable
from scio_engine.core.console import ConsoleEntry, classify_console
from scio_engine.core.preview import Observation
from scio_engine.execution.provider import Message, ProviderRegistry
from scio_engine.intake.schema import AppSpec, DataSensitivity, FieldMeta
from scio_engine.layerb.service import NotBuildableError


def booking_spec() -> AppSpec:
    return AppSpec(
        purpose=FieldMeta(value="Guests book a table and get a confirmation."),
        users_and_roles=FieldMeta(value=["guests"]),
        entities=FieldMeta(value=["bookings", "tables", "guests"]),
        key_actions=FieldMeta(value=["book a table", "cancel a booking"]),
        sign_in=FieldMeta(value="No account — name and phone."),
        data_ownership_sensitivity=FieldMeta(
            value=DataSensitivity(owner="you", sensitive=False, kinds=[])
        ),
        non_goals=FieldMeta(value=["no payments for now"]),
    )


def clean(count: int = 40) -> ScriptedPreview:
    """A preview that reports a clean, benign-noise-only page every time."""
    favicon = ConsoleEntry(
        type="error",
        text="Failed to load resource: the server responded with a status of 404",
        url="http://127.0.0.1:3000/favicon.ico",
    )
    return ScriptedPreview(
        [
            Observation(
                screenshot_path=None, console=classify_console([favicon]), title="Scio app"
            )
        ]
        * count
    )


PROMPT = """# Build package: pkg_feature_booking (feature)

## The architecture you own (build exactly this)
operation create_booking — book a table on booking; inputs: name: text; returns: booking
screen /booking at /booking — book a table; uses: create_booking

---

Write the complete code for `pkg_feature_booking`. Every file you return must be one
this package owns:
- app/booking/page.tsx
- components/booking-form.tsx
- lib/db/booking.ts
- tests/booking.test.ts
"""


class TestStandIn:
    """It is not a model. It only has to produce something the contract accepts."""

    def test_it_writes_exactly_the_files_the_prompt_names(self):
        output = generate_files(PROMPT)

        for path in (
            "app/booking/page.tsx",
            "components/booking-form.tsx",
            "lib/db/booking.ts",
            "tests/booking.test.ts",
        ):
            assert f"FILE: {path}" in output

    def test_every_ui_element_is_instrumented(self):
        output = generate_files(PROMPT)

        # Without this the verifier rejects the build, which is the point of it.
        assert 'data-scio-id="' in output
        assert 'data-scio-package="pkg_feature_booking"' in output

    def test_the_operations_it_owns_appear_in_its_code(self):
        # The contract-consistency agent checks exactly this.
        assert "create_booking" in generate_files(PROMPT)

    def test_a_fix_returns_the_code_unchanged(self):
        current = "FILE: a.tsx\n```\n<div data-scio-id=\"keep-me\" />\n```"
        prompt = f"## The current code for `pkg_x`\n\n{current}\n\n## What is wrong\n\n1. something"

        echoed = echo_current_files(prompt)

        # Inventing an edit here would corrupt the instrumentation being checked.
        assert 'data-scio-id="keep-me"' in echoed

    @pytest.mark.asyncio
    async def test_it_answers_a_critique_with_a_verdict_not_code(self):
        provider = StandInProvider()
        critique = "## Acceptance criteria (judge against exactly these)\n- x"
        completion = await provider.complete("any-model", [Message(role="user", content=critique)])
        assert completion.text == PASS_VERDICT

    def test_the_registry_is_not_mistaken_for_the_fake_one(self):
        # is_fake drives real decisions (the whole's fallback); the stand-in
        # produces real text, so it must not be counted as a fake provider.
        assert standin_registry().is_fake is False


class TestFullBuild:
    @pytest.mark.asyncio
    async def test_an_approved_spec_becomes_an_assembled_app(self, tmp_path: Path):
        events = []
        async for event, payload in stream_full_build(
            booking_spec(),
            project_id="p1",
            registry=ProviderRegistry.fake(),
            preview=clean(),
            app_dir=tmp_path,
        ):
            events.append((event, payload))

        kinds = [event for event, _ in events]
        assert kinds[0] == "started"
        assert kinds[-1] == "finished"

        started = events[0][1]
        assert isinstance(started, BuildStarted)
        assert started.packages[0] == "pkg_foundation"  # dependency order, from Layer C
        assert started.total == len(started.packages)
        assert started.whole  # the confirmation carried through from Layer B

        finished = events[-1][1]
        assert isinstance(finished, BuildFinished)
        assert finished.works is True
        assert finished.git_sha
        assert finished.build_version == 1
        assert finished.element_count > 0
        assert finished.standin is True  # honest: no model wrote this code

    @pytest.mark.asyncio
    async def test_it_reports_every_page_the_app_has(self, tmp_path: Path):
        # The design window can only offer the pages it is told about, and it
        # used to be told about none (B069).
        finished = None
        async for event, payload in stream_full_build(
            booking_spec(),
            project_id="p-routes",
            registry=ProviderRegistry.fake(),
            preview=clean(),
            app_dir=tmp_path,
        ):
            if event == "finished":
                finished = payload

        assert isinstance(finished, BuildFinished)
        assert "/" in finished.routes  # the front door leads, because that is where you land
        assert finished.routes[0] == "/"
        assert len(finished.routes) == len(set(finished.routes))  # named once each

    @pytest.mark.asyncio
    async def test_progress_counts_parts_that_actually_finished(self, tmp_path: Path):
        finished_events = []
        total = 0
        async for event, payload in stream_full_build(
            booking_spec(),
            project_id="p2",
            registry=ProviderRegistry.fake(),
            preview=clean(),
            app_dir=tmp_path,
        ):
            if event == "started":
                total = payload.total
            if event == "progress" and payload.status != "building":
                finished_events.append(payload.done)

        assert finished_events == list(range(1, total + 1))

    @pytest.mark.asyncio
    async def test_the_assembled_app_is_committed_with_its_manifest(self, tmp_path: Path):
        async for _event, _payload in stream_full_build(
            booking_spec(),
            project_id="p3",
            registry=ProviderRegistry.fake(),
            preview=clean(),
            app_dir=tmp_path,
        ):
            pass

        assert (tmp_path / "scio-manifest.json").exists()
        assert (tmp_path / ".git").exists()
        assert (tmp_path / "app" / "layout.tsx").exists()

    @pytest.mark.asyncio
    async def test_a_spec_that_never_passed_the_gate_is_refused(self, tmp_path: Path):
        half_answered = AppSpec(purpose=FieldMeta(value="Something vague."))

        with pytest.raises(NotBuildableError):
            async for _event, _payload in stream_full_build(
                half_answered,
                project_id="p4",
                registry=ProviderRegistry.fake(),
                preview=clean(),
                app_dir=tmp_path,
            ):
                pass

        # It never got as far as writing anything.
        assert not (tmp_path / "app").exists()


class TestPromotion:
    """B070: "Build it" delivers the app the design window produced.

    It used to recreate the workspace from the spec, which threw away both the
    version history the design panel offers to return to and — the larger loss,
    and the quieter one — every change the user had made in that session.
    """

    async def _build(self, tmp_path: Path, project_id: str = "p1") -> None:
        async for _event, _payload in stream_full_build(
            booking_spec(),
            project_id=project_id,
            registry=ProviderRegistry.fake(),
            preview=clean(),
            app_dir=tmp_path,
        ):
            pass

    @pytest.mark.asyncio
    async def test_a_build_leaves_its_plan_with_the_app(self, tmp_path: Path):
        await self._build(tmp_path)

        stored = load_plan(tmp_path)
        assert stored is not None
        assert stored.plan.order  # the same order the build ran in
        assert stored.contracts  # and the contracts each part was judged against
        assert (tmp_path / PLAN_PATH).exists()

    @pytest.mark.asyncio
    async def test_a_promotion_delivers_the_files_that_are_there(self, tmp_path: Path):
        await self._build(tmp_path)
        # Stand in for a design change: the user edited the app by hand.
        page = tmp_path / "app" / "layout.tsx"
        page.write_text(page.read_text() + "\n// the user asked for this\n")

        events = []
        async for event, payload in stream_promotion(
            project_id="p1",
            app_dir=tmp_path,
            registry=ProviderRegistry.fake(),
            build_version=2,
            preview=clean(),
        ):
            events.append((event, payload))

        assert [e for e, _ in events][0] == "started"
        assert [e for e, _ in events][-1] == "finished"
        # The edit survived: nothing regenerated the file.
        assert "the user asked for this" in page.read_text()

    @pytest.mark.asyncio
    async def test_a_promotion_judges_every_part_it_delivers(self, tmp_path: Path):
        await self._build(tmp_path)

        finished = None
        checked = []
        async for event, payload in stream_promotion(
            project_id="p1",
            app_dir=tmp_path,
            registry=ProviderRegistry.fake(),
            build_version=2,
            preview=clean(),
        ):
            if event == "package":
                checked.append(payload.package_id)
            if event == "finished":
                finished = payload

        assert isinstance(finished, BuildFinished)
        stored = load_plan(tmp_path)
        assert stored is not None
        # Delivered means checked: every part in the plan was judged, not waved through.
        assert checked == stored.plan.order

    @pytest.mark.asyncio
    async def test_a_promotion_does_not_downgrade_what_the_build_passed(self, tmp_path: Path):
        """Found by clicking through the free path, not by a test.

        The preview said "5 of 5 parts work" and the delivery said "3 of 5", on
        files nobody had touched. With no key the fake provider answers a
        critique with a digest, an unreadable verdict is a failure, and the
        promotion was judging with the ordinary registry while the build had
        judged with the stand-in.
        """
        await self._build(tmp_path)

        built = None
        async for event, payload in stream_full_build(
            booking_spec(),
            project_id="p1",
            registry=ProviderRegistry.fake(),
            preview=clean(),
            app_dir=tmp_path,
        ):
            if event == "finished":
                built = payload

        promoted = None
        async for event, payload in stream_promotion(
            project_id="p1",
            app_dir=tmp_path,
            registry=ProviderRegistry.fake(),
            build_version=2,
            preview=clean(),
        ):
            if event == "finished":
                promoted = payload

        assert isinstance(built, BuildFinished) and isinstance(promoted, BuildFinished)
        assert promoted.parts_working == built.parts_working

    @pytest.mark.asyncio
    async def test_the_delivered_app_keeps_the_history_it_was_built_with(self, tmp_path: Path):
        await self._build(tmp_path)
        before = (tmp_path / ".git").exists()

        async for _event, _payload in stream_promotion(
            project_id="p1",
            app_dir=tmp_path,
            registry=ProviderRegistry.fake(),
            build_version=2,
            preview=clean(),
        ):
            pass

        assert before and (tmp_path / ".git").exists()

    @pytest.mark.asyncio
    async def test_a_workspace_with_no_plan_is_refused_rather_than_rebuilt(self, tmp_path: Path):
        # Silently falling back to a rebuild would be the exact data loss this
        # exists to prevent — and invisible to the person it happens to.
        with pytest.raises(WorkspaceUnavailable):
            async for _event, _payload in stream_promotion(
                project_id="p1",
                app_dir=tmp_path,
                registry=ProviderRegistry.fake(),
                preview=clean(),
            ):
                pass
