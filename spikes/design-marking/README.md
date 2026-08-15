# Spike — the in-iframe marking bridge

One question, answered cheaply: **can a user mark an element inside the embedded preview, have
the design window resolve it to its `data-scio-id` + package, and round-trip a directed change
back?**

Read `FINDINGS.md` for the verdict. This file is how to run it.

```bash
python3 run_spike.py           # the whole chain in a real browser, prints a verdict
python3 run_spike.py --serve    # bring both origins up and click it yourself
python3 -m pytest tests/ -q     # the payload seam, no browser
```

## What it puts together

```
    preview  http://127.0.0.1:A      shell  http://127.0.0.1:B
    ─────────────────────────        ──────────────────────────
    the booking blueprint            iframe + message listener
    + bridge.js (preview mode)  ──▶  /resolve  → core.resolver (strict)
                                ◀──  /change   → core.regenerate (isolated)
```

Two ports means two origins, which is the real condition: the parent cannot read into the frame,
so marking has to be sent out from inside it.

| | |
|---|---|
| `preview/bridge.js` | the injected annotation script — captures clicks, draws the marker, postMessages out |
| `shell/index.html` | the design-window stub — iframe, markings list, notes, change button |
| `run_spike.py` | assembles the fixture, serves both origins, drives it in Chromium, prints the verdict |
| `tests/` | the bridge→resolver seam without a browser |
| `app/`, `out/` | generated; gitignored |

## Fixture

The booking blueprint from `spikes/local-data/app` — the engine's own adapter output, already
instrumented, with 294 MB of `node_modules` this spike symlinks rather than reinstalls. It is
copied (never modified in place), stamped with `data-scio-package` by the real
`core.stamping.stamp_files`, and its manifest derived by the real `core.manifest_builder`.

## What is real and what is a stand-in

**Real:** the instrumentation contract, `build_manifest`, `resolve_marking` (including every
refusal), `directed_regenerate`, `verify_isolation`, the instrumentation re-verification, a real
Next dev server, a real browser, two real origins.

**Stand-in:** the change itself is a find/replace (`MechanicalRegenerator`) — no LLM. The shell is
a single HTML file with no framework, and its "selected marking" is just the last successful one.

Nothing here is wired into `apps/*`, and nothing here should be.
