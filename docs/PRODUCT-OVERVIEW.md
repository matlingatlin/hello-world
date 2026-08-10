# Scio — Product overview (the whole, refined)

**In one sentence:** the user gives their input, and out comes a professionally built app,
website, or automation — code they own.

This is the synthesised product vision. It ties together the three gates and everything around
them. It is the reference the technical architecture (agents/models) is built to serve, and it
sits above the detail docs (PRD, UX-FLOW, DATA-MODEL, INTAKE-SCHEMA, LAYER-A/B, decisions).

## The model: one engine, three gates
Scio is **one engine run in three modes**, not three systems. All three gates share the same
brain (A -> B -> C), the same sandbox, the same marking->code core, the same matrix + multi-pass
relay, and the same vision loop. This is what makes quality consistent and the whole coherent.

- **Gate 1 — Input.** A conversational agent (a wizard in dialogue form) works against a
  checklist: it knows what information it needs, ticks the list off, and asks new questions until
  it can. When the list is satisfied ("buildable enough"), the input is captured. (= Layer A.)
- **Gate 2 — Preview / design.** From the captured input, generate a professional, *runnable*
  preview (real code, not mockups) shown in a smart "design window" with a prompt field and
  visual tools (mark, draw, annotate each marking). It handles: prompt changes, visual marking
  changes, both at once, or none (proceed). On "Generate again" it PRESERVES everything not
  annotated, interprets what to change, regenerates in a directed way, and re-shows. Supports
  going back (undo/versions) inside the window. This needs the FULL A->B->C brain — no shortcut.
  (= Layer B heavily involved.)
- **Gate 3 — Build.** Take the approved input contract + the approved preview/code and EXTEND
  it (not a restart) into a finished, professional app: fill out and harden, testing continuously
  (the vision loop, per build package). Show it in the design window, now FULLY TESTABLE as the
  real running app. Then a final packaging step. (= Layer C + the builder.)

What passes between gates is the **contract + code**, never a picture — so the final product
matches what was approved, by construction. Anything that conflicts with the contract is
**flagged and asked**, never silently built.

## The shared core (built once, used by all gates)
- **A -> B -> C brain.** A: intake schema (checklist, typed, metadata). B: understanding (the
  whole) + a machine-readable architecture graph + the generation playbook, validated by rules
  before generation. C: decompose the architecture into a dependency-ordered graph of small,
  contract-bearing build packages.
- **Sandbox.** Every runnable preview / app runs in an isolated sandbox (ADR-0005). This is the
  heaviest, most cost-driving piece — and gate 2 and gate 3 share it.
- **Marking -> code.** Every visual element is tied to its code / build package, so a change is
  a *directed* regeneration of just that part. This coupling is the hardest single piece, and it
  is shared by preview, build, and post-delivery editing.
- **Matrix + multi-pass relay.** Pick the best models per task; run pass 1 (best) -> review/
  rewrite/complement passes -> final pass (best). More passes on hard packages, fewer on easy.
- **Vision loop.** Build a package -> run it -> verify against its contract -> fix -> next.

## Lifecycle & persistence
- **After delivery is not a new mode.** Returning to a project drops you back into the design
  window with your running app; gates 2/3 simply run again on a living project. The whole and the
  contract persist between visits, so a change months later still knows what it must not break.
- **Editing the delivered app** uses the same marking->code tool. That requires the coupling and
  the contract to be **saved with the project** (git + DB), not just held during a session.
- **Accounts/projects are the frame, not the magic** — but they make the magic persistent. A
  workspace is the tenant boundary; a project is the container for a journey through the gates and
  holds everything the gates produce (spec/design/build versions, code, coupling). Every gate
  transition is saved; you can leave mid-way and return exactly where you were.
- **Git holds the code; the DB holds the state/contracts.** That split is what makes the app
  truly yours (real code you can take) AND lets Scio keep the whole (contracts in the DB).
- **Versions are one timeline.** A small preview tweak and a big build step are the same kind of
  save point — human-described ("before the table map"), backed by real git commits,
  non-destructive (restore adds a point on top, deletes nothing), returnable anytime.

## Reference uploads ("show, don't just tell")
An input channel in gate 1 AND gate 2: attach documents, images, etc., tag what each is (a
colour, a font, a layout, a doc), and the engine extracts the concrete thing (hex from a colour
image, the font, requirements from a doc) into spec fields / design tokens. Stored as a
per-project, retrievable RAG the engine pulls from during the build. Tenant-isolated and treated
as untrusted input (scanned, size/type checked).

## Cost & budget (so the economics work)
Controlled on three levels: LLM (configurable pass-count, directed regeneration, caching),
sandbox (idle timeout, concurrency caps, aggressive stop), and budget (metering ->
warn -> pause at the cap; never a surprise bill).
- **Estimate at the spec gate**, as a range, explicitly "for the base build, without changes"
  ("building the base: ~X; each change you make after adds"). Derived from the build plan's
  package count + expected passes + sandbox time.
- **Live counter** while working ("base + 3 changes = ~Y so far"), so cost never sneaks up.
- A professional app in hours may cost real money — that's fine; directed regeneration is what
  keeps the margin, not a way to cut corners.

## When a build fails
The vision loop has a cap; a failure = the cap is reached and a package still doesn't meet its
contract. It happens sometimes (a flaky integration, a contradiction surfacing at runtime).
The response: **isolate** (thanks to Layer C, one package fails, not the app — "9 of 10 parts
work"), **be honest and exact** (which package, what was expected, what happened, where in the
code), and **always give a way forward** (let the user re-steer that part; deliver the working
rest with the broken part clearly marked "needs a look"; worst case, hand over the clean code +
exactly where the problem is). Never silent, never total. Lean: build what you can, collect the
broken parts, and show everything honestly at the reveal rather than stopping at the first problem.

## Security (where "professional, not a leaky prototype" lives)
Structural on five levels, never a checklist at the end:
1. The locked stack — Supabase row-level security enforces data access at the database, not in
   app code the LLM might slip on.
2. The generation playbook — secure defaults (RLS on, input validation, authz on protected
   operations, no secrets in code) inherited by every build package.
3. Derived from input — the sensitivity field sets the security posture deterministically.
4. Verified, not assumed — the vision loop + a security validation agent check for leaks, missing
   access controls, keys in code, and fix them in the loop.
5. Tenant isolation — our own platform isolates each workspace's projects and uploads.
Honest limit: we guarantee secure defaults and catch common holes to a high baseline; we don't
promise every possible app is invulnerable. Status shows what was checked.

## Wait / build UX
A professional build with testing takes minutes to ~an hour. Make it feel like a professional at
work: show real, plain-language progress calmly (real "9 of 12 parts done", not a fake bar — no
scary logs); don't lock the user in (build in the background, notify when done); set expectations
up front (the time estimate). The long wait is mainly the *first* build; changes (directed
regeneration) are seconds-to-a-minute, so iterating feels fast. Be honest about time, never fake it.

## The three types: app + website + automation
One machine, three types. Everything is shared EXCEPT gate 2's preview surface, which is
**type-aware**:
- **App** — screens + logic + data. Preview = runnable app, marking->code on the UI.
- **Website** — mostly screens/content; a *lighter* version of the app path; preview can be even
  more visual; marking->code fits perfectly.
- **Automation** — has no screen to mark on. It's a flow ("when X -> do Y -> then Z"). Preview is
  the **flow visualised** (a map of triggers/steps/actions); "marking" = click a step and change
  it; the test is "run the flow with sample data and show what happens at each step".
So it's not three products — it's one product with a type-aware preview surface.

## Build order
Build **app** first, all the way. But design the core so it does NOT assume "app", so gate 2 can
gain a second (website) and third (automation) variant without rebuilding the brain. Website is
then a relatively small effort (a lighter app). **Automation is the largest separate effort (a
new preview + test model) and is a deliberate later phase, not MVP.**

## How this maps to what exists
Built: the marketing site + brand; the backend foundations (auth, tenant isolation, project CRUD);
the React app shell (projects end-to-end); the engine scaffold + Layer A (intake schema) + the
execution machinery (providers + matrix + multi-pass relay) + Layer B (architecture graph, the
whole, playbook, validation). Next: Layer C (build plan), then the builder + sandbox + marking->code
(the shared hard core), then wiring the gates together.
