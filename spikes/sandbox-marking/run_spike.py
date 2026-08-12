#!/usr/bin/env python3
"""SPIKE — the end-to-end demonstration.

Start a sandbox -> serve the preview -> see it (screenshot + console) -> click a
point and resolve it to a package -> make a directed change -> prove nothing else
moved -> look again.

Run: python3 run_spike.py   (from spikes/sandbox-marking/)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sandbox.directed_change import (  # noqa: E402
    ChangeRequest,
    plan_directed_change,
    snapshot,
    verify_isolation,
)
from sandbox.inspector import PreviewInspector  # noqa: E402
from sandbox.local_docker import LocalDockerSandbox  # noqa: E402
from sandbox.local_process import LocalProcessSandbox  # noqa: E402
from sandbox.provider import SandboxProvider  # noqa: E402
from sandbox.resolver import Manifest  # noqa: E402

ROOT = Path(__file__).parent
APP_DIR = ROOT / "example-app"
OUT_DIR = ROOT / "out"


def heading(text: str) -> None:
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


def pick_provider() -> SandboxProvider:
    """Prefer a real container boundary; fall back to a process, loudly."""
    docker = LocalDockerSandbox()
    if docker.is_available():
        print("sandbox: LocalDockerSandbox (container)")
        return docker
    print("sandbox: LocalProcessSandbox — no Docker daemon reachable.")
    print("         NOTE: a process shares the host; this proves the mechanic, NOT isolation.")
    return LocalProcessSandbox()


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    results: dict[str, object] = {}
    manifest = Manifest.load(APP_DIR / "scio-manifest.json")
    tracked = manifest.all_files()

    provider = pick_provider()
    if not provider.is_available():
        print("FAIL: no sandbox provider available in this environment")
        return 1

    heading("1. Start the sandbox and serve the preview")
    started = time.time()
    handle = provider.start(APP_DIR, port=0)
    boot_s = time.time() - started
    print(f"preview at {handle.url}  (ready in {boot_s:.1f}s, kind={handle.kind})")
    results["boot_seconds"] = round(boot_s, 1)
    results["sandbox_kind"] = handle.kind

    try:
        inspector = PreviewInspector(handle.url)

        heading("2. See it — screenshot + console (the vision loop's senses)")
        point = inspector.center_of('[data-scio-id="booking-submit"]')
        print(f"'Book table' button sits at {point}")

        observation, by_point, by_selector = inspector.observe(
            OUT_DIR / "before.png",
            clicks=[point] if point else [],
            selectors=['[data-scio-id="booking-form-title"]', '[data-scio-id="site-header"]'],
        )
        print(f"title:      {observation.title!r}")
        print(f"screenshot: {observation.screenshot_path.name} "
              f"({observation.screenshot_path.stat().st_size} bytes)")
        print(f"console:    {len(observation.console)} message(s)")
        for message in observation.console:
            print(f"   [{message.type}] {message.text[:80]}  <- {message.url[-40:]}")
        print(f"all errors:  {observation.errors}")
        print(f"app errors:  {observation.app_errors}   (noise filtered)")
        print(f"clean:       {observation.clean}")
        results["console_before"] = [m.full for m in observation.console]
        results["all_errors_before"] = observation.errors
        results["app_errors_before"] = observation.app_errors
        results["console_clean_before"] = observation.clean

        heading("3. Click -> element -> package -> source location")
        hits = [("click at " + str(point), by_point[0])] if by_point else []
        hits += [("selector title", by_selector[0]), ("selector header", by_selector[1])]
        resolution_log = []
        for label, hit in hits:
            location = manifest.resolve(hit.scio_id) if hit.scio_id else None
            print(f"{label}:")
            print(f"   element  {hit.tag} data-scio-id={hit.scio_id!r} text={hit.text!r}")
            if location:
                print(f"   -> package {location.package}")
                print(f"   -> source  {location.file}:{location.line} ({location.component}) "
                      f"[{location.matched_by}]")
            resolution_log.append(
                {
                    "how": label,
                    "scio_id": hit.scio_id,
                    "package": location.package if location else None,
                    "source": f"{location.file}:{location.line}" if location else None,
                }
            )
        results["resolutions"] = resolution_log

        heading("4. Directed change — touch ONLY the marked element's package")
        before = snapshot(APP_DIR, tracked)
        request = ChangeRequest(
            scio_id="booking-submit",
            instruction="make the button say 'Reserve my table'",
            find="Book table",
            replace="Reserve my table",
        )
        package, edits = plan_directed_change(request, manifest, APP_DIR)
        print(f"marking '{request.scio_id}' -> {package}")
        print(f"instruction: {request.instruction}")
        print(f"files to edit: {', '.join(edits)}")
        provider.apply_change(handle, edits)

        heading("5. Isolation proof")
        proof = verify_isolation(APP_DIR, before, package, manifest)
        print(proof.summary())
        print(f"\nisolated: {proof.isolated}")
        results["isolation"] = {
            "target_package": proof.target_package,
            "changed": proof.changed_files,
            "unchanged_count": len(proof.unchanged_files),
            "violations": proof.violations,
            "isolated": proof.isolated,
        }

        diff = subprocess.run(
            ["git", "diff", "--stat", "--", str(APP_DIR.relative_to(ROOT.parent.parent))],
            cwd=ROOT.parent.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        print("\ngit diff --stat:")
        print(diff.stdout or "(no tracked changes yet — files are new to git)")

        heading("6. Look again — the change is live, the rest is intact")
        after, _, after_selectors = inspector.observe(
            OUT_DIR / "after.png",
            selectors=['[data-scio-id="booking-submit"]', '[data-scio-id="site-header"]'],
        )
        print(f"button now reads: {after_selectors[0].text!r}")
        print(f"header still reads: {after_selectors[1].text!r}")
        print(f"console: {len(after.console)} message(s); app errors: {after.app_errors}; clean={after.clean}")
        results["button_after"] = after_selectors[0].text
        results["header_after"] = after_selectors[1].text
        results["console_clean_after"] = after.clean

        heading("7. Restore the example app")
        restore = {relative: content for relative, content in
                   ((r, (APP_DIR / r).read_text().replace("Reserve my table", "Book table"))
                    for r in edits)}
        provider.apply_change(handle, restore)
        print("example-app restored to its committed state")

    finally:
        provider.stop(handle)
        print("\nsandbox stopped")

    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
    print(f"\nresults written to {OUT_DIR / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
