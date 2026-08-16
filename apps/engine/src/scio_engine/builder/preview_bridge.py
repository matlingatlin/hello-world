"""Putting the marking bridge into a preview build — and keeping it out of delivery.

The design window needs the running app to report what the user marked, because
it cannot read into the iframe (spikes/design-marking). So a preview build ships
one extra client-side module. A delivery build does not.

The mechanism is deliberately the same one the verification data layer already
uses (library/verification): a conditional inside the app's own next.config.js,
evaluated at boot from an environment flag. Consequences worth stating:

- **The generated code is untouched.** The bridge is added to the client bundle
  by webpack, not written into `app/layout.tsx`. That matters more than it
  looks: the manifest maps ids to *source lines*, isolation compares file
  hashes, and directed regeneration rewrites whole packages. Editing generated
  files to add a preview feature would disturb all three.
- **Absent, not disabled.** Without the flag the entry is never registered, so
  the code is not in the bundle. There is no build in which the delivered app
  contains a listener that "happens to be off".
- **It lives under `.scio/`**, which the workspace gitignores — build
  scaffolding, not the user's code.
"""

from __future__ import annotations

import os
from pathlib import Path

PREVIEW_FLAG = "SCIO_PREVIEW_MODE"
SHELL_ORIGIN_ENV = "NEXT_PUBLIC_SCIO_SHELL_ORIGIN"
"""NEXT_PUBLIC_ so Next inlines it into the client bundle — the bridge needs the
shell's origin at runtime, in the browser, to pin its postMessage target."""

BRIDGE_SOURCE = Path(__file__).resolve().parent / "preview" / "bridge.js"
BRIDGE_DIR = ".scio/preview"
BRIDGE_FILE = f"{BRIDGE_DIR}/bridge.js"


def preview_enabled(env: dict[str, str] | None = None) -> bool:
    """Whether this process should build previews with the bridge."""
    source = env if env is not None else os.environ
    return source.get(PREVIEW_FLAG, "").lower() in {"1", "true", "yes"}


def preview_webpack() -> str:
    """The next.config.js block that adds the bridge to the client bundle.

    Prepended to `main-app` (the App Router's client entry) so it runs before
    the app's own code on every route, with no import for the app to forget.
    """
    return f"""
    if (previewing && !isServer) {{
      // The marking bridge, for the design window (spikes/design-marking).
      // Registered ONLY under {PREVIEW_FLAG}: a delivery build does not reach
      // this branch, so the bridge is absent from the bundle rather than
      // present-and-idle.
      const previousEntry = config.entry;
      config.entry = async () => {{
        const entries = await previousEntry();
        const bridge = path.resolve(__dirname, "{BRIDGE_FILE}");
        for (const name of ["main-app", "main"]) {{
          const entry = entries[name];
          if (Array.isArray(entry) && !entry.includes(bridge)) entry.unshift(bridge);
        }}
        return entries;
      }};
    }}
"""


def preview_flag_js() -> str:
    """The boot-time condition the block above reads."""
    return f"""
const previewing = ["1", "true", "yes"].includes(
  String(process.env.{PREVIEW_FLAG} ?? "").toLowerCase(),
);
"""


def prepare(app_dir: Path) -> Path:
    """Write the bridge into the app. Safe to call on every build."""
    app_dir = Path(app_dir).resolve()
    target = app_dir / BRIDGE_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(BRIDGE_SOURCE.read_text())
    gitignore = app_dir / ".scio" / ".gitignore"
    if not gitignore.exists():
        gitignore.parent.mkdir(parents=True, exist_ok=True)
        gitignore.write_text("*\n")
    return target


def preview_env(shell_origin: str) -> dict[str, str]:
    """What the app's process needs so the bridge is built in, and knows who to
    talk to. Without an origin the bridge stays silent rather than broadcasting."""
    return {PREVIEW_FLAG: "1", SHELL_ORIGIN_ENV: shell_origin}


def bridge_in(html: str) -> bool:
    """Whether a served page carries the bridge.

    Used by the tests that hold the delivery promise: the same app, served
    without the flag, must not contain it.
    """
    return "scio-preview" in html or "__scioBridge" in html
