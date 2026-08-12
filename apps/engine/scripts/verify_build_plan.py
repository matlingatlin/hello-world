#!/usr/bin/env python3
"""Prove the ORCHESTRATOR against a real running app, not just fixtures.

The unit tests cover the decisions (order, blocking, aggregate status). This
covers the claim they cannot: that packages generated one after another actually
assemble into ONE app that runs together — the shell booting first, later
packages appearing in the same live server, and every route rendering at the end.

The model is scripted (no keys here), the sandbox and the browser are real:

    python3 scripts/verify_build_plan.py [workdir]

Needs the spike's app for its installed node_modules (Next.js will not boot
without them, and installing mid-boot is what killed the first spike run).
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE / "src"))

from scio_engine.builder.loop import BuildOptions, SandboxPreview  # noqa: E402
from scio_engine.builder.orchestrate import (  # noqa: E402
    AppBuildOptions,
    stream_build_plan,
)
from scio_engine.core.instrumentation import Manifest  # noqa: E402
from scio_engine.core.preview import PreviewInspector  # noqa: E402
from scio_engine.core.sandbox import LocalProcessSandbox  # noqa: E402
from scio_engine.execution.provider import ProviderRegistry  # noqa: E402
from scio_engine.layerc.decompose import topological_order  # noqa: E402
from scio_engine.layerc.plan import (  # noqa: E402
    BuildPackage,
    BuildPlan,
    NodeRef,
    PackageInterface,
    PackageKind,
)

SPIKE_APP = ENGINE.parent.parent / "spikes" / "sandbox-marking" / "example-app"
SCAFFOLD = ("package.json", "next.config.js", "tsconfig.json", "next-env.d.ts")

FOUNDATION, TOKENS, SCHEMA = "pkg_foundation", "pkg_design_tokens", "pkg_schema"
BOOKING, MENU = "pkg_feature_booking", "pkg_feature_menu"


def make_plan() -> BuildPlan:
    packages = [
        BuildPackage(
            id=FOUNDATION,
            kind=PackageKind.foundation,
            goal="Scaffold the app shell and the home screen.",
            architecture_slice=[
                NodeRef(kind="security", name="security_posture"),
                NodeRef(kind="screen", name="/"),
            ],
            interface=PackageInterface(routes=["/"], exports=["app shell"]),
            acceptance_criteria=["The shell renders and the home screen is reachable."],
        ),
        BuildPackage(
            id=TOKENS,
            kind=PackageKind.design_tokens,
            goal="Encode the design tokens.",
            architecture_slice=[NodeRef(kind="tokens", name="design_tokens")],
            dependencies=[FOUNDATION],
            acceptance_criteria=["Tokens are defined once."],
        ),
        BuildPackage(
            id=SCHEMA,
            kind=PackageKind.schema,
            goal="Create the bookings and dishes tables.",
            architecture_slice=[
                NodeRef(kind="table", name="bookings"),
                NodeRef(kind="table", name="dishes"),
            ],
            dependencies=[FOUNDATION],
            interface=PackageInterface(tables=["bookings", "dishes"]),
            acceptance_criteria=["Every table exists with row-level security."],
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


# --- the scripted "model" -----------------------------------------------------
# Real Next.js code: it has to compile and render, or the live proof proves
# nothing. Written once here so the run is reproducible.

FOUNDATION_CODE = """FILE: app/layout.tsx
```tsx
import { SiteHeader } from "../components/site-header";

export const metadata = { title: "Bistro Nord" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
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
      <a data-scio-id="nav-booking" data-scio-package="pkg_foundation" href="/booking">Book</a>
      <a data-scio-id="nav-menu" data-scio-package="pkg_foundation" href="/menu">Menu</a>
    </header>
  );
}
```

FILE: lib/supabase.ts
```ts
export const supabase = {
  from(table: string) {
    return { insert: async (row: unknown) => ({ table, row }) };
  },
};
```

FILE: app/page.tsx
```tsx
export default function HomePage() {
  return (
    <main data-scio-id="home-main" data-scio-package="pkg_foundation">
      <h1 data-scio-id="home-title" data-scio-package="pkg_foundation">Welcome to Bistro Nord</h1>
    </main>
  );
}
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


def feature_code(entity: str, route: str, operation: str, label: str) -> str:
    package = f"pkg_feature_{entity}"
    component = entity.title()
    return f"""FILE: app{route}/page.tsx
```tsx
import {{ {component}Form }} from "../../components/{entity}-form";

export default function {component}Page() {{
  return (
    <main data-scio-id="{entity}-page" data-scio-package="{package}">
      <h1 data-scio-id="{entity}-title" data-scio-package="{package}">{label}</h1>
      <{component}Form />
    </main>
  );
}}
```

FILE: components/{entity}-form.tsx
```tsx
export function {component}Form() {{
  return (
    <form data-scio-id="{entity}-form" data-scio-package="{package}">
      <input
        data-scio-id="{entity}-name"
        data-scio-package="{package}"
        name="name"
        placeholder="Your name"
      />
      <button data-scio-id="{entity}-submit" data-scio-package="{package}">{label}</button>
    </form>
  );
}}
```

FILE: components/{entity}-list.tsx
```tsx
export function {component}List({{ rows }}: {{ rows: {{ id: string; name: string }}[] }}) {{
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

export async function {operation}(input: {{ name: string }}) {{
  return await supabase.from("{entity}s").insert(input);
}}
```

FILE: tests/{entity}.test.ts
```ts
import {{ {operation} }} from "../lib/db/{entity}";

test("{operation} stores a row", async () => {{
  expect(await {operation}({{ name: "Ada" }})).toBeTruthy();
}});
```
"""


PASS = '{"verdict": "pass", "criteria": [], "problems": []}'

REPLIES = [
    FOUNDATION_CODE, PASS,
    TOKENS_CODE, PASS,
    SCHEMA_CODE, PASS,
    feature_code("booking", "/booking", "create_booking", "Book a table"), PASS,
    feature_code("menu", "/menu", "list_menu", "Today's menu"), PASS,
]

CONTRACTS = {
    package: f"# Build package: {package}\nBuild exactly your slice."
    for package in (FOUNDATION, TOKENS, SCHEMA, BOOKING, MENU)
}


def heading(text: str) -> None:
    print(f"\n{'=' * 68}\n{text}\n{'=' * 68}")


def scaffold(workdir: Path) -> None:
    """A workspace with dependencies already installed — the sandbox refuses to
    start otherwise, and for good reason (see LocalProcessSandbox)."""
    workdir.mkdir(parents=True, exist_ok=True)
    for name in SCAFFOLD:
        shutil.copy2(SPIKE_APP / name, workdir / name)
    node_modules = workdir / "node_modules"
    if not node_modules.exists():
        node_modules.symlink_to(SPIKE_APP / "node_modules")


async def main() -> int:
    workdir = Path(sys.argv[1]) if len(sys.argv) > 1 else ENGINE / "out" / "assembled-app"
    if not (SPIKE_APP / "node_modules").exists():
        print(f"Need installed dependencies to borrow. Tried: {SPIKE_APP}")
        return 1

    if workdir.exists():
        shutil.rmtree(workdir)
    scaffold(workdir)

    plan = make_plan()
    heading("1. The plan, in dependency order")
    for index, package_id in enumerate(plan.order, start=1):
        deps = plan.graph[package_id]
        print(f"  {index}. {package_id}  <- {', '.join(deps) or 'nothing'}")

    heading("2. Build every package INTO ONE running app")
    preview = SandboxPreview(
        LocalProcessSandbox(), screenshot_dir=workdir.parent / "assembled-shots"
    )
    registry = ProviderRegistry.scripted(REPLIES, loop_last=False)
    options = AppBuildOptions(
        package=BuildOptions(max_attempts=2, codegen_passes=1, critique_passes=1),
        close_preview=False,  # keep it up: the routes are checked below
    )

    result = None
    async for event, payload in stream_build_plan(
        plan, workdir, contracts=CONTRACTS, registry=registry, preview=preview, options=options
    ):
        if event == "progress" and payload.status == "building":
            print(f"  -> {payload.package_id} ...")
        elif event == "progress":
            print(f"     {payload.as_line()}")
        elif event == "result":
            result = payload

    assert result is not None
    heading("3. Aggregate status (what the reveal shows)")
    print(result.honest_summary())
    print(f"\napp url:       {result.app_url}")
    print(f"build version: {result.build_version} @ {result.git_sha[:12]}")
    print(f"elements:      {result.element_count} instrumented, app-wide")

    heading("4. The app-wide manifest (derived from the assembled source)")
    manifest = Manifest.load(workdir / "scio-manifest.json")
    for package_id in plan.order:
        owned = sorted(i for i, loc in manifest.elements.items() if loc.package == package_id)
        print(f"  {package_id}: {', '.join(owned) or '(no instrumented elements)'}")

    heading("5. Every route renders, in the SAME running app")
    # Each route is checked for the shell AND for the package that owns it: a
    # route that only shows the shell would mean the later package never made it
    # into the running app, which is the whole claim under test.
    routes = {
        "/": (FOUNDATION, "[data-scio-id='home-title']"),
        "/booking": (BOOKING, "[data-scio-id='booking-submit']"),
        "/menu": (MENU, "[data-scio-id='menu-submit']"),
    }
    ok = True
    for route, (owner, selector) in routes.items():
        inspector = PreviewInspector(result.app_url.rstrip("/") + route)
        # Playwright's sync API cannot run inside a running asyncio loop.
        observation = await asyncio.to_thread(
            inspector.observe,
            workdir.parent / "assembled-shots" / f"route{route.replace('/', '-')}.png",
            selectors=["[data-scio-id='site-header']", selector],
        )
        shell, owned = observation.hits[0], observation.hits[1]
        rendered = owned.scio_package == owner and shell.scio_id == "site-header"
        print(
            f"  {route:<9} shell={shell.scio_id} + {owned.scio_id} ({owned.scio_package}) "
            f"text={owned.text!r} console-failures={observation.console.failures or 'none'}"
        )
        ok = ok and observation.console.clean and rendered

    preview.close()

    heading("VERDICT")
    print(f"assembled into one running app: {'YES' if ok and result.works else 'NO'}")
    print(f"screenshots: {workdir.parent / 'assembled-shots'}")
    return 0 if ok and result.works else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
