#!/usr/bin/env python3
"""SPIKE experiment — do stable IDs survive a regeneration?

The kickoff names this as the biggest carried-forward risk, so rather than
speculate we reproduce the failure mechanically. Two regenerations of the same
component are written by hand, in the two shapes a model plausibly returns:

  A. restructured markup, ids preserved   (what we need)
  B. restructured markup, ids dropped     (what happens if the prompt doesn't insist)

Then we re-resolve the same marking against each and report what breaks.

Run: python3 experiment_id_stability.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sandbox.inspector import PreviewInspector  # noqa: E402
from sandbox.local_process import LocalProcessSandbox  # noqa: E402
from sandbox.resolver import Manifest, UnknownElementError  # noqa: E402

ROOT = Path(__file__).parent
APP_DIR = ROOT / "example-app"
TARGET = "components/booking-form.tsx"

# A: the model rewrote the button (wrapped it, changed the class, reordered
# attributes) but kept data-scio-id — the outcome the playbook must enforce.
REGEN_IDS_KEPT = '''"use client";

// Regenerated (variant A): markup restructured, identity preserved.
import { useState } from "react";

const SLOTS = ["18:00", "18:30", "19:00", "19:30"];

export function BookingForm() {
  const [slot, setSlot] = useState("18:30");

  return (
    <section className="card" data-scio-package="pkg_feature_booking" data-scio-id="booking-form">
      <header>
        <h1 data-scio-id="booking-form-title" data-scio-package="pkg_feature_booking">
          Book a table
        </h1>
        <p className="sub" data-scio-id="booking-form-subtitle" data-scio-package="pkg_feature_booking">
          Bistro Nord · pick a time
        </p>
      </header>

      <div className="fields">
        <label htmlFor="date">Date</label>
        <div className="field" id="date" data-scio-id="booking-field-date" data-scio-package="pkg_feature_booking">
          Fri, 8 Aug
        </div>
        <label htmlFor="party">Party size</label>
        <div className="field" id="party" data-scio-id="booking-field-party" data-scio-package="pkg_feature_booking">
          2 guests
        </div>
      </div>

      <label>Time</label>
      <div className="slots" data-scio-id="booking-slots" data-scio-package="pkg_feature_booking">
        {SLOTS.map((value) => (
          <button
            key={value}
            className="slot"
            data-on={value === slot}
            data-scio-id={`booking-slot-${value}`}
            data-scio-package="pkg_feature_booking"
            onClick={() => setSlot(value)}
          >
            {value}
          </button>
        ))}
      </div>

      <div className="actions">
        <button
          className="book"
          data-scio-id="booking-submit"
          data-scio-package="pkg_feature_booking"
          onClick={() => console.log(`[booking] create_booking at ${slot}`)}
        >
          Book table
        </button>
      </div>
    </section>
  );
}
'''

# B: the same restructuring, but the model dropped the instrumentation —
# markup a human would call correct, and the design window can no longer
# address a single element in it.
REGEN_IDS_DROPPED = REGEN_IDS_KEPT.replace(
    "// Regenerated (variant A): markup restructured, identity preserved.",
    "// Regenerated (variant B): markup restructured, identity LOST.",
)
for _attr in (
    ' data-scio-id="booking-submit"',
    ' data-scio-id="booking-form-title"',
    ' data-scio-id="booking-form"',
):
    REGEN_IDS_DROPPED = REGEN_IDS_DROPPED.replace(_attr, "")


def probe(app_dir: Path, label: str, manifest: Manifest) -> dict:
    """Boot the app in the given state and try to address the submit button."""
    sandbox = LocalProcessSandbox()
    handle = sandbox.start(app_dir, port=0)
    try:
        inspector = PreviewInspector(handle.url)
        point = inspector.center_of("button.book")  # find it visually, as a user would
        observation, by_point, _ = inspector.observe(
            ROOT / "out" / f"id-stability-{label}.png", clicks=[point] if point else []
        )
        hit = by_point[0] if by_point else None
        scio_id = hit.scio_id if hit else None

        resolved = None
        error = None
        if scio_id:
            try:
                location = manifest.resolve(scio_id)
                resolved = f"{location.package} @ {location.file}:{location.line}"
            except UnknownElementError as exc:
                error = str(exc)
        else:
            error = "the clicked element carries no data-scio-id"

        return {
            "label": label,
            "clicked_at": point,
            "scio_id": scio_id,
            "resolved": resolved,
            "error": error,
            "app_errors": observation.app_errors,
        }
    finally:
        sandbox.stop(handle)


def main() -> int:
    manifest = Manifest.load(APP_DIR / "scio-manifest.json")
    (ROOT / "out").mkdir(exist_ok=True)
    original = (APP_DIR / TARGET).read_text()

    print("=" * 70)
    print("Do stable IDs survive a regeneration?")
    print("=" * 70)

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        backup = Path(tmp) / "booking-form.tsx"
        shutil.copy(APP_DIR / TARGET, backup)
        try:
            results.append(probe(APP_DIR, "baseline", manifest))

            (APP_DIR / TARGET).write_text(REGEN_IDS_KEPT)
            results.append(probe(APP_DIR, "regen-ids-kept", manifest))

            (APP_DIR / TARGET).write_text(REGEN_IDS_DROPPED)
            results.append(probe(APP_DIR, "regen-ids-dropped", manifest))
        finally:
            (APP_DIR / TARGET).write_text(original)
            print("\nexample-app restored\n")

    for result in results:
        print(f"--- {result['label']}")
        print(f"    clicked at      {result['clicked_at']}")
        print(f"    element id      {result['scio_id']!r}")
        print(f"    resolves to     {result['resolved'] or '— NOT ADDRESSABLE —'}")
        if result["error"]:
            print(f"    error           {result['error'][:100]}")
        print()

    # The verdict is NOT "did it resolve" — a click that falls through to an
    # ancestor still resolves, just to the wrong package. Compare against the
    # baseline instead.
    baseline, kept, dropped = results
    kept_ok = kept["scio_id"] == baseline["scio_id"] and kept["resolved"] == baseline["resolved"]
    dropped_ok = (
        dropped["scio_id"] == baseline["scio_id"] and dropped["resolved"] == baseline["resolved"]
    )

    print("=" * 70)
    print(f"ids preserved  -> same element, same package : {'YES' if kept_ok else 'NO'}")
    print(f"ids dropped    -> same element, same package : {'YES' if dropped_ok else 'NO'}")
    if not dropped_ok:
        print()
        print("  How it failed matters more than that it failed:")
        print(f"    expected {baseline['scio_id']!r} -> {baseline['resolved']}")
        print(f"    got      {dropped['scio_id']!r} -> {dropped['resolved']}")
        print("  The click did not error. It walked up to the nearest instrumented")
        print("  ancestor and resolved to the WRONG package — a directed change would")
        print("  have edited the app shell instead of the button the user marked.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
