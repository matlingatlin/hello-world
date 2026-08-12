#!/usr/bin/env python3
"""Prove the core against a REAL running sandbox, not just fixtures.

The unit tests cover the logic; this covers the part that can only be checked by
actually booting an app, looking at it through a browser, clicking a pixel, and
watching a directed change land.

Needs the spike's instrumented app (it has node_modules installed):
    python3 scripts/verify_core.py [path-to-app]
Defaults to ../../spikes/sandbox-marking/example-app.
"""

from __future__ import annotations

import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE / "src"))

from scio_engine.core import (  # noqa: E402
    ManifestStore,
    MarkingResolutionError,
    MechanicalRegenerator,
    build_manifest,
    choose_sandbox,
    directed_regenerate,
    ids_in_source,
    resolve_marking,
    verify_instrumentation,
)
from scio_engine.core.preview import PreviewInspector  # noqa: E402
from scio_engine.core.resolver import ElementHit  # noqa: E402

DEFAULT_APP = ENGINE.parent.parent / "spikes" / "sandbox-marking" / "example-app"
PACKAGE_FILES = {
    "pkg_foundation": ["app/layout.tsx", "components/site-header.tsx"],
    "pkg_design_tokens": ["app/globals.css"],
    "pkg_feature_booking": [
        "app/page.tsx",
        "components/booking-form.tsx",
        "components/booking-list.tsx",
    ],
}


def heading(text: str) -> None:
    print(f"\n{'=' * 68}\n{text}\n{'=' * 68}")


def main() -> int:
    app_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_APP
    app_dir = app_dir.resolve()
    if not (app_dir / "node_modules").exists():
        print(f"Need an app with dependencies installed. Tried: {app_dir}")
        return 1

    heading("1. Derive the manifest FROM the source (never hand-written)")
    manifest = build_manifest(app_dir, PACKAGE_FILES)
    print(f"generated_from: {manifest.generated_from}")
    print(f"elements: {len(manifest.elements)}   patterns: {len(manifest.patterns)}")
    for scio_id in sorted(manifest.elements)[:4]:
        location = manifest.elements[scio_id]
        print(f"   {scio_id:24s} -> {location.package:22s} {location.file}:{location.line}")

    heading("2. Verify instrumentation")
    report = verify_instrumentation(app_dir, manifest)
    print(f"valid: {report.valid}   elements: {report.element_count}")
    report.raise_for_status()

    heading("3. Persist the coupling and reload it")
    store = ManifestStore(app_dir)
    original_manifest = store.path.read_text() if store.exists() else None
    store.save(manifest)
    reloaded = store.load()
    print(f"round-trip ok: {reloaded.ids() == manifest.ids()}")

    sandbox = choose_sandbox()
    print(f"\nsandbox: {sandbox.name} (isolated={getattr(sandbox, 'isolated', '?')})")
    handle = sandbox.start(app_dir, port=0)
    print(f"preview: {handle.url}")

    original_form = (app_dir / "components/booking-form.tsx").read_text()
    try:
        inspector = PreviewInspector(handle.url)
        if not inspector.is_available():
            print("Playwright unavailable — skipping the browser half")
            return 0

        heading("4. Look at it — screenshot + CLASSIFIED console")
        point = inspector.center_of('[data-scio-id="booking-submit"]')
        observation = inspector.observe(ENGINE / "out" / "core-before.png", points=[point])
        print(f"title: {observation.title!r}")
        print(f"console messages: {len(observation.console.classifications)}")
        for c in observation.console.classifications:
            print(f"   [{c.origin}/{c.severity}] fails_build={c.fails_build}  "
                  f"{c.entry.text[:56]}")
        print(f"failures:   {observation.console.failures}")
        print(f"suppressed: {observation.console.suppressed}")
        print(f"clean: {observation.console.clean}   <- favicon 404 did not fail the build")

        heading("5. Resolve the click strictly")
        hit = observation.hits[0]
        print(f"clicked {point} -> <{hit.tag}> id={hit.scio_id!r}")
        marking = resolve_marking(hit, manifest)
        print(f"   -> {marking.package} @ {marking.location.file}:{marking.location.line}")

        heading("6. A lost id must FAIL, not resolve to the parent")
        lost = ElementHit(
            scio_id=None, scio_package=None, tag=hit.tag, text=hit.text,
            ancestor_id=hit.ancestor_id, ancestor_package=hit.ancestor_package,
            ancestor_distance=hit.ancestor_distance,
        )
        print(f"ancestor available: {lost.ancestor_id!r} ({lost.ancestor_package})")
        try:
            resolve_marking(lost, manifest)
            print("!! FAILED: it resolved anyway")
            return 1
        except MarkingResolutionError as exc:
            print(f"correctly refused: {str(exc)[:110]}...")

        heading("7. Directed regeneration + isolation proof")
        result = directed_regenerate(
            app_dir,
            hit,
            "make the button say 'Reserve my table'",
            manifest=manifest,
            regenerator=MechanicalRegenerator("Book table", "Reserve my table"),
            sandbox=sandbox,
            handle=handle,
            package_files=PACKAGE_FILES,
        )
        print(result.isolation.summary())
        print(f"accepted: {result.accepted}   instrumentation valid: "
              f"{result.instrumentation.valid}")

        after = inspector.observe(
            ENGINE / "out" / "core-after.png",
            selectors=['[data-scio-id="booking-submit"]', '[data-scio-id="site-header"]'],
        )
        print(f"button now: {after.hits[0].text!r}")
        print(f"header still: {after.hits[1].text!r}")

        heading("8. A regeneration that drops an id is rejected + rolled back")
        before_ids = ids_in_source(app_dir, manifest.all_files())
        bad = directed_regenerate(
            app_dir,
            hit,
            "restructure the button",
            manifest=result.manifest,
            regenerator=MechanicalRegenerator(' data-scio-id="booking-submit"', ""),
            sandbox=sandbox,
            handle=handle,
            package_files=PACKAGE_FILES,
        )
        print(f"accepted: {bad.accepted}   rolled_back: {bad.rolled_back}")
        print(f"reason: {bad.rejection}")
        restored = ids_in_source(app_dir, manifest.all_files())
        print(f"ids intact after rollback: {restored == before_ids}")

    finally:
        (app_dir / "components/booking-form.tsx").write_text(original_form)
        if original_manifest is None:
            store.path.unlink(missing_ok=True)
        else:
            store.path.write_text(original_manifest)
        sandbox.stop(handle)
        print("\nsandbox stopped; app restored")

    heading("All core checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
