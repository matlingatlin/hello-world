#!/usr/bin/env python3
"""The in-iframe marking bridge, end to end.

    booking blueprint -> Next dev (origin A, bridge injected)
                      -> shell (origin B) embeds it in an iframe
                      -> click inside the frame -> postMessage out
                      -> strict resolver: scio_id -> package + source line
                      -> mechanical directed change to that package only
                      -> re-serve, reload, only that change is visible

Everything that decides anything is the engine's real code: `resolve_marking`,
`build_manifest`, `directed_regenerate`, `verify_isolation`. The spike supplies
the two things that do not exist yet — the bridge inside the preview, and a
parent shell to receive from it.

    python3 run_spike.py           run the whole chain and print the verdict
    python3 run_spike.py --serve   just bring both origins up and leave them

Nothing here is production. See ../design-marking/FINDINGS.md for the verdict.
"""

from __future__ import annotations

import http.server
import json
import os
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

SPIKE = Path(__file__).resolve().parent
REPO = SPIKE.parents[1]
ENGINE = REPO / "apps" / "engine"
FIXTURE = REPO / "spikes" / "local-data" / "app"
APP = SPIKE / "app"
OUT = SPIKE / "out"

sys.path.insert(0, str(ENGINE / "src"))

from scio_engine.core.instrumentation import Manifest  # noqa: E402
from scio_engine.core.manifest_builder import build_manifest  # noqa: E402
from scio_engine.core.regenerate import (  # noqa: E402
    MechanicalRegenerator,
    directed_regenerate,
)
from scio_engine.core.resolver import (  # noqa: E402
    ElementHit,
    MarkingResolutionError,
    resolve_marking,
)
from scio_engine.core.stamping import stamp_files  # noqa: E402

# The package each file belongs to. In a real build this is Layer C's file plan;
# the fixture predates it, so the spike states it once, here, and everything
# downstream (stamping, manifest, isolation) derives from this single map.
PACKAGE_FILES: dict[str, list[str]] = {
    "pkg_foundation": ["app/layout.tsx", "app/page.tsx"],
    "pkg_feature_booking": [
        "app/booking/page.tsx",
        "app/booking/new/page.tsx",
        "components/booking-form.tsx",
        "components/booking-list.tsx",
        "lib/db/booking.ts",
        "lib/validation/booking.ts",
        "app/actions/booking.ts",
    ],
}


def say(message: str) -> None:
    print(f"\n\033[36m▸ {message}\033[0m", flush=True)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# --------------------------------------------------------------------------
# 1. The fixture: the booking blueprint, stamped, with the bridge injected
# --------------------------------------------------------------------------


def prepare_app(shell_origin: str) -> Manifest:
    """A working copy of the blueprint, in preview mode."""
    if APP.exists():
        shutil.rmtree(APP)
    shutil.copytree(
        FIXTURE,
        APP,
        symlinks=True,
        ignore=shutil.ignore_patterns("node_modules", ".next", ".env.local", ".scio"),
    )
    # 294 MB of dependencies, already installed by the local-data spike. A
    # symlink rather than a copy: this app is a fixture, not a deliverable.
    (APP / "node_modules").symlink_to(FIXTURE / "node_modules", target_is_directory=True)

    # The blueprint carries data-scio-id everywhere but was written before
    # stamping existed, so most files have no data-scio-package. Stamp with the
    # real stamper — the manifest and the resolver both depend on the tag.
    for package, files in PACKAGE_FILES.items():
        contents = {f: (APP / f).read_text() for f in files if (APP / f).exists()}
        for relative, stamped in stamp_files(contents, package).items():
            (APP / relative).write_text(stamped)

    _inject_bridge(shell_origin)

    manifest = build_manifest(APP, PACKAGE_FILES)
    OUT.mkdir(exist_ok=True)
    manifest.save(OUT / "manifest.json")
    return manifest


BRIDGE_MARK = "__scio_preview_bridge__"


def _inject_bridge(shell_origin: str) -> None:
    """Put the bridge in the layout — behind the preview-mode flag.

    This is the shape the real thing would take: the design window serves the
    app with SCIO_PREVIEW_MODE set, and the delivered app never has the flag, so
    the script tag does not render at all. It is one conditional in the layout,
    not a build variant.
    """
    shutil.copy(SPIKE / "preview" / "bridge.js", _public() / "bridge.js")

    layout = APP / "app" / "layout.tsx"
    source = layout.read_text()
    if BRIDGE_MARK in source:
        return
    injected = f"""
{{/* {BRIDGE_MARK}: PREVIEW ONLY. Absent from the app the user receives —
    the flag is set by the design window's sandbox, never by a build. */}}
{{process.env.SCIO_PREVIEW_MODE === "1" ? (
  <>
    <script
      dangerouslySetInnerHTML={{{{
        __html: `window.__SCIO_SHELL_ORIGIN__ = {json.dumps(shell_origin)};`,
      }}}}
    />
    <script src="/__scio/bridge.js" defer />
  </>
) : null}}
"""
    source = source.replace(
        "{children}</body>",
        "{children}" + injected + "</body>",
    )
    layout.write_text(source)


def _public() -> Path:
    target = APP / "public" / "__scio"
    target.mkdir(parents=True, exist_ok=True)
    return target


# --------------------------------------------------------------------------
# 2. Two origins
# --------------------------------------------------------------------------


def start_preview(port: int, preview_mode: bool = True) -> subprocess.Popen:
    process = subprocess.Popen(
        ["npx", "next", "dev", "--port", str(port), "--hostname", "127.0.0.1"],
        cwd=APP,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={
            **os.environ,
            "NEXT_TELEMETRY_DISABLED": "1",
            **({"SCIO_PREVIEW_MODE": "1"} if preview_mode else {}),
        },
    )
    _await(f"http://127.0.0.1:{port}/booking/new", 180, process)
    return process


def _await(url: str, timeout: int, process: subprocess.Popen | None = None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            raise SystemExit(f"the preview died:\n{process.stdout.read()}")
        try:
            urllib.request.urlopen(url, timeout=10)
            return
        except urllib.error.HTTPError:
            return  # serving, just not 200 — good enough to be up
        except Exception:
            time.sleep(1)
    raise SystemExit(f"{url} never came up")


class Shell(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """The design-window stub. Serves the page, and does the two things the
    browser must not be trusted to do: resolve a marking, and apply a change."""

    daemon_threads = True
    allow_reuse_address = True

    manifest: Manifest
    preview_origin: str
    changes: list[dict]


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def _send(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/config"):
            return self._send({"preview_origin": self.server.preview_origin})
        if self.path.startswith("/manifest"):
            return self._send(json.loads(self.server.manifest.model_dump_json()))
        body = (SPIKE / "shell" / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)) or b"{}")
        if self.path.startswith("/resolve"):
            return self._send(resolve_payload(payload, self.server.manifest))
        if self.path.startswith("/change"):
            return self._send(apply_change(payload, self.server))
        self._send({"error": "not found"}, 404)


def resolve_payload(payload: dict, manifest: Manifest) -> dict:
    """A postMessage from the bridge -> a package and a source line, or a refusal."""
    raw = payload.get("hit", {})
    hit = ElementHit(
        scio_id=raw.get("scio_id"),
        scio_package=raw.get("scio_package"),
        tag=raw.get("tag", ""),
        text=raw.get("text", ""),
        ancestor_id=raw.get("ancestor_id"),
        ancestor_package=raw.get("ancestor_package"),
        ancestor_distance=raw.get("ancestor_distance", 0),
    )
    try:
        marking = resolve_marking(hit, manifest)
    except MarkingResolutionError as exc:
        return {"ok": False, "error": str(exc), "coords": payload.get("coords", {})}
    return {
        "ok": True,
        "scio_id": marking.scio_id,
        "package": marking.package,
        "file": marking.location.file,
        "line": marking.location.line,
        "tag": hit.tag,
        "text": hit.text,
        "coords": payload.get("coords", {}),
        "route": payload.get("route", ""),
    }


# The mock change. A find/replace, chosen so it appears in exactly one package's
# files — the point is the targeting and the isolation proof, not the edit.
MOCK_EDITS = {
    "Book a table → Reserve our table": ("Book a table", "Reserve our table"),
    "No bookings yet → Nothing booked yet": ("No bookings yet", "Nothing booked yet"),
}


def apply_change(payload: dict, server: Shell) -> dict:
    """A directed change through the engine's own guarded path."""
    marking = payload.get("marking") or {}
    instruction = payload.get("instruction", "")
    find, replace = MOCK_EDITS.get(instruction, (instruction, instruction))

    hit = ElementHit(
        scio_id=marking.get("scio_id"),
        scio_package=marking.get("package"),
        tag=marking.get("tag", ""),
    )
    try:
        result = directed_regenerate(
            APP,
            hit,
            instruction,
            manifest=server.manifest,
            regenerator=MechanicalRegenerator(find, replace),
            package_files=PACKAGE_FILES,
        )
    except Exception as exc:
        return {"ok": False, "summary": f"{type(exc).__name__}: {exc}"}

    server.manifest = result.manifest
    record = {
        "instruction": instruction,
        "note": payload.get("note", ""),
        "package": result.package,
        "edited": result.edited_files,
        "isolated": result.isolation.isolated,
        "unchanged": len(result.isolation.unchanged_files),
        "accepted": result.accepted,
    }
    server.changes.append(record)
    return {
        "ok": result.accepted and result.isolation.isolated,
        "summary": result.isolation.summary(),
        **record,
    }


def start_shell(port: int, manifest: Manifest, preview_origin: str) -> Shell:
    server = Shell(("127.0.0.1", port), Handler)
    server.manifest = manifest
    server.preview_origin = preview_origin
    server.changes = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# --------------------------------------------------------------------------
# 3. Drive it
# --------------------------------------------------------------------------


def drive(shell_origin: str, preview_origin: str, shots: Path) -> dict:
    """Do what a person would do, in a real browser."""
    from playwright.sync_api import sync_playwright

    from scio_engine.core.preview import chromium_executable

    found: dict = {}
    shots.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium_executable())
        page = browser.new_page(viewport={"width": 1360, "height": 900})
        page.goto(shell_origin, wait_until="networkidle")
        page.wait_for_timeout(2500)

        found["dom_access"] = page.inner_text('[data-testid="dom-access"]')

        page.click('[data-testid="arm"]')
        frame = next(f for f in page.frames if preview_origin in f.url)

        # Mark the submit button: an instrumented leaf, inside the feature.
        frame.click('[data-scio-id="booking-form-submit"]')
        page.wait_for_selector('[data-testid="marking"]', timeout=15000)
        page.wait_for_timeout(400)
        page.screenshot(path=str(shots / "01-marked.png"), full_page=True)
        found["first_marking"] = page.inner_text('[data-testid="marking"]')

        # A second marking, with a note — the shell must hold several.
        frame.click('[data-scio-id="booking-form-name"]')
        page.wait_for_timeout(600)
        notes = page.query_selector_all(".note")
        if notes:
            notes[-1].fill("this label should say 'Your full name'")
        found["markings"] = page.eval_on_selector_all(
            '[data-testid="marking"]', "e => e.map(x => x.innerText.split('\\n')[0])"
        )
        page.screenshot(path=str(shots / "02-two-markings.png"), full_page=True)

        # Mark an element that is NOT instrumented, to see the refusal.
        frame.evaluate(
            """() => {
              const el = document.createElement('div');
              el.id = 'uninstrumented';
              el.textContent = 'no scio id here';
              el.style.cssText = 'padding:20px;background:#fee';
              document.querySelector('[data-scio-id="booking-form"]').appendChild(el);
            }"""
        )
        frame.click("#uninstrumented")
        page.wait_for_timeout(800)
        found["refusal"] = page.eval_on_selector_all(
            '[data-testid="marking"]', "e => e.map(x => x.innerText).filter(t => t.includes('Could not'))"
        )

        # The round trip.
        before = (APP / "components" / "booking-form.tsx").read_text()
        layout_before = (APP / "app" / "layout.tsx").read_text()
        page.fill('[data-testid="instruction"]', "Book a table → Reserve our table")
        page.click('[data-testid="apply"]')
        page.wait_for_function(
            "() => document.querySelector('[data-testid=\"result\"]').innerText.includes('target package')",
            timeout=60000,
        )
        found["change_result"] = page.inner_text('[data-testid="result"]')

        # Next recompiles on file change; the shell reloads the frame itself.
        page.wait_for_timeout(9000)
        page.screenshot(path=str(shots / "03-after-change.png"), full_page=True)
        frame = next(f for f in page.frames if preview_origin in f.url)
        found["button_after"] = frame.inner_text('[data-scio-id="booking-form-submit"]')
        found["ids_after"] = frame.eval_on_selector_all(
            "[data-scio-id]", "e => e.map(x => x.getAttribute('data-scio-id'))"
        )
        found["form_changed"] = (APP / "components" / "booking-form.tsx").read_text() != before
        found["layout_untouched"] = (APP / "app" / "layout.tsx").read_text() == layout_before

        browser.close()
    return found


def main() -> int:
    if not FIXTURE.exists():
        raise SystemExit(f"fixture missing: {FIXTURE} (run the local-data spike first)")

    preview_port, shell_port = free_port(), free_port()
    preview_origin = f"http://127.0.0.1:{preview_port}"
    shell_origin = f"http://127.0.0.1:{shell_port}"

    say("Assembling the blueprint with the bridge injected")
    manifest = prepare_app(shell_origin)
    print(f"  {len(manifest.elements)} instrumented ids, {len(manifest.packages)} packages")

    say(f"Preview on {preview_origin} (SCIO_PREVIEW_MODE=1)")
    preview = start_preview(preview_port)

    say(f"Shell on {shell_origin}")
    server = start_shell(shell_port, manifest, preview_origin)

    if "--serve" in sys.argv:
        print(f"\n  open {shell_origin}  (ctrl-c to stop)")
        try:
            preview.wait()
        except KeyboardInterrupt:
            pass
        preview.terminate()
        return 0

    try:
        say("Driving it in a browser")
        found = drive(shell_origin, preview_origin, OUT / "shots")
        found["changes"] = server.changes
    finally:
        preview.terminate()
        server.shutdown()

    # The load-bearing safety claim, checked rather than asserted: with the flag
    # off, the SAME app serves no bridge at all.
    say("Serving the same app WITHOUT preview mode")
    plain_port = free_port()
    plain = start_preview(plain_port, preview_mode=False)
    try:
        html = urllib.request.urlopen(
            f"http://127.0.0.1:{plain_port}/booking/new", timeout=60
        ).read().decode()
        found["shipped_has_bridge"] = ("__scio/bridge.js" in html) or ("__SCIO_SHELL_ORIGIN__" in html)
        found["shipped_has_ids"] = html.count("data-scio-id") > 0
        print(f"  bridge in the shipped HTML: {found['shipped_has_bridge']}")
        print(f"  ids still present:          {found['shipped_has_ids']}")
    finally:
        plain.terminate()

    if True:
        (OUT / "result.json").write_text(json.dumps(found, indent=2))
        report(found)
        return 0 if verdict(found) else 1


def verdict(found: dict) -> bool:
    return all(
        [
            "blocked" in found["dom_access"],
            "booking-form-submit" in found["first_marking"],
            "pkg_feature_booking" in found["first_marking"],
            len(found.get("markings", [])) >= 2,
            bool(found.get("refusal")),
            "Reserve our table" in found.get("button_after", ""),
            found.get("form_changed") is True,
            found.get("layout_untouched") is True,
            found.get("shipped_has_bridge") is False,
            found.get("shipped_has_ids") is True,
        ]
    )


def report(found: dict) -> None:
    say("What happened")
    print(f"  parent DOM access ....... {found['dom_access']}")
    print(f"  first marking ........... {found['first_marking'].splitlines()[0]}")
    print(f"  markings held ........... {len(found.get('markings', []))}")
    print(f"  uninstrumented click .... {'refused' if found.get('refusal') else 'NOT REFUSED'}")
    print(f"  change ..................\n{indent(found.get('change_result', ''))}")
    print(f"  button after reload ..... {found.get('button_after')!r}")
    print(f"  ids after change ........ {len(found.get('ids_after', []))} still present")
    print(f"  layout untouched ........ {found.get('layout_untouched')}")
    print(f"  bridge in shipped app ... {found.get('shipped_has_bridge')} (must be False)")
    say("VERDICT: " + ("round-trip works" if verdict(found) else "BLOCKED — see out/result.json"))


def indent(text: str) -> str:
    return "\n".join(f"      {line}" for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
