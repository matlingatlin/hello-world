# Spike findings — sandbox + marking→code

**Date:** 2026-08-09 · **Backlog:** B039 · **Status:** spike complete, mechanic proven
**Verdict: the mechanic is sound. Build it — with two guardrails that this spike showed are
not optional.**

Everything below was actually run in this environment. Where something could not be run,
it says so.

---

## What was proven

| # | Claim | Result |
|---|---|---|
| 1 | A sandbox can run generated code and serve a live preview | ✅ ready in **6.7–7.8 s** |
| 2 | We can capture a screenshot + console from the running preview | ✅ 30 KB PNG, console with source URLs |
| 3 | A **click** resolves to the right element → package → source line | ✅ exact hit, no ambiguity |
| 4 | A directed change touches **only** the target package | ✅ 1 file changed, **5 byte-identical** |
| 5 | The change is live and the rest of the app is intact | ✅ button changed, header untouched |

Reproduce: `python3 run_spike.py` (full chain) and `python3 experiment_id_stability.py`
(the regeneration experiment). `pytest tests/` covers the targeting logic without a browser
— 16 tests, all green.

---

## The two findings that change how we build this

### 1. A lost ID does not fail loudly — it silently edits the wrong package

This is the most important thing the spike found, and it was not what I expected to find.

The experiment regenerated one component twice: once preserving `data-scio-id`, once
dropping it (markup a human reviewer would call perfectly correct either way). Clicking the
same pixel:

| Regeneration | Element resolved | Package resolved |
|---|---|---|
| baseline | `booking-submit` | `pkg_feature_booking` @ `booking-form.tsx:47` |
| ids preserved | `booking-submit` | `pkg_feature_booking` @ `booking-form.tsx:47` ✅ |
| **ids dropped** | **`main`** | **`pkg_foundation` @ `layout.tsx:13`** ❌ |

The click did not error. `elementFromPoint` walked up to the nearest instrumented ancestor
and resolved confidently to the **wrong package**. A directed change would then have
rewritten the app shell because the user marked a button.

**Carry forward — two defences, both required:**
- **Emit the manifest from the builder, not from prose.** The builder knows which package it
  is writing; the manifest must be its output, so an id can never drift from its package.
- **Verify instrumentation after every regeneration, before accepting it.** Compare the
  post-regen id set against the pre-regen set; a disappeared id is a failed build, not a
  silent success. Cheap to check, catastrophic to miss.

Fallthrough itself should also be explicit: if the resolved element is an *ancestor* of what
was clicked rather than the clicked node, treat it as "could not address this" and say so,
rather than acting on the ancestor.

### 2. The vision loop cannot read "any console error" as failure

Every page load logged this error:

```
Failed to load resource: the server responded with a status of 404 (Not Found)
```

It is a missing `/favicon.ico`. Nothing to do with the generated app. A critique agent
treating console errors as build failures would fail **every build ever made**.

Worse, the message **text names nothing** — classification is only possible via the
message's source URL, which is why `ConsoleMessage` now carries `url`. Filtering on text
alone is impossible.

**Carry forward:** the critique agent judges `app_errors` (noise filtered by source), never
raw `errors`. Keep the noise list short and justified — a filter that grows loose will one
day hide a real failure. The spike's list is three entries; treat additions as decisions.

---

## Smaller things worth knowing

- **Dependencies must be complete before the sandbox starts.** The first run died because
  Next.js auto-installed TypeScript mid-boot and then crashed on its own require hook. The
  sandbox image must ship a fully installed dependency set; no install-on-first-boot.
- **Point-clicks resolve as well as selectors**, provided the walk-up-to-ancestor step
  exists — a click usually lands on a text node, not the marked element.
- **Loop-rendered elements need patterns, not exact entries.** Four time-slot buttons share
  one source location; the manifest matches `booking-slot-*` and the id carries the
  instance key. Real apps are full of lists, so this is the common case, not the exception.
- **Hash-based isolation proof works and is cheap.** Snapshot the tracked files, apply the
  change, re-hash: any file that moved outside the target package is a violation. It should
  run on every directed change in production, not just in a spike.
- **Hot reload made the change visible without a restart** — good for the design window's
  feel, but it means "the preview updated" is not evidence the change compiled cleanly.
  The vision loop still has to look.

---

## What this spike did NOT prove

Being explicit, because the gap matters:

- **Isolation.** Docker's CLI is installed here but no daemon is reachable, so the sandbox
  ran as a **local `next dev` process**, behind the same `SandboxProvider` interface. That
  proves the *mechanic*; it proves nothing about safely running untrusted generated code.
  `LocalDockerSandbox` is written but has never been executed — treat it as a sketch.
- **ACA at scale.** No Azure here. Session pool behaviour, prewarm latency, concurrency
  limits and cost under many parallel projects are all unmeasured. The 6.7 s boot is a warm
  local process and should not be read as an ACA number.
- **Real LLM regeneration.** The directed edit was a mechanical string swap. What the spike
  tested is the *targeting*; whether a model preserves ids while rewriting is exactly the
  risk finding #1 covers, and it needs a real run against a real model.
- **Playwright inside the sandbox.** The browser ran on the host against the preview URL. In
  production the question is whether Playwright runs *inside* the ACA session or beside it —
  unresolved, and it affects both the container image and the cost model.
- **Anything at scale.** One tiny app, one page, eleven instrumented elements.

---

## Recommendation for the real build (B040)

1. Keep the `SandboxProvider` interface as it stands; add `AcaSandbox` behind it. The
   fallback path in this spike is evidence the seam is in the right place.
2. Make the manifest a **build artifact of each package**, and validate it after every
   generation and regeneration (finding #1).
3. Ship the console-noise filter with the vision loop from day one, classified by source
   URL (finding #2), and make the noise list a reviewed file rather than an inline constant.
4. Run the isolation proof on every directed change in production — it is a few hashes and
   it is the only thing that actually enforces the promise.
5. Spike ACA separately and early: prewarm latency, concurrency, cost, and where Playwright
   runs. That is the remaining unknown, and it is a cost/scale unknown rather than a
   feasibility one.

---

## Layout

```
spikes/sandbox-marking/
  sandbox/provider.py         SandboxProvider interface + handle
  sandbox/local_process.py    the implementation that ran here (next dev)
  sandbox/local_docker.py     container implementation — written, NEVER RUN
  sandbox/inspector.py        Playwright: screenshot, console, click→element
  sandbox/resolver.py         manifest: scio-id → package + source location
  sandbox/directed_change.py  targeting + the hash-based isolation proof
  example-app/                instrumented Next.js booking app + scio-manifest.json
  run_spike.py                the end-to-end demonstration
  experiment_id_stability.py  the regeneration experiment behind finding #1
  tests/test_mechanic.py      16 fast tests for the targeting logic
  out/                        screenshots + results.json from the last run
```
