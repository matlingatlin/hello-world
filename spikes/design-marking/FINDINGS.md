# Spike findings — the in-iframe marking bridge

**Date:** 2026-08-12 · **De-risks:** gate 2 (the design window) · **Status:** spike complete
**Verdict: the bridge works, end to end. Build gate 2 on it — the parent must never try to
reach into the preview, and the preview must never decide what a marking means.**

Everything below was run in this environment. Reproduce with:

```bash
python3 run_spike.py          # the whole chain, in a real browser
python3 run_spike.py --serve   # bring both origins up and click it yourself
python3 -m pytest tests/ -q    # the payload seam, no browser (8 tests)
```

---

## What was proven

| # | Claim | Result |
|---|---|---|
| 1 | The parent genuinely **cannot** read into the preview's DOM | ✅ `SecurityError` — so a bridge is not optional |
| 2 | A click inside the iframe reaches the parent | ✅ `postMessage`, origin-pinned both ways |
| 3 | The parent resolves it to `data-scio-id` → package → **source line** | ✅ `booking-form-submit` → `pkg_feature_booking` @ `components/booking-form.tsx:70` |
| 4 | Several markings, each with its own note | ✅ 2 held, notes attached per marking |
| 5 | An uninstrumented element is **refused**, not resolved to its ancestor | ✅ names `booking-form` as evidence, never as the answer |
| 6 | A directed change touches only the marked package | ✅ 2 files changed, **7 byte-identical**, `layout.tsx` untouched |
| 7 | The change is visible after a real frame reload | ✅ "Book a table" → "Reserve our table", 13 ids intact |
| 8 | The bridge is **absent** from the app the user receives | ✅ flag off → no script, ids still present |

Screenshots: `out/shots/`. Raw result: `out/result.json`.

## Timings (this fixture, this machine)

| leg | time |
|---|---|
| `next dev` boot | 7.4 s |
| **click → resolved marking on screen** | **150 ms** |
| directed change + isolation proof (mechanical) | 0.07 s |
| frame reload → change visible | < 1 s |

The interactive part is comfortably interactive. The slow leg in the real product will be the
LLM regeneration between those last two rows — everything the spike measured is noise beside it.

---

## The three findings that shape gate 2

### 1. The bridge is load-bearing, and the reason is worth stating precisely

The shell tries `iframe.contentDocument` on every load and prints the result. It gets:

```
SecurityError: Failed to read a named property 'document' from 'Window': Blocked a frame …
```

Different port = different origin, and the preview will always be on its own origin (its own
sandbox). So **no amount of cleverness in the parent gets a `data-scio-id`.** Everything the
design window knows about what the user marked has to be sent out from inside the preview.

That makes the bridge a *product surface*, not a helper: if it is missing or broken, marking is
not degraded, it is impossible.

### 2. The preview reports; the parent decides — and that split is what keeps the old bug dead

The sandbox-marking spike (B039) found that a click on an uninstrumented element walked up to
the nearest instrumented ancestor and resolved *confidently* to the wrong package — a marked
button would have rewritten the app shell.

The bridge could easily have re-introduced that bug, because the fall-through is natural to
write in JavaScript. It does not: `describe()` reports the clicked node **and**, separately, the
nearest instrumented ancestor, and never substitutes one for the other. The decision is made in
Python by `core/resolver.resolve_marking`, which raises. Clicking an uninstrumented `<div>` in
the preview produced, in the shell:

> The element you marked (`<div>`) has no data-scio-id. Its ancestor 'booking-form' does
> (package pkg_feature_booking), but resolving to an ancestor would target the wrong part of the
> app — the spike proved this rewrites the shell instead of the marked element. This element
> needs instrumentation.

**Carry forward:** the bridge must stay dumb. Any "helpfulness" added to it — nearest match,
best guess, closest ancestor — reopens B039's bug on the far side of a security boundary where
the guardrail cannot see it.

### 3. Coordinates do not survive the crossing — so the preview must draw its own marker

The click coordinates the bridge captures are in the **preview's** viewport, with the preview's
own scroll position. The parent's viewport is a different coordinate space, and the parent
cannot read the frame's scroll offset (finding 1). Any attempt to draw a highlight from the
parent onto the iframe would be guesswork that drifts the moment anyone scrolls.

So the marker is drawn **inside** the preview, by the bridge, from the element's own
`getBoundingClientRect()`. It is always exactly right, and it costs the parent nothing. The
coordinates still travel in the payload, but only as provenance ("you clicked here"), never as
something the parent renders.

A cosmetic wrinkle worth handling in gate 2: the marker's label is drawn 20 px above its box, so
labels collide when two marked elements are close together. Offset or flip them.

---

## Smaller things the spike ran into

- **Escape everything the preview sends.** A refusal message containing `<div>` was interpolated
  into the shell's `innerHTML` and *became a div* — the tag vanished from the message. In the
  real product the payload also carries generated `innerText`, so this is untrusted input from a
  second origin. The stub now escapes; gate 2 should render through the framework rather than
  string-building.
- **Pin the origin in both directions.** The bridge posts to exactly the shell origin, never
  `"*"`, and ignores messages that are not from it; the shell checks `event.origin` before
  reading anything. A wildcard here would broadcast the app's structure to any page that
  framed the preview.
- **Marking must suppress the app's own behaviour.** The preview is a working app: the first
  version of the bridge submitted the booking form while marking it. The bridge now
  `preventDefault()`s while armed — and arming is explicit, so an unarmed preview is just an app.
- **Reload, do not hot-update.** The shell re-points the iframe `src` after a change. Next's fast
  refresh would also have shown it, but a reload proves the change is in the *served app* rather
  than in a React tree, which is the claim the reveal makes to the user.
- **"Selected" must be explicit.** The stub applies the change to the most recent successful
  marking. With several markings on screen that is a guess; gate 2 needs the user to pick.

---

## What to carry into gate 2

1. **The bridge ships as preview-mode-only code, injected by the sandbox, not by a build.** One
   conditional in the layout on `SCIO_PREVIEW_MODE`; verified here that with the flag off the
   served HTML contains no bridge while every `data-scio-id` is still there.
2. **The payload shape is `core.resolver.ElementHit`** plus coords/route. Keeping it identical to
   the existing dataclass meant the shell had nothing to translate, and no place to soften a
   refusal.
3. **Resolution and change stay server-side.** The browser sends a hit; the engine resolves,
   regenerates, proves isolation and hands back a summary. The design window renders that
   summary — it never computes it.
4. **Show the refusal as a first-class outcome.** "Could not address this — this element needs
   instrumentation" is a real answer with a real next step, and it is what stops the wrong
   package being rewritten. It should look like a normal state in the UI, not an error banner.
5. **A directed change may legitimately touch several files.** This one edited both
   `booking-form.tsx` and `booking/new/page.tsx` — the heading and the button shared a string,
   and both belong to the marked package. Isolation is per *package*, not per file; the reveal
   should say which files moved.

## What this spike did NOT settle

- **Real regeneration.** The change here is a find/replace (`MechanicalRegenerator`). Whether an
  LLM, given a marking plus a note, edits the right thing and preserves every id is B041's
  question, not this one.
- **Marking in a scrolled or responsive frame.** Everything was above the fold at one viewport.
- **Several markings applied as one change.** The stub applies one; batching notes into a single
  regeneration is a gate-2 design decision.
- **The sandbox boundary.** This ran `next dev` as a local process (`LocalProcessSandbox`), which
  is not an isolation boundary. On a real sandbox the origin is still different, so the bridge
  argument is unchanged — but serving `public/__scio/bridge.js` has to be arranged by whatever
  provider runs the preview.
