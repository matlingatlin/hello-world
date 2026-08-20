"""The interaction channel (B060b): "it works" as something a build passes or fails.

Until now the vision loop could say the page rendered. It could not say the
booking saved, so Layer C marked "works end to end and persists" unobservable
(B054) and nobody checked the one thing the user actually cares about.

Four claims carry this file, and the last one is the only one that matters:

1. Layer C derives the scripts deterministically, from the graph.
2. An interaction criterion goes to the script, not to the critique — and is not
   recorded as unverified either, which was B054's only way to describe it.
3. A failure feeds the repair loop and shows up in the honest status.
4. **Driven for real**, against a real browser and a real database: a correct
   booking feature passes, one whose insert silently fails does not, and the
   isolation criterion is the difference between a policy and no policy.

The live tests skip when the sandbox has no browser or no pglite — never pass
quietly. A green suite that never opened a page would be worse than a red one.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from conftest import scripted_codegen
from scio_engine.builder.critique import (
    interaction_criteria,
    judgeable_criteria,
    unjudged_criteria,
)
from scio_engine.builder.loop import BuildOptions, ScriptedPreview, build_package, file_chunks
from scio_engine.builder.result import PackageStatus
from scio_engine.core.interaction import (
    Action,
    Script,
    ScriptResult,
    StepResult,
    assert_present,
    assert_row,
    click,
    fill,
    reload,
    resolve,
    selector_for,
    selectors_for,
)
from scio_engine.core.interaction_runner import run_script
from scio_engine.core.preview import chromium_executable, playwright_available
from scio_engine.execution.provider import (
    Completion,
    ModelProvider,
    ProviderRegistry,
    Vendor,
)
from scio_engine.layerb.architecture import (
    Architecture,
    AuthAccess,
    AuthMode,
    Column,
    DataModel,
    FieldType,
    Operation,
    Screen,
    ScreensRouting,
    SecurityPosture,
    Table,
)
from scio_engine.layerc.criteria import Observability, interacting, judgeable, scoped_out
from scio_engine.layerc.decompose import build_plan
from scio_engine.layerc.scripts import ALICE, BOB, isolation_script, persistence_script
from scio_engine.library.verification import prepare
from test_verification_data import node_binary, node_with_pglite  # noqa: I001

ENGINE_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# The architecture the scripts are derived from
# --------------------------------------------------------------------------


def booking_architecture(*, with_accounts: bool = True) -> Architecture:
    """A booking app: guests create bookings and see their own."""
    return Architecture(
        data_model=DataModel(
            tables=[
                Table(
                    name="booking",
                    row_level_security=True,
                    columns=[
                        Column(name="id", type=FieldType.uuid),
                        Column(name="owner_id", type=FieldType.uuid, nullable=True),
                        Column(name="guest_name", type=FieldType.text),
                        Column(name="party_size", type=FieldType.integer),
                        Column(name="created_at", type=FieldType.timestamp),
                    ],
                )
            ]
        ),
        auth_access=AuthAccess(
            mode=AuthMode.email_link if with_accounts else AuthMode.none,
            provider="supabase-auth" if with_accounts else "",
            identifies_users=with_accounts,
            identity_fields=[] if with_accounts else ["name", "phone"],
        ),
        operations=[
            Operation(
                name="create_booking",
                verb="create",
                entity="booking",
                description="book a table",
                inputs=[
                    Column(name="guest_name", type=FieldType.text),
                    Column(name="party_size", type=FieldType.integer),
                ],
            ),
            Operation(
                name="list_booking",
                verb="list",
                entity="booking",
                description="see my bookings",
            ),
        ],
        screens_routing=ScreensRouting(
            screens=[
                Screen(name="Bookings", route="/booking", operations=["list_booking"]),
                Screen(name="New booking", route="/booking/new", operations=["create_booking"]),
            ]
        ),
        security_posture=SecurityPosture(row_level_security=True, sensitive=True),
    )


def booking_package(**kwargs):
    plan = build_plan(booking_architecture(**kwargs))
    return next(p for p in plan.packages if p.id == "pkg_feature_booking")


# --------------------------------------------------------------------------
# 1. Layer C derives the scripts, deterministically
# --------------------------------------------------------------------------


class TestTheScriptsAreDerived:
    def test_the_persistence_criterion_is_no_longer_scoped_out(self):
        """The reversal of B054: the criterion exists, and it is observable."""
        package = booking_package()

        persists = [c for c in package.acceptance_criteria if "persists" in c]
        interaction = [c for c in persists if c.observed_by is Observability.interaction]

        assert interaction, [c.text for c in persists]
        assert interaction[0].script is not None
        assert interaction[0].judged_by_interaction

    def test_it_fills_submits_reloads_and_looks_in_both_places(self):
        arch = booking_architecture()
        op = next(o for o in arch.operations if o.name == "create_booking")
        script = persistence_script(arch, "booking", op, arch.screens_routing.screens)

        actions = [step.action for step in script.steps]

        assert script.route == "/booking/new"
        assert Action.fill in actions
        assert actions.index(Action.click) < actions.index(Action.reload)
        # The reload comes BEFORE both assertions: that is the whole point.
        assert actions.index(Action.reload) < actions.index(Action.assert_present)
        assert Action.assert_row in actions

    def test_the_reload_is_the_list_route_not_the_form(self):
        """A form that still shows what you typed proves nothing."""
        arch = booking_architecture()
        op = next(o for o in arch.operations if o.name == "create_booking")
        script = persistence_script(arch, "booking", op, arch.screens_routing.screens)

        reload_step = next(s for s in script.steps if s.action is Action.reload)
        assert reload_step.target == "/booking"

    def test_it_types_only_into_fields_a_browser_can_type_into(self):
        """A generated id column or a <select> is left alone — a script that
        guesses at one fails a form that works."""
        arch = booking_architecture()
        op = next(o for o in arch.operations if o.name == "create_booking")
        script = persistence_script(arch, "booking", op, arch.screens_routing.screens)

        filled = [s.target for s in script.steps if s.action is Action.fill]
        assert filled == ["booking-form-guest-name", "booking-form-party-size"]
        assert not any("owner" in target or "-id" in target for target in filled)

    def test_every_fill_has_a_fallback_the_schema_fixes(self):
        """The id is the builder's to choose; the field's `name` is not."""
        arch = booking_architecture()
        op = next(o for o in arch.operations if o.name == "create_booking")
        script = persistence_script(arch, "booking", op, arch.screens_routing.screens)

        fills = [s for s in script.steps if s.action is Action.fill]
        assert all(s.fallback for s in fills)
        assert 'form [name="guest_name"]' in [s.fallback for s in fills]

    def test_an_operation_with_no_screen_to_drive_stays_unobserved(self):
        """Honest: a criterion nobody can run must not gate a build."""
        arch = booking_architecture()
        arch.screens_routing.screens = []
        op = next(o for o in arch.operations if o.name == "create_booking")

        assert persistence_script(arch, "booking", op, []) is None

        package = next(
            p for p in build_plan(arch).packages if p.id == "pkg_feature_booking"
        )
        persists = [c for c in package.acceptance_criteria if "persists" in c]
        assert all(c.observed_by is Observability.unsupported for c in persists)

    def test_the_isolation_script_gives_each_user_their_own_row(self):
        arch = booking_architecture()
        op = next(o for o in arch.operations if o.name == "create_booking")
        script = isolation_script(arch, "booking", op, arch.screens_routing.screens)

        actors = [s.value for s in script.steps if s.action is Action.as_user]
        assert actors == [ALICE, BOB]
        # Bob must see his OWN row as well as not Alice's — otherwise a list
        # that is broken for everybody would read as perfect isolation.
        assert [s.action for s in script.steps][-3:] == [
            Action.reload,
            Action.assert_present,
            Action.assert_absent,
        ]
        assert [s.text for s in script.steps if s.action is Action.assert_present] == [
            "{{marker_a}}",
            "{{marker_b}}",
        ]

    def test_an_app_with_no_identity_gets_no_isolation_criterion(self):
        """No accounts, no owner to isolate by. Claiming otherwise would fail
        every guest app for a policy it was right not to have."""
        arch = booking_architecture(with_accounts=False)
        op = next(o for o in arch.operations if o.name == "create_booking")

        assert isolation_script(arch, "booking", op, arch.screens_routing.screens) is None

    def test_a_table_with_no_owner_column_gets_no_isolation_criterion(self):
        arch = booking_architecture()
        table = arch.data_model.get("booking")
        table.columns = [c for c in table.columns if c.name != "owner_id"]
        op = next(o for o in arch.operations if o.name == "create_booking")

        assert isolation_script(arch, "booking", op, arch.screens_routing.screens) is None

    def test_derivation_is_stable_across_runs(self):
        """Two builds of the same app must produce the same script, or diffing
        one build against another becomes impossible."""
        arch = booking_architecture()
        op = next(o for o in arch.operations if o.name == "create_booking")

        first = persistence_script(arch, "booking", op, arch.screens_routing.screens)
        second = persistence_script(arch, "booking", op, arch.screens_routing.screens)

        assert first.model_dump() == second.model_dump()


# --------------------------------------------------------------------------
# 2. The channel routes the criterion to the right judge
# --------------------------------------------------------------------------


class TestTheChannelRouting:
    def test_the_critique_is_never_asked_about_persistence(self):
        """A model looking at a screenshot cannot tell whether the row reached
        Postgres. Asking manufactures the failure B054 exists to prevent."""
        package = booking_package()

        asked = [c.text for c in judgeable_criteria(package)]

        assert asked, "the render criteria must still reach the critique"
        assert not any("persists" in text for text in asked)

    def test_an_interaction_criterion_is_not_reported_as_unverified(self):
        """It IS verified — by driving the app. Listing it as scoped out would
        report 'nobody checked' about the one thing that was checked hardest."""
        package = booking_package()

        unjudged = unjudged_criteria(package)
        driven = [c.text for c in interaction_criteria(package)]

        assert driven
        assert not any(text in line for line in unjudged for text in driven)

    def test_it_is_the_scripts_that_get_run(self):
        package = booking_package()

        driven = interaction_criteria(package)

        assert len(driven) == 2  # persistence + isolation
        assert all(c.script is not None for c in driven)

    def test_a_package_that_renders_nothing_drives_nothing(self):
        """Same structural rule as the critique's: no markup, no interaction."""
        package = booking_package()
        criteria = package.acceptance_criteria

        assert interacting(criteria, ["supabase/migrations/0001_init.sql"]) == []
        assert judgeable(criteria, ["supabase/migrations/0001_init.sql"]) == []

    def test_an_interaction_criterion_still_needs_a_file_that_produces_it(self):
        package = booking_package()
        # A file plan with UI but nothing that could submit a form.
        thin = ["app/booking/page.tsx"]

        assert interacting(package.acceptance_criteria, thin) == []
        assert any("persists" in line for line in scoped_out(package.acceptance_criteria, thin))


class TestTheVocabulary:
    def test_a_loop_rendered_id_is_still_addressable(self):
        assert selector_for("booking-row-*") == '[data-scio-id^="booking-row-"]'
        assert selector_for("booking-form") == '[data-scio-id="booking-form"]'

    def test_the_id_is_tried_before_the_fallback(self):
        step = fill("booking-form-guest-name", "Ada", fallback='form [name="guest_name"]')

        assert selectors_for(step) == [
            '[data-scio-id="booking-form-guest-name"]',
            'form [name="guest_name"]',
        ]

    def test_markers_are_filled_in_per_run(self):
        script = Script(
            name="s",
            route="/booking/new",
            steps=[fill("f", "{{marker}}"), assert_present(text="{{marker}}")],
        )

        resolved = resolve(script, {"marker": "scio-1-abcd"})

        assert [s.value for s in resolved.steps] == ["scio-1-abcd", ""]
        assert resolved.steps[1].text == "scio-1-abcd"
        assert script.steps[0].value == "{{marker}}", "the original is not mutated"

    def test_a_failure_reads_as_something_to_fix(self):
        result = ScriptResult(
            name="create_booking persists",
            passed=False,
            steps=[
                StepResult(step=fill("booking-form-guest-name", "Ada"), ok=True),
                StepResult(
                    step=click("booking-form-submit"),
                    ok=False,
                    detail="Timeout: waiting for selector",
                ),
            ],
        )

        assert result.failure == (
            "create_booking persists: could not click booking-form-submit "
            "— Timeout: waiting for selector"
        )


# --------------------------------------------------------------------------
# 3. The loop treats it as evidence: gate, repair, honest status
# --------------------------------------------------------------------------

FEATURE_CODE = """FILE: app/actions/booking.ts
```ts
// create_booking
export async function createBookingAction() {}
```

FILE: components/booking-form.tsx
```tsx
export function BookingForm() {
  return <form data-scio-id="booking-form"><button data-scio-id="booking-form-submit" /></form>;
}
```

FILE: components/booking-list.tsx
```tsx
export function BookingList() {
  return <ul data-scio-id="booking-list" />;
}
```

FILE: lib/db/booking.ts
```ts
// list_booking
export async function listBooking() { return []; }
```

FILE: lib/validation/booking.ts
```ts
export const bookingSchema = {};
```

FILE: tests/booking.test.ts
```ts
it("creates a booking", () => {});
it("rejects invalid input", () => {});
```

FILE: app/booking/page.tsx
```tsx
export default function Page() { return <main data-scio-id="booking-page" />; }
```

FILE: app/booking/new/page.tsx
```tsx
export default function Page() { return <main data-scio-id="booking-new-page" />; }
```
"""

PASSING_CRITIQUE = '{"verdict": "pass", "criteria": [], "problems": []}'


def one_attempt_options(max_attempts: int) -> BuildOptions:
    """One relay pass per step, so the scripted replies map 1:1 onto calls."""
    return BuildOptions(
        max_attempts=max_attempts, codegen_passes=1, critique_passes=1, persist=False
    )


def registry_for(replies: list[str], package=None):
    """A fake provider that answers codegen and critique in order.

    When a package is given, every codegen reply is padded to the package's full
    file plan (B076): these tests are about the interaction channel, not about
    completeness, and a fixture that wrote five of eight files is now correctly
    told it is missing three.
    """
    if package is not None:
        replies = scripted_codegen(package, replies)
    return ProviderRegistry.scripted(replies)


class CountingProvider(ModelProvider):
    """Answers, and remembers how often it was asked."""

    vendor = Vendor.anthropic

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls = 0

    async def complete(self, model, messages, **kwargs) -> Completion:
        self.calls += 1
        text = self.replies[min(self.calls - 1, len(self.replies) - 1)]
        return Completion(text=text, model=model, vendor=Vendor.anthropic, output_tokens=1)


def clean_observation():
    from scio_engine.core.console import classify_console
    from scio_engine.core.preview import Observation

    return Observation(screenshot_path=None, console=classify_console([]), title="Bookings")


def passed(script: Script) -> ScriptResult:
    return ScriptResult(name=script.name, passed=True)


def failed(name: str, detail: str) -> ScriptResult:
    return ScriptResult(
        name=name,
        passed=False,
        steps=[StepResult(step=reload("/booking"), ok=True),
               StepResult(step=assert_present(text="scio-1"), ok=False, detail=detail)],
    )


class TestTheLoopUsesIt:
    async def test_a_preview_that_cannot_drive_reports_it_rather_than_passing(
        self, tmp_path
    ):
        """The default path, unchanged: no data layer, no verdict invented."""
        package = booking_package()
        preview = ScriptedPreview([clean_observation()])  # no interactions at all

        result = await build_package(
            package,
            "contract",
            tmp_path,
            registry=registry_for([FEATURE_CODE, PASSING_CRITIQUE], package),
            preview=preview,
            options=one_attempt_options(1),
        )

        assert result.status is PackageStatus.passed
        assert preview.driven == [], "nothing should have been driven"
        not_verified = [r.what for r in result.remainders]
        assert any("nobody drove it" in line for line in not_verified), not_verified

    async def test_a_failing_script_fails_the_package_and_says_why(self, tmp_path):
        package = booking_package()
        preview = ScriptedPreview(
            [clean_observation()],
            interactions=[
                failed(
                    "create_booking persists",
                    "no row in booking matching {'guest_name': 'scio-1-abcd'} — it was not saved",
                )
            ],
        )

        result = await build_package(
            package,
            "contract",
            tmp_path,
            registry=registry_for([FEATURE_CODE, FEATURE_CODE], package),
            preview=preview,
            options=one_attempt_options(1),
        )

        assert result.status is PackageStatus.needs_look
        assert "it was not saved" in result.honest_status()
        assert {r.source for r in result.remainders} == {"interaction"}

    async def test_the_failure_is_fed_back_into_the_repair_loop(self, tmp_path):
        """The point of a gate: the next attempt is told what went wrong."""
        package = booking_package()
        preview = ScriptedPreview(
            [clean_observation()],
            interactions=[
                failed("create_booking persists", "it was not saved"),
                passed(Script(name="create_booking persists")),
                passed(Script(name="isolation")),
            ],
        )
        registry = registry_for([FEATURE_CODE, FEATURE_CODE, PASSING_CRITIQUE], package)

        result = await build_package(
            package,
            "contract",
            tmp_path,
            registry=registry,
            preview=preview,
            options=one_attempt_options(2),
        )

        repair = result.attempts[1]
        assert repair.action == "fix"
        assert result.status is PackageStatus.passed
        assert any("[interaction]" in p for p in result.attempts[0].problems)

    async def test_the_critique_is_not_paid_for_when_the_app_does_not_work(
        self, tmp_path
    ):
        """A relay costs money to tell us what a browser already proved."""
        package = booking_package()
        provider = CountingProvider(scripted_codegen(package, [FEATURE_CODE]))
        preview = ScriptedPreview(
            [clean_observation()],
            interactions=[failed("create_booking persists", "it was not saved")],
        )

        await build_package(
            package,
            "contract",
            tmp_path,
            registry=ProviderRegistry(providers={Vendor.anthropic: provider}),
            preview=preview,
            options=one_attempt_options(1),
        )

        # The codegen calls and nothing more: the critique was never asked.
        # A package this size is generated in bounded chunks (B076), so "the
        # codegen" is one call per chunk — what matters is that no relay was
        # spent on a verdict the browser had already given.
        assert provider.calls == len(file_chunks(package))

    async def test_every_derived_script_is_run(self, tmp_path):
        package = booking_package()
        preview = ScriptedPreview(
            [clean_observation()],
            interactions=[passed(Script(name="a")), passed(Script(name="b"))],
        )

        await build_package(
            package,
            "contract",
            tmp_path,
            registry=registry_for([FEATURE_CODE, PASSING_CRITIQUE], package),
            preview=preview,
            options=one_attempt_options(1),
        )

        assert len(preview.driven) == 2
        # Resolved, not templated: a run must not type "{{marker}}" into a form.
        assert all("{{" not in step.value for script in preview.driven for step in script.steps)

    async def test_two_attempts_never_share_a_marker(self, tmp_path):
        """The database survives a repair. A reused marker would let attempt 2
        pass on the row attempt 1 left behind."""
        package = booking_package()
        preview = ScriptedPreview(
            [clean_observation()],
            interactions=[failed("create_booking persists", "not saved")],
        )

        await build_package(
            package,
            "contract",
            tmp_path,
            registry=registry_for([FEATURE_CODE, FEATURE_CODE], package),
            preview=preview,
            options=one_attempt_options(2),
        )

        markers = {
            step.value
            for script in preview.driven
            for step in script.steps
            if step.action is Action.fill and step.value.startswith("scio-")
        }
        assert len(markers) >= 2, markers


# --------------------------------------------------------------------------
# 4. Driven for real: a browser, an app, and a database
# --------------------------------------------------------------------------

CORRECT_SCHEMA = """
create table bookings (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid,
  guest_name text not null,
  party_size integer not null,
  created_at timestamptz not null default now()
);

alter table bookings enable row level security;

create policy bookings_own on bookings for select using (owner_id = auth.uid());
create policy bookings_insert on bookings for insert with check (true);
"""

SCHEMA_WITHOUT_ISOLATION = CORRECT_SCHEMA.replace(
    "using (owner_id = auth.uid())", "using (true)"
)
"""RLS is ON and there is a policy — it just does not isolate anybody. The
failure mode that looks correct in a code review."""

APP_SERVER = r"""
import http from "node:http";
import { getSupabaseClient } from "./.scio/verification/client.ts";
import { answer } from "./.scio/verification/verify.ts";

/** The one difference between the two apps under test. */
const BROKEN = process.env.APP_BROKEN_INSERT === "1";

const client = getSupabaseClient();

function esc(value) {
  return String(value ?? "").replace(
    /[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
  );
}

/**
 * The form ids follow the seed catalog, NOT the derived convention:
 * `booking-form-name` for the `guest_name` column. That is deliberate — a
 * correct app must not fail because the builder named the id its own way.
 */
const FORM_PAGE = `<!doctype html><html><body data-scio-id="app-shell">
  <form data-scio-id="booking-form" method="post" action="/booking/new">
    <input data-scio-id="booking-form-name" name="guest_name" />
    <input data-scio-id="booking-form-party-size" name="party_size" type="number" value="2" />
    <button data-scio-id="booking-form-submit" type="submit">Book a table</button>
  </form>
</body></html>`;

async function listPage() {
  const { data, error } = await client.from("bookings").select("*");
  if (error) {
    return `<!doctype html><body data-scio-id="booking-error">${esc(error.message)}</body>`;
  }
  const rows = (data ?? [])
    .map((r) =>
      `<li data-scio-id="booking-row-${r.id}">${esc(r.guest_name)} — ${esc(r.party_size)}</li>`)
    .join("");
  return `<!doctype html><html><body data-scio-id="app-shell">
    <ul data-scio-id="booking-list">${rows}</ul>
  </body></html>`;
}

async function create(body) {
  const form = new URLSearchParams(body);
  if (BROKEN) return;  // the insert that silently does nothing
  const { data: { user } } = await client.auth.getUser();
  await client.from("bookings").insert({
    owner_id: user?.id ?? null,
    guest_name: form.get("guest_name"),
    party_size: Number(form.get("party_size") ?? 2),
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  try {
    if (url.pathname === "/api/__scio_verify") {
      const payload = await answer(url.searchParams);
      res.writeHead(200, { "content-type": "application/json" });
      return res.end(JSON.stringify(payload));
    }
    if (req.method === "POST" && url.pathname === "/booking/new") {
      let body = "";
      for await (const chunk of req) body += chunk;
      await create(body);
      res.writeHead(303, { location: "/booking" });
      return res.end();
    }
    if (url.pathname === "/booking/new") {
      res.writeHead(200, { "content-type": "text/html" });
      return res.end(FORM_PAGE);
    }
    if (url.pathname === "/booking" || url.pathname === "/") {
      res.writeHead(200, { "content-type": "text/html" });
      return res.end(await listPage());
    }
    res.writeHead(404).end("not found");
  } catch (error) {
    res.writeHead(500, { "content-type": "text/html" });
    res.end(`<body data-scio-id="crash">${esc(error.message)}</body>`);
  }
});

server.listen(Number(process.env.APP_PORT), "127.0.0.1", () => {
  console.log(`READY ${server.address().port}`);
});
"""


needs_a_browser = pytest.mark.skipif(
    not playwright_available() or node_with_pglite() is None,
    reason="a browser and node with @electric-sql/pglite are both needed here",
)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class RunningApp:
    """A generated app, running, with a real database behind it."""

    def __init__(self, tmp_path: Path, schema: str, *, broken: bool = False) -> None:
        (tmp_path / "supabase" / "migrations").mkdir(parents=True)
        (tmp_path / "supabase" / "migrations" / "0001_init.sql").write_text(schema)
        (tmp_path / "lib").mkdir(exist_ok=True)
        (tmp_path / "lib" / "supabase.ts").write_text(
            'import { createClient } from "@supabase/supabase-js";\n'
        )
        self.app = tmp_path
        self.database = prepare(tmp_path)
        # ESM ignores NODE_PATH and resolves by walking up from the importing
        # file, so the modules have to be reachable from the app itself.
        link = tmp_path / "node_modules"
        if not link.exists():
            link.symlink_to(node_with_pglite(), target_is_directory=True)
        (tmp_path / "server.mjs").write_text(APP_SERVER)

        self.port = free_port()
        self.process = subprocess.Popen(
            [node_binary(), str(tmp_path / "server.mjs")],
            cwd=tmp_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={
                "PATH": "/usr/bin:/bin",
                "APP_PORT": str(self.port),
                "APP_BROKEN_INSERT": "1" if broken else "0",
                **self.database.env,
            },
        )
        self._await_ready()

    def _await_ready(self) -> None:
        deadline = time.time() + 120
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(f"the app died:\n{self.process.stdout.read()}")
            try:
                # The first request boots pglite and applies the migration.
                with urllib.request.urlopen(f"{self.url}/booking", timeout=90):
                    return
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        raise AssertionError("the app never came up")

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def verify_url(self) -> str:
        return self.url + self.database.verify_path

    def rows(self) -> int:
        """What is really in the database, whoever is asking."""
        with urllib.request.urlopen(f"{self.verify_url}?table=booking") as response:
            return json.loads(response.read()).get("count", -1)

    def drive(self, script: Script, markers: dict[str, str]) -> ScriptResult:
        return run_script(
            self.url,
            resolve(script, markers),
            verify_url=self.verify_url,
            browser_path=chromium_executable() or "",
        )

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:  # pragma: no cover
            self.process.kill()
        self.database.discard()


@pytest.fixture
def running(tmp_path):
    """Builds the app the test asks for, and always takes it down again."""
    apps: list[RunningApp] = []

    def build(schema: str = CORRECT_SCHEMA, *, broken: bool = False) -> RunningApp:
        target = tmp_path / f"app{len(apps)}"
        target.mkdir()
        app = RunningApp(target, schema, broken=broken)
        apps.append(app)
        return app

    yield build

    for app in apps:
        app.stop()
    # ~39MB per database; the sandbox notices.
    shutil.rmtree(tmp_path, ignore_errors=True)


MARKERS = {"marker": "Ada-7f3a", "marker_a": "Ada-7f3a", "marker_b": "Grace-91c2"}


def the_persistence_script() -> Script:
    arch = booking_architecture()
    op = next(o for o in arch.operations if o.name == "create_booking")
    return persistence_script(arch, "booking", op, arch.screens_routing.screens)


def the_isolation_script() -> Script:
    arch = booking_architecture()
    op = next(o for o in arch.operations if o.name == "create_booking")
    return isolation_script(arch, "booking", op, arch.screens_routing.screens)


@needs_a_browser
class TestDrivenForReal:
    def test_a_correct_feature_passes_the_persistence_criterion(self, running):
        app = running()

        result = app.drive(the_persistence_script(), MARKERS)

        assert result.passed, result.failure
        assert app.rows() == 1, "and the row is really in Postgres"

    def test_an_insert_that_silently_does_nothing_fails_it(self, running):
        """The failure this whole channel exists to catch: the page looks fine,
        the form submits, and nothing was saved."""
        app = running(broken=True)

        result = app.drive(the_persistence_script(), MARKERS)

        assert not result.passed
        assert app.rows() == 0
        # And it says something a repair prompt can act on.
        assert "Ada-7f3a" in result.failure or "not saved" in result.failure

    def test_it_drives_by_scio_id_and_falls_back_only_when_it_must(self, running):
        """`booking-form-name` is the app's id for the `guest_name` column; the
        derived script asks for `booking-form-guest-name` and still fills it."""
        app = running()

        result = app.drive(the_persistence_script(), MARKERS)

        submitted = next(
            s for s in result.steps if s.step.action is Action.click
        )
        assert submitted.ok, "the submit button IS addressed by its scio id"
        assert result.passed, result.failure

    def test_a_guest_cannot_read_another_guests_booking(self, running):
        """The second criterion B054 had to scope out — now a gate."""
        app = running()

        result = app.drive(the_isolation_script(), MARKERS)

        assert result.passed, result.failure
        assert app.rows() == 2, "both bookings were made; only the reading differs"

    def test_without_an_isolating_policy_it_fails(self, running):
        """RLS is enabled and a policy exists; it just lets everyone read
        everything. A code review passes this. The script does not."""
        app = running(SCHEMA_WITHOUT_ISOLATION)

        result = app.drive(the_isolation_script(), MARKERS)

        assert not result.passed
        assert "Ada-7f3a" in result.failure, result.failure

    def test_the_database_is_asked_about_the_entity_not_the_relation(self, running):
        """The architecture says `booking`; the migration wrote `bookings`."""
        app = running()

        with urllib.request.urlopen(f"{app.verify_url}?table=booking") as response:
            singular = json.loads(response.read())
        with urllib.request.urlopen(f"{app.verify_url}?table=bookings") as response:
            plural = json.loads(response.read())

        assert singular == plural == {"count": 0}

    def test_an_unknown_table_is_an_error_not_an_empty_count(self, running):
        """A count of zero would read as 'it was not saved' and send the repair
        loop after code that is fine."""
        app = running()

        with urllib.request.urlopen(f"{app.verify_url}?table=nowhere") as response:
            payload = json.loads(response.read())

        assert "no table for 'nowhere'" in payload.get("error", "")


@needs_a_browser
class TestTheRunnerIsHonest:
    def test_a_missing_element_is_a_finding_not_a_crash(self, running):
        app = running()
        script = Script(
            name="a button that is not there",
            route="/booking/new",
            steps=[click("booking-form-nonexistent")],
        )

        result = run_script(app.url, script, browser_path=chromium_executable() or "")

        assert not result.passed
        assert "booking-form-nonexistent" in result.failure

    def test_asserting_a_row_without_a_data_layer_says_so(self, running):
        app = running()
        script = Script(
            name="no verify endpoint",
            route="/booking",
            steps=[assert_row("booking", {})],
        )

        result = run_script(app.url, script, browser_path=chromium_executable() or "")

        assert not result.passed
        assert "not running with data" in result.failure


def test_the_engine_still_imports_without_playwright():
    """The channel is an optional extra, like the rest of the preview."""
    source = (ENGINE_ROOT / "src/scio_engine/core/interaction_runner.py").read_text()

    assert "from playwright.sync_api import sync_playwright" in source
    assert source.index("def run_script") < source.index("import sync_playwright")


def test_the_runner_is_never_called_from_the_event_loop():
    """Sync Playwright refuses to run inside one — a lesson already learned."""
    loop_source = (ENGINE_ROOT / "src/scio_engine/builder/loop.py").read_text()
    driving = loop_source[loop_source.index("async def _drive") :]

    assert "asyncio.to_thread(" in driving
    assert driving.index("asyncio.to_thread(") < driving.index("preview.interact")
