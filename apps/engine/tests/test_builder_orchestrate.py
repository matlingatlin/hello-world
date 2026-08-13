"""Full build-plan orchestration (B041b) — packages assembled into ONE app.

What matters here is not that the loop runs several times. It is that the app is
assembled: later packages are generated into the workspace the earlier ones are
already standing in, the guardrails hold across package boundaries, and a part
that cannot be finished takes down only what actually depends on it.
"""

from pathlib import Path

import pytest

from scio_engine.builder.loop import BuildOptions, ScriptedPreview
from scio_engine.builder.orchestrate import (
    ASSEMBLY_HEADER,
    AppBuildOptions,
    BuildProgress,
    run_build_plan,
    stream_build_plan,
)
from scio_engine.builder.result import PackageStatus
from scio_engine.core.console import classify_console
from scio_engine.core.instrumentation import Manifest
from scio_engine.core.preview import Observation
from scio_engine.execution.provider import ProviderRegistry, Vendor
from scio_engine.layerc.decompose import topological_order
from scio_engine.layerc.plan import (
    BuildPackage,
    BuildPlan,
    NodeRef,
    PackageInterface,
    PackageKind,
)

FOUNDATION = "pkg_foundation"
SCHEMA = "pkg_schema"
TOKENS = "pkg_design_tokens"
BOOKING = "pkg_feature_booking"
MENU = "pkg_feature_menu"


# --- the plan -----------------------------------------------------------------


def make_plan() -> BuildPlan:
    """A small but real shape: a shell, a schema, tokens, and two features that
    depend on the schema but not on each other."""
    packages = [
        BuildPackage(
            id=FOUNDATION,
            kind=PackageKind.foundation,
            goal="Scaffold the app shell and the home screen.",
            architecture_slice=[
                NodeRef(kind="security", name="security_posture"),
                NodeRef(kind="screen", name="/"),
            ],
            interface=PackageInterface(routes=["/"], exports=["app shell", "supabase client"]),
            acceptance_criteria=["The shell renders and navigation reaches the home screen."],
        ),
        BuildPackage(
            id=SCHEMA,
            kind=PackageKind.schema,
            goal="Create the bookings and dishes tables with row-level security.",
            architecture_slice=[
                NodeRef(kind="table", name="bookings"),
                NodeRef(kind="table", name="dishes"),
            ],
            dependencies=[FOUNDATION],
            interface=PackageInterface(tables=["bookings", "dishes"]),
            acceptance_criteria=["Every table exists with row-level security enabled."],
        ),
        BuildPackage(
            id=TOKENS,
            kind=PackageKind.design_tokens,
            goal="Encode the design tokens as CSS variables and a Tailwind theme.",
            architecture_slice=[NodeRef(kind="tokens", name="design_tokens")],
            dependencies=[FOUNDATION],
            acceptance_criteria=["Tokens are defined once and consumed by Tailwind."],
        ),
        BuildPackage(
            id=BOOKING,
            kind=PackageKind.feature,
            goal="Build the booking feature.",
            architecture_slice=[
                NodeRef(kind="operation", name="create_booking"),
                NodeRef(kind="screen", name="/booking"),
            ],
            dependencies=[FOUNDATION, SCHEMA, TOKENS],
            interface=PackageInterface(operations=["create_booking"], routes=["/booking"]),
            acceptance_criteria=["A guest can book a table in a few taps."],
        ),
        BuildPackage(
            id=MENU,
            kind=PackageKind.feature,
            goal="Build the menu feature.",
            architecture_slice=[
                NodeRef(kind="operation", name="list_menu"),
                NodeRef(kind="screen", name="/menu"),
            ],
            dependencies=[FOUNDATION, SCHEMA, TOKENS],
            interface=PackageInterface(operations=["list_menu"], routes=["/menu"]),
            acceptance_criteria=["A guest can read the menu."],
        ),
    ]
    return BuildPlan(
        packages=packages,
        order=topological_order(packages),
        graph={p.id: list(p.dependencies) for p in packages},
    )


CONTRACTS = {
    FOUNDATION: "# Build package: pkg_foundation\nScaffold the shell.",
    SCHEMA: "# Build package: pkg_schema\nCreate the tables.",
    TOKENS: "# Build package: pkg_design_tokens\nEncode the tokens.",
    BOOKING: "# Build package: pkg_feature_booking\nBuild booking.",
    MENU: "# Build package: pkg_feature_menu\nBuild menu.",
}


# --- what the "model" returns, per package ------------------------------------

FOUNDATION_CODE = """FILE: app/layout.tsx
```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body data-scio-id="app-shell" data-scio-package="pkg_foundation">
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
```

FILE: components/site-header.tsx
```tsx
export function SiteHeader() {
  return (
    <header data-scio-id="site-header" data-scio-package="pkg_foundation">
      <a data-scio-id="nav-home" data-scio-package="pkg_foundation" href="/">Bistro Nord</a>
    </header>
  );
}
```

FILE: lib/supabase.ts
```ts
export const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);
```

FILE: app/page.tsx
```tsx
export default function HomePage() {
  return (
    <main data-scio-id="home-main" data-scio-package="pkg_foundation">
      Welcome to Bistro Nord
    </main>
  );
}
```
"""

SCHEMA_CODE = """FILE: supabase/migrations/0001_init.sql
```sql
create table bookings (id uuid primary key, guest_name text not null);
create table dishes (id uuid primary key, title text not null);
alter table bookings enable row level security;
alter table dishes enable row level security;
```

FILE: types/database.ts
```ts
export type Booking = { id: string; guest_name: string };
export type Dish = { id: string; title: string };
```
"""

TOKENS_CODE = """FILE: app/globals.css
```css
:root { --ink: #101319; --paper: #ffffff; }
```

FILE: tailwind.config.ts
```ts
export default { theme: { colors: { ink: "var(--ink)", paper: "var(--paper)" } } };
```
"""


def feature_code(entity: str, route: str, operation: str, *, form_id: str = "") -> str:
    """The five files a feature package owns, instrumented per the contract."""
    package = f"pkg_feature_{entity}"
    form = form_id or f"{entity}-form"
    return f"""FILE: app{route}/page.tsx
```tsx
export default function {entity.title()}Page() {{
  return (
    <main data-scio-id="{entity}-page" data-scio-package="{package}">
      <{entity.title()}Form />
    </main>
  );
}}
```

FILE: components/{entity}-form.tsx
```tsx
export function {entity.title()}Form() {{
  return (
    <form data-scio-id="{form}" data-scio-package="{package}">
      <button data-scio-id="{entity}-submit" data-scio-package="{package}">Go</button>
    </form>
  );
}}
```

FILE: components/{entity}-list.tsx
```tsx
export function {entity.title()}List({{ rows }}) {{
  return (
    <ul data-scio-id="{entity}-list" data-scio-package="{package}">
      {{rows.map((row) => (
        <li
          key={{row.id}}
          data-scio-id={{`{entity}-row-${{row.id}}`}}
          data-scio-package="{package}"
        >
          {{row.name}}
        </li>
      ))}}
    </ul>
  );
}}
```

FILE: lib/db/{entity}.ts
```ts
import {{ supabase }} from "../supabase";

export async function {operation}(input) {{
  return await supabase.from("{entity}s").insert(input);
}}
```

FILE: tests/{entity}.test.ts
```ts
test("{operation} works", async () => {{
  expect(await {operation}({{}})).toBeTruthy();
}});
```
"""


BOOKING_CODE = feature_code("booking", "/booking", "create_booking")
MENU_CODE = feature_code("menu", "/menu", "list_menu")
# The same menu package, but reusing the booking form's id — an app-wide collision.
MENU_CODE_STEALING_AN_ID = feature_code("menu", "/menu", "list_menu", form_id="booking-form")

SCHEMA_BROKEN = """FILE: supabase/migrations/0001_init.sql
```sql
create table bookings (id uuid primary key, guest_name text not null);
```

FILE: types/database.ts
```ts
```
"""
"""A schema package that fails deterministically — an empty types file.

It used to fail its critique instead. It cannot any more, and that is the point
of B054: a package that renders nothing is never asked to prove itself from a
screenshot. Failure isolation is still real, it just arrives through the channel
that applies — the validation agents.
"""

PASS = '{"verdict": "pass", "criteria": [], "problems": []}'
FAIL = (
    '{"verdict": "fail", "criteria": [], '
    '"problems": ["Row-level security is not enabled on dishes."]}'
)


# --- harness ------------------------------------------------------------------


class CountingPreview(ScriptedPreview):
    """A scripted preview that remembers how it was used — the assembly claim is
    'one app, one sandbox', and that has to be checkable."""

    def __init__(self, observations, **kwargs):
        super().__init__(observations, **kwargs)
        self.applied_dirs: list[Path] = []
        self.observed_dirs: list[Path] = []
        self.closes = 0

    def apply(self, app_dir: Path, files: dict[str, str]) -> None:
        self.applied_dirs.append(app_dir)
        super().apply(app_dir, files)

    def observe(self, app_dir: Path, *, attempt: int) -> Observation:
        self.observed_dirs.append(app_dir)
        return super().observe(app_dir, attempt=attempt)

    def close(self) -> None:
        self.closes += 1

    @property
    def url(self) -> str:
        return "http://127.0.0.1:4321"


def clean() -> Observation:
    return Observation(screenshot_path=None, console=classify_console([]), title="Bistro Nord")


def options(**overrides) -> AppBuildOptions:
    package = BuildOptions(max_attempts=2, codegen_passes=1, critique_passes=1)
    return AppBuildOptions(package=package, **overrides)


async def run(app_dir, replies, *, plan=None, preview=None, opts=None):
    plan = plan or make_plan()
    preview = preview or CountingPreview([clean()])
    registry = ProviderRegistry.scripted(replies, loop_last=False)
    result = await run_build_plan(
        plan,
        app_dir,
        contracts=CONTRACTS,
        registry=registry,
        preview=preview,
        options=opts or options(),
    )
    return result, preview, registry


ALL_GOOD = [
    FOUNDATION_CODE, PASS,
    TOKENS_CODE, PASS,
    SCHEMA_CODE, PASS,
    BOOKING_CODE, PASS,
    MENU_CODE, PASS,
]
"""Order matters: it is the plan's topological order, and a mismatch makes the
scripted provider hand the wrong code to the wrong package — which is exactly
the failure a wrong build order would cause in production."""


class TestDependencyOrder:
    def test_the_plan_orders_foundation_before_everything_that_needs_it(self):
        order = make_plan().order
        assert order[0] == FOUNDATION
        assert order.index(SCHEMA) < order.index(BOOKING)
        assert order.index(TOKENS) < order.index(BOOKING)

    async def test_packages_are_built_in_that_order(self, tmp_path):
        result, _, _ = await run(tmp_path, ALL_GOOD)

        assert [p.package_id for p in result.packages] == make_plan().order


class TestIncrementalAssembly:
    async def test_every_package_lands_in_one_app(self, tmp_path):
        result, _, _ = await run(tmp_path, ALL_GOOD)

        assert result.works
        # One workspace holding all five packages' files.
        for relative in ("app/layout.tsx", "types/database.ts", "app/globals.css",
                         "components/booking-form.tsx", "components/menu-form.tsx"):
            assert (tmp_path / relative).exists(), relative

    async def test_the_manifest_is_app_wide(self, tmp_path):
        result, _, _ = await run(tmp_path, ALL_GOOD)

        manifest = Manifest.load(tmp_path / "scio-manifest.json")
        assert manifest.elements["site-header"].package == FOUNDATION
        assert manifest.elements["booking-form"].package == BOOKING
        assert manifest.elements["menu-form"].package == MENU
        assert set(manifest.packages) >= {FOUNDATION, SCHEMA, TOKENS, BOOKING, MENU}
        assert result.element_count == len(manifest.elements)

    async def test_a_later_package_is_told_what_is_already_standing(self, tmp_path):
        _, _, registry = await run(tmp_path, ALL_GOOD)

        provider = registry.get(Vendor.anthropic)
        # Call 7 is the booking package's codegen (2 calls per package, in order).
        booking_prompt = "\n".join(m.content for m in provider.calls[6][1])
        assert ASSEMBLY_HEADER in booking_prompt
        assert "components/site-header.tsx" in booking_prompt
        assert "ids already taken: app-shell, home-main, nav-home, site-header" in booking_prompt

    async def test_the_first_package_has_nothing_to_integrate_with(self, tmp_path):
        _, _, registry = await run(tmp_path, ALL_GOOD)

        foundation_prompt = "\n".join(
            m.content for m in registry.get(Vendor.anthropic).calls[0][1]
        )
        assert ASSEMBLY_HEADER not in foundation_prompt

    async def test_one_sandbox_serves_the_whole_app(self, tmp_path):
        _, preview, _ = await run(tmp_path, ALL_GOOD)

        assert {d for d in preview.observed_dirs} == {tmp_path.resolve()}
        assert preview.calls == 5  # one look per package, at the whole app
        assert preview.closes == 1  # torn down once, at the end — not per package

    async def test_the_assembled_app_is_persisted_as_one_version(self, tmp_path):
        result, _, _ = await run(tmp_path, ALL_GOOD)

        assert result.git_sha
        assert result.build_version == 1
        assert result.app_url == "http://127.0.0.1:4321"
        assert (tmp_path / "scio-manifest.json").exists()


class TestCrossPackageGuardrails:
    async def test_a_package_reusing_an_earlier_packages_id_is_rejected(self, tmp_path):
        replies = [
            FOUNDATION_CODE, PASS,
            TOKENS_CODE, PASS,
            SCHEMA_CODE, PASS,
            BOOKING_CODE, PASS,
            # Both attempts collide, and neither reaches the critique: the
            # instrumentation guardrail rejects them first.
            MENU_CODE_STEALING_AN_ID,
            MENU_CODE_STEALING_AN_ID,
        ]
        result, _, _ = await run(tmp_path, replies)

        menu = result.get(MENU)
        # Every attempt was rolled back, so the package contributed nothing at
        # all — "failed", not "needs a look at what it left behind".
        assert menu.status is PackageStatus.failed
        assert menu.files == []
        assert all(a.instrumentation_ok is False and a.rolled_back for a in menu.attempts)
        assert any("appears 2 times" in r.what for r in menu.remainders)
        # The booking package it collided with is untouched.
        assert result.get(BOOKING).status is PackageStatus.passed
        assert 'data-scio-id="booking-form"' in (
            tmp_path / "components/booking-form.tsx"
        ).read_text()


class TestFailureIsolation:
    async def test_a_failing_package_blocks_its_dependents_but_not_its_siblings(
        self, tmp_path
    ):
        replies = [
            FOUNDATION_CODE, PASS,
            TOKENS_CODE, PASS,
            SCHEMA_BROKEN, SCHEMA_BROKEN,  # schema never passes its validation
        ]
        result, _, _ = await run(tmp_path, replies)

        assert result.get(SCHEMA).status is PackageStatus.needs_look
        assert result.get(FOUNDATION).status is PackageStatus.passed
        assert result.get(TOKENS).status is PackageStatus.passed  # independent, still built
        for feature in (BOOKING, MENU):
            blocked = result.get(feature)
            assert blocked.status is PackageStatus.blocked
            assert SCHEMA in blocked.remainders[0].what
            assert blocked.files == []  # nothing was built on top of a broken dependency

    async def test_the_aggregate_status_is_honest(self, tmp_path):
        replies = [
            FOUNDATION_CODE, PASS,
            TOKENS_CODE, PASS,
            SCHEMA_BROKEN, SCHEMA_BROKEN,
        ]
        result, _, _ = await run(tmp_path, replies)

        assert result.works is False
        assert result.working == [FOUNDATION, TOKENS]
        assert result.needs_look == [SCHEMA]
        assert sorted(result.blocked) == sorted([BOOKING, MENU])

        summary = result.honest_summary()
        assert summary.startswith("2 of 5 parts work.")
        assert "1 need a look" in summary
        assert "2 not built (a dependency is broken)" in summary

    async def test_the_working_parts_are_still_persisted(self, tmp_path):
        replies = [
            FOUNDATION_CODE, PASS,
            TOKENS_CODE, PASS,
            SCHEMA_BROKEN, SCHEMA_BROKEN,
        ]
        result, _, _ = await run(tmp_path, replies)

        # The user is shown this build, so the user must be able to return to it.
        assert result.git_sha
        manifest = Manifest.load(tmp_path / "scio-manifest.json")
        assert "site-header" in manifest.elements

    async def test_blocking_is_transitive(self, tmp_path):
        plan = make_plan()
        # A reporting package that depends on the booking feature, which will be
        # blocked by the schema — the block has to travel two hops.
        plan.packages.append(
            BuildPackage(
                id="pkg_feature_report",
                kind=PackageKind.feature,
                goal="Build the report feature.",
                architecture_slice=[NodeRef(kind="operation", name="list_report")],
                dependencies=[BOOKING],
                acceptance_criteria=["An owner can see today's bookings."],
            )
        )
        plan.order = topological_order(plan.packages)
        plan.graph = {p.id: list(p.dependencies) for p in plan.packages}

        replies = [
            FOUNDATION_CODE, PASS,
            TOKENS_CODE, PASS,
            SCHEMA_BROKEN, SCHEMA_BROKEN,
        ]
        result, _, _ = await run(tmp_path, replies, plan=plan)

        report = result.get("pkg_feature_report")
        assert report.status is PackageStatus.blocked
        assert BOOKING in report.remainders[0].what  # the dependency it waited on
        assert report.remainders[0].where == SCHEMA  # the root cause, named

    async def test_nothing_crashes_when_a_package_produces_no_code(self, tmp_path):
        replies = [
            FOUNDATION_CODE, PASS,
            TOKENS_CODE, PASS,
            "I would start by considering the guests.",
            "Still thinking about it.",
        ]
        result, _, _ = await run(tmp_path, replies)

        assert result.get(SCHEMA).status is PackageStatus.failed
        assert result.blocked == [BOOKING, MENU]
        assert "5 parts" in result.honest_summary()


class TestProgress:
    async def test_progress_events_count_real_parts(self, tmp_path):
        events = []
        preview = CountingPreview([clean()])
        registry = ProviderRegistry.scripted(ALL_GOOD, loop_last=False)
        async for event, payload in stream_build_plan(
            make_plan(),
            tmp_path,
            contracts=CONTRACTS,
            registry=registry,
            preview=preview,
            options=options(),
        ):
            events.append((event, payload))

        kinds = [event for event, _ in events]
        assert kinds[-1] == "result"
        assert kinds.count("package") == 5

        finished = [
            payload
            for event, payload in events
            if event == "progress"
            and isinstance(payload, BuildProgress)
            and payload.status != "building"
        ]
        assert [p.done for p in finished] == [1, 2, 3, 4, 5]
        assert finished[-1].as_line().startswith("5 of 5 parts done")
        assert finished[2].as_line().startswith("3 of 5 parts done")


@pytest.mark.parametrize("package_id", [FOUNDATION, SCHEMA, TOKENS, BOOKING, MENU])
async def test_every_package_reports_four_checks(tmp_path, package_id):
    result, _, _ = await run(tmp_path, ALL_GOOD)

    assert result.get(package_id).checks_passed == 4
