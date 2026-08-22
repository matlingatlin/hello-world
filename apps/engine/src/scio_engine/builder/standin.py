"""A stand-in for the model that writes the code, for running without keys.

Be clear about what this is. It is NOT a model and its output is NOT real app
code: it emits syntactically valid, correctly instrumented placeholder files that
satisfy the contract's shape. That proves the *pipeline* — plan, generate, verify
instrumentation, run, look, judge, assemble, persist — end to end, on a machine
with no API keys. It proves nothing about code quality; that needs real models.

It exists because the alternative is worse. FakeProvider returns a digest, so
every package would fail extraction and the whole path would be untestable
without keys — and an untestable path is one that breaks quietly between the day
keys are added and the day anyone notices.

B041b's verify script used a hand-written app for one fixed plan. This does the
same job for any plan, by reading the contract it is given.
"""

from __future__ import annotations

import re

from ..execution.provider import Completion, Message, ModelProvider, ProviderRegistry, Vendor

_PACKAGE_ID = re.compile(r"^# Build package: (\S+)", re.MULTILINE)
_OWNED_FILES = re.compile(r"^- (\S+\.\w+)$", re.MULTILINE)
_OPERATIONS = re.compile(r"^operation (\w+)", re.MULTILINE)
_CURRENT_FILES = re.compile(
    r"^FILE: (?P<path>\S+)\n```\n(?P<body>.*?)^```", re.MULTILINE | re.DOTALL
)
_CRITIQUE_MARKER = "Acceptance criteria (judge against exactly these)"
_DESIGN_CHANGE_MARKER = "## What the user marked, and what they want"

PASS_VERDICT = '{"verdict": "pass", "criteria": [], "problems": []}'


def _component_name(path: str) -> str:
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return "".join(part.capitalize() for part in re.split(r"[-_]", stem) if part) or "Part"


def _slug(package: str, path: str) -> str:
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    prefix = package.removeprefix("pkg_").replace("_", "-")
    return f"{prefix}-{stem}".replace("--", "-")


def _page(package: str, path: str, operations: list[str]) -> str:
    """A route page. Every element is instrumented, which is what the verifier
    and the design window both depend on."""
    name = _component_name(path.removesuffix("/page.tsx") or "home") + "Page"
    scio = _slug(package, path.removesuffix("/page.tsx") or "home")
    listed = "".join(
        f'\n      <li data-scio-id="{scio}-op-{op.replace("_", "-")}" '
        f'data-scio-package="{package}">{op}</li>'
        for op in operations
    )
    body = (
        f'\n    <ul data-scio-id="{scio}-ops" data-scio-package="{package}">'
        f"{listed}\n    </ul>"
        if listed
        else ""
    )
    return f"""export default function {name}() {{
  return (
    <main data-scio-id="{scio}" data-scio-package="{package}">
      <h1 data-scio-id="{scio}-title" data-scio-package="{package}">{package}</h1>{body}
    </main>
  );
}}
"""


def _layout(package: str) -> str:
    # The stylesheet is part of the locked stack and the workspace scaffolds it,
    # so this import always resolves — even before the design-tokens package runs.
    return f"""import "./globals.css";

export const metadata = {{ title: "Scio app" }};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body data-scio-id="app-shell" data-scio-package="{package}">
        {{children}}
      </body>
    </html>
  );
}}
"""


def _component(package: str, path: str) -> str:
    name = _component_name(path)
    scio = _slug(package, path)
    return f"""export function {name}() {{
  return (
    <section data-scio-id="{scio}" data-scio-package="{package}">
      <button data-scio-id="{scio}-action" data-scio-package="{package}">{name}</button>
    </section>
  );
}}
"""


def _module(path: str, operations: list[str]) -> str:
    """A lib module. The operation names matter: the contract-consistency agent
    checks that everything the package owns is actually present in its code."""
    functions = "\n\n".join(
        f"export async function {op}(input: Record<string, unknown>) {{\n"
        f"  return {{ ok: true, operation: \"{op}\", input }};\n}}"
        for op in operations
    ) or "export const ready = true;"
    return functions + "\n"


def _test(path: str, operations: list[str]) -> str:
    if not operations:
        return 'test("the part is present", () => {\n  expect(true).toBe(true);\n});\n'
    checks = "\n".join(
        f'  expect(typeof {op}).toBe("function");' for op in operations
    )
    return (
        'test("every operation this part owns exists", () => {\n' + checks + "\n});\n"
    )


_TAILWIND_CONFIG = """import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};

export default config;
"""


_SUPABASE_MODULE = """import { createClient, type SupabaseClient } from "@supabase/supabase-js";

/**
 * The app's one database client.
 *
 * A real module rather than a placeholder, for the same reason as
 * `tailwind.config.ts`: the library's own components import `getSupabaseClient`
 * from here on every assembled build, and a file exporting a lone boolean makes
 * the finished app fail to compile — which is exactly what shipped before
 * anybody asked the compiler (B048).
 */
let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (client) return client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";
  client = createClient(url, key);
  return client;
}

/** Whether a database has actually been connected yet. A preview runs before
 *  anyone has, and a screen that 500s because of that helps nobody. */
export function hasDatabase(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL);
}
"""


def _content_for(package: str, path: str, operations: list[str]) -> str:
    if path.endswith(".sql"):
        return "-- schema placeholder\nselect 1;\n"
    if path.endswith("tailwind.config.ts"):
        # A real config, not a placeholder: PostCSS loads this file on every
        # compile, so an `export const ready = true` here breaks the whole app.
        return _TAILWIND_CONFIG
    if path.endswith(".css"):
        return (
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n\n"
            ":root { --ink: #101319; --paper: #ffffff; }\n"
        )
    if path == "lib/supabase.ts":
        return _SUPABASE_MODULE
    if path == "app/layout.tsx":
        return _layout(package)
    if path.endswith("/page.tsx"):
        return _page(package, path, operations)
    if path.endswith((".tsx", ".jsx")):
        return _component(package, path)
    if "test" in path or "spec" in path:
        return _test(path, operations)
    if path.endswith((".ts", ".js")):
        return _module(path, operations)
    return "// placeholder\n"


def generate_files(prompt: str) -> str:
    """Turn a build prompt into FILE blocks for exactly the paths it names."""
    package_match = _PACKAGE_ID.search(prompt)
    package = package_match.group(1) if package_match else "pkg_unknown"
    files = _OWNED_FILES.findall(prompt)
    operations = _OPERATIONS.findall(prompt)

    blocks = []
    for path in files:
        # The module implements the operations and its test checks them; the page
        # lists them, so the assembled app visibly reflects what the part owns.
        ops = (
            operations
            if (path.endswith(".ts") and not path.endswith(".d.ts"))
            or path.endswith("/page.tsx")
            else []
        )
        blocks.append(f"FILE: {path}\n```\n{_content_for(package, path, ops)}```")
    return "\n\n".join(blocks) or "No files were requested."


def echo_current_files(prompt: str) -> str:
    """A 'fix' from the stand-in returns the code unchanged.

    It has no judgment to apply, and inventing a change would corrupt the very
    instrumentation the loop is checking.
    """
    blocks = [
        f"FILE: {m.group('path')}\n```\n{m.group('body')}```"
        for m in _CURRENT_FILES.finditer(prompt)
    ]
    return "\n\n".join(blocks) or generate_files(prompt)


def apply_marked_change(prompt: str) -> str:
    """A directed change from the stand-in: the same code, plus a note saying so.

    Without this the free path stops dead at gate 2, because the ordinary fake
    provider returns a digest and extraction fails — so nobody without an API
    key could ever click through the design window, which is exactly the kind of
    path that breaks quietly (see this module's opening note).

    It changes one thing and one thing only: a comment at the top of each file
    the change touched, naming what was asked for. That is a real byte change,
    so the round trip is genuinely exercised — isolation proof, instrumentation
    re-verification, commit, design version — while every `data-scio-id` is left
    exactly where it was. Inventing an actual edit would corrupt the coupling the
    whole gate depends on, and pretending to have made one would be a lie the
    user could not see through.
    """
    asked = prompt.rsplit(_DESIGN_CHANGE_MARKER, 1)[-1].strip().splitlines()
    wanted = " / ".join(line.strip() for line in asked[:4] if line.strip())[:160]
    blocks = []
    for match in _CURRENT_FILES.finditer(prompt):
        body = match.group("body")
        note = (
            "// scio stand-in: no model configured, so this was not really "
            f"changed. Asked: {wanted}\n"
        )
        without_note = "\n".join(
            line for line in body.splitlines() if not line.startswith("// scio stand-in:")
        )
        blocks.append(f"FILE: {match.group('path')}\n```\n{note}{without_note}\n```")
    return "\n\n".join(blocks) or generate_files(prompt)


class StandInProvider(ModelProvider):
    """Answers the builder's prompts deterministically, without a model."""

    vendor = Vendor.fake

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Message]]] = []

    async def complete(
        self,
        model: str,
        messages: list[Message],
        *,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout_s: float = 120.0,
    ) -> Completion:
        self.calls.append((model, messages))
        joined = "\n".join(m.content for m in messages)

        if _CRITIQUE_MARKER in joined:
            text = PASS_VERDICT
        elif _DESIGN_CHANGE_MARKER in joined:
            text = apply_marked_change(joined)
        elif "## What is wrong" in joined:
            text = echo_current_files(joined)
        else:
            text = generate_files(joined)

        return Completion(
            text=text,
            model=model,
            vendor=Vendor.fake,
            input_tokens=len(joined.split()),
            output_tokens=len(text.split()),
            stop_reason="end_turn",
        )


def standin_registry() -> ProviderRegistry:
    """A registry whose every vendor is the stand-in.

    Used only for the *builder*: Layer B and Layer C keep the ordinary registry,
    because their fallbacks are already honest (a deterministic narrative, and
    rules).
    """
    shared = StandInProvider()
    return ProviderRegistry(
        providers={
            Vendor.anthropic: shared,
            Vendor.openai: shared,
            Vendor.google: shared,
            Vendor.fake: shared,
        }
    )
