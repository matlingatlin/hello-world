"""The single-package build loop (B041a).

Three things are worth proving here, and they are the three the spike said would
bite: the loop's guardrails actually stop a bad build, benign noise does not,
and a package that cannot be finished comes back honest instead of cheerful.
"""

from pathlib import Path

import pytest

from scio_engine.builder.codegen import CodeExtractionError, extract_files
from scio_engine.builder.file_plan import planned_files
from scio_engine.builder.loop import BuildOptions, ScriptedPreview, build_package
from scio_engine.builder.result import PackageStatus
from scio_engine.core.console import ConsoleEntry, classify_console
from scio_engine.core.preview import Observation
from scio_engine.execution.provider import (
    Completion,
    ModelProvider,
    ProviderRegistry,
    Vendor,
)
from scio_engine.layerc.plan import BuildPackage, NodeRef, PackageKind

PACKAGE_ID = "pkg_feature_booking"


@pytest.fixture
def package() -> BuildPackage:
    return BuildPackage(
        id=PACKAGE_ID,
        kind=PackageKind.feature,
        goal="A guest can book a table and see their bookings.",
        architecture_slice=[
            NodeRef(kind="operation", name="create_booking"),
            NodeRef(kind="screen", name="/booking"),
        ],
        acceptance_criteria=["A guest can book a table in a few taps."],
    )


# --- what the "model" returns -------------------------------------------------
# Written by hand rather than generated, so a test failure means the loop changed
# its mind about something — never that a model did.

GOOD_CODE = """Here is the package.

FILE: app/booking/page.tsx
```tsx
export default function BookingPage() {
  return (
    <main data-scio-id="booking-page" data-scio-package="pkg_feature_booking">
      <BookingForm />
    </main>
  );
}
```

FILE: components/booking-form.tsx
```tsx
export function BookingForm() {
  return (
    <form data-scio-id="booking-form" data-scio-package="pkg_feature_booking">
      <button data-scio-id="booking-submit" data-scio-package="pkg_feature_booking">
        Book a table
      </button>
    </form>
  );
}
```

FILE: components/booking-list.tsx
```tsx
export function BookingList({ rows }) {
  return (
    <ul data-scio-id="booking-list" data-scio-package="pkg_feature_booking">
      {rows.map((row) => (
        <li
          key={row.id}
          data-scio-id={`booking-row-${row.id}`}
          data-scio-package="pkg_feature_booking"
        >
          {row.name}
        </li>
      ))}
    </ul>
  );
}
```

FILE: lib/db/booking.ts
```ts
export async function create_booking(input) {
  return await db.from("bookings").insert(input);
}
```

FILE: lib/validation/booking.ts
```ts
export const bookingSchema = { name: "string" };
```

FILE: app/actions/booking.ts
```ts
"use server";

import { create_booking } from "@/lib/db/booking";

export async function createBookingAction(formData: FormData) {
  return create_booking({ name: String(formData.get("name")) });
}
```

FILE: tests/booking.test.ts
```ts
test("create_booking stores a booking", async () => {
  expect(await create_booking({ name: "Ada" })).toBeTruthy();
});
```
"""

# The careless regeneration from the spike: the submit button loses its id.
CODE_WITH_DROPPED_ID = GOOD_CODE.replace(
    '<button data-scio-id="booking-submit" data-scio-package="pkg_feature_booking">',
    "<button>",
)

CRITIQUE_PASS = """{"verdict": "pass",
 "criteria": [{"criterion": "A guest can book a table in a few taps.",
               "met": true, "why": "The form renders with a submit control."}],
 "problems": []}"""

CRITIQUE_FAIL = """{"verdict": "fail",
 "criteria": [{"criterion": "A guest can book a table in a few taps.",
               "met": false, "why": "The form never asks for a date."}],
 "problems": ["The booking form has no date field, so a guest cannot say when."]}"""


def clean_observation() -> Observation:
    return Observation(screenshot_path=None, console=classify_console([]), title="Book a table")


def observation_with(entries: list[ConsoleEntry]) -> Observation:
    return Observation(
        screenshot_path=None, console=classify_console(entries), title="Book a table"
    )


def one_pass(**overrides) -> BuildOptions:
    """One relay pass per step, so the script maps 1:1 onto model calls."""
    base = dict(max_attempts=2, codegen_passes=1, critique_passes=1, build_version=1)
    base.update(overrides)
    return BuildOptions(**base)


async def run(package, app_dir, replies, observations, options):
    return await build_package(
        package,
        "## Goal\nA guest can book a table.\n",
        app_dir,
        registry=ProviderRegistry.scripted(replies, loop_last=False),
        preview=ScriptedPreview(observations),
        options=options,
    )


class TestHappyPath:
    async def test_generates_verifies_and_passes_in_one_attempt(self, package, tmp_path):
        result = await run(
            package,
            tmp_path,
            [GOOD_CODE, CRITIQUE_PASS],
            [clean_observation()],
            one_pass(),
        )

        assert result.status is PackageStatus.passed
        assert result.checks_passed == result.checks_total == 5
        assert len(result.attempts) == 1
        assert result.files == sorted(planned_files(package))
        assert result.remainders == []
        assert "works" in result.honest_status()

    async def test_persists_the_build_with_its_manifest(self, package, tmp_path):
        result = await run(
            package,
            tmp_path,
            [GOOD_CODE, CRITIQUE_PASS],
            [clean_observation()],
            one_pass(),
        )

        assert result.git_sha
        assert result.build_version == 1
        # The coupling is committed WITH the code — a restored version must carry
        # its own manifest (core/persistence).
        assert (tmp_path / "scio-manifest.json").exists()
        assert (tmp_path / ".git").exists()


class TestGuardrailsInTheLoop:
    async def test_a_regeneration_that_drops_an_id_is_rejected_and_rolled_back(
        self, package, tmp_path
    ):
        result = await run(
            package,
            tmp_path,
            [GOOD_CODE, CRITIQUE_FAIL, CODE_WITH_DROPPED_ID],
            [clean_observation(), clean_observation()],
            one_pass(max_attempts=2),
        )

        second = result.attempts[1]
        assert second.instrumentation_ok is False
        assert second.rolled_back is True
        # GUARDRAIL 1 in full: the file on disk is the one from before the bad fix.
        form = (tmp_path / "components/booking-form.tsx").read_text()
        assert 'data-scio-id="booking-submit"' in form
        assert result.status is PackageStatus.needs_look
        assert any("was lost in this regeneration" in r.what for r in result.remainders)

    async def test_benign_console_noise_does_not_fail_the_build(self, package, tmp_path):
        favicon_404 = ConsoleEntry(
            type="error",
            text="Failed to load resource: the server responded with a status of 404",
            url="http://127.0.0.1:3000/favicon.ico",
        )
        observation = observation_with([favicon_404])

        result = await run(
            package, tmp_path, [GOOD_CODE, CRITIQUE_PASS], [observation], one_pass()
        )

        assert observation.console.suppressed  # it WAS an error-level message
        assert result.status is PackageStatus.passed

    async def test_a_real_console_error_fails_the_build(self, package, tmp_path):
        api_500 = ConsoleEntry(
            type="error",
            text="Failed to load resource: the server responded with a status of 500",
            url="http://127.0.0.1:3000/api/bookings",
        )

        result = await run(
            package,
            tmp_path,
            [GOOD_CODE],
            [observation_with([api_500])],
            one_pass(max_attempts=1),
        )

        assert result.status is PackageStatus.needs_look
        assert result.attempts[0].console_ok is False
        assert any(r.source == "console" for r in result.remainders)
        # The critique is not even asked once the console says the app is broken.
        assert result.attempts[0].critique_passed is False


class TestFailureIsolation:
    async def test_cap_reached_reports_needs_a_look_rather_than_passing(
        self, package, tmp_path
    ):
        result = await run(
            package,
            tmp_path,
            [GOOD_CODE, CRITIQUE_FAIL, GOOD_CODE, CRITIQUE_FAIL],
            [clean_observation(), clean_observation()],
            one_pass(max_attempts=2),
        )

        assert result.status is PackageStatus.needs_look
        assert len(result.attempts) == 2  # capped, not retried forever
        assert result.files  # the code is there to look at
        assert "needs a look" in result.honest_status()
        assert any("no date field" in r.what for r in result.remainders)

    async def test_an_unparseable_critique_is_never_a_pass(self, package, tmp_path):
        result = await run(
            package,
            tmp_path,
            [GOOD_CODE, "Looks great to me!"],
            [clean_observation()],
            one_pass(max_attempts=1),
        )

        assert result.status is PackageStatus.needs_look
        assert any("could not be parsed" in r.what for r in result.remainders)

    async def test_a_reply_with_no_code_fails_honestly_without_crashing(
        self, package, tmp_path
    ):
        result = await run(
            package,
            tmp_path,
            ["I would start by considering the user's needs."],
            [clean_observation()],
            one_pass(max_attempts=1),
        )

        assert result.status is PackageStatus.failed
        assert result.files == []
        assert "failed" in result.honest_status()

    async def test_the_budget_stops_the_loop_instead_of_spending(self, package, tmp_path):
        result = await run(
            package,
            tmp_path,
            [GOOD_CODE, CRITIQUE_PASS],
            [clean_observation()],
            one_pass(max_attempts=2, budget_usd=0.0),
        )

        assert result.status is PackageStatus.failed
        assert any("budget" in r.what.lower() for r in result.remainders)


class CutOffProvider(ModelProvider):
    """A model that ran into max_tokens mid-file — the shape a real codegen
    reply takes when a package is bigger than the output budget."""

    vendor = Vendor.anthropic

    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, model, messages, **kwargs) -> Completion:
        self.calls += 1
        return Completion(
            text=GOOD_CODE[: len(GOOD_CODE) // 2],
            model=model,
            vendor=Vendor.anthropic,
            output_tokens=16000,
            stop_reason="max_tokens",
        )


class TestTruncatedReply:
    """Half a component on disk is worse than none: the loop must notice."""

    async def test_a_cut_off_reply_writes_nothing_and_says_why(self, package, tmp_path):
        provider = CutOffProvider()
        result = await build_package(
            package,
            "## Goal\nA guest can book a table.\n",
            tmp_path,
            registry=ProviderRegistry(providers={Vendor.anthropic: provider}),
            preview=ScriptedPreview([clean_observation()]),
            options=one_pass(max_attempts=2),
        )

        assert result.status is PackageStatus.failed
        assert result.files == []
        assert not list(tmp_path.glob("**/*.tsx"))
        assert any("cut off" in problem for a in result.attempts for problem in a.problems)
        assert provider.calls == 2  # it was retried, and told what went wrong


class TestExtraction:
    def test_files_outside_the_package_are_dropped_not_written(self, package):
        reply = GOOD_CODE + "\nFILE: ../../etc/passwd\n```\nroot:x:0:0\n```\n"
        extracted = extract_files(reply, allowed=planned_files(package))

        assert "../../etc/passwd" not in extracted.files
        assert extracted.ignored_paths == ["../../etc/passwd"]

    def test_a_reply_with_no_file_blocks_raises(self):
        with pytest.raises(CodeExtractionError):
            extract_files("Sure! Here's how I'd approach it.", allowed=["a.ts"])

    def test_the_planned_files_are_the_only_paths_the_model_may_use(self, package):
        assert set(extract_files(GOOD_CODE, allowed=planned_files(package)).files) == set(
            planned_files(package)
        )


def test_scripted_preview_is_deterministic(tmp_path: Path):
    preview = ScriptedPreview([clean_observation()])
    assert preview.observe(tmp_path, attempt=1).title == "Book a table"
    assert preview.observe(tmp_path, attempt=2).title == "Book a table"  # loops the last
