# 0017. "Build it" promotes the design workspace; it does not rebuild it

- **Status:** Accepted
- **Date:** 2026-08-22
- **Phase:** PP6 (the design window) / PP8 (delivery)

## Context

Level 2 puts the user inside their app before it is delivered: a preview is built,
they mark elements, describe what should be different, and each accepted change is
committed into the workspace as a design version they can return to.

Then they press **Build it**, and until now that ran the whole path again —
Layer B, Layer C, a fresh workspace, every package regenerated from the frozen
spec. `prepare_workspace(fresh=True)` deleted the directory the design session had
been committing into.

Two things died there. The one that got noticed (B070) is the history: the versions
panel offers "return to this version", and after a delivery build the commits it
points at are gone. The larger one is quieter — **every change the user made in
that session**. The spec never contained them. Marking a button and writing "make
this quieter" changes the code, not the spec, so a regeneration from the spec
produces an app with none of it. The user watched their work being built, then
watched it being replaced by something else.

The tension is real, though: a delivered app must still be *checked*. "Whatever is
in the directory" is not a deliverable if nobody has judged it.

## Decision

**The delivery build promotes the design workspace.** When a project has a current
design version naming a workspace, "Build it" delivers that workspace:

- **Nothing is regenerated.** No codegen, no repair loop, no fresh directory. The
  files the user shaped are the files that ship, and the git history stays intact —
  so a design version stays returnable after delivery.
- **Everything is re-judged.** The same gates in the same order as a fresh build —
  instrumentation, validation, console, interaction, critique — run over what is on
  disk (`verify_package` / `stream_verification`). Delivered means checked.
- **The plan travels with the app.** A build writes its plan and contracts to
  `.scio/plan.json` in the workspace. A promotion reads them back rather than
  re-running Layers B and C, which would cost money and could produce a *different*
  plan — the app would then be judged against criteria it was never built to meet.
- **The delivered app carries no bridge.** The promotion serves the workspace
  without the preview flag, so the marking bridge that made the preview clickable is
  absent from the thing the user owns.
- **A workspace with no stored plan is refused**, never silently rebuilt: the silent
  rebuild is the data loss this exists to prevent, and it would be invisible to the
  person it happened to.
- **The build version records which design it came from** (`design_version_id`), so
  the provenance of a delivered app does not stop at a spec that does not describe it.

A project that never opened the design window is unaffected: there is nothing to
promote, and the build generates the app for the first time exactly as before.

## Consequences

- The user's design work reaches the delivered app. This is the point.
- **A delivery is now cheap.** It pays for the critique passes, not for generating
  the whole app a second time — the second full build was always waste, and it was
  also the second bill.
- The honest status of a delivered build reflects the app *as shaped*, including any
  damage a design change did. That is a feature: it is measured, not assumed.
- The design version and the build version now point at the same workspace, so the
  workspace lifecycle belongs to the project rather than to a single build. Deleting
  it (B100) has to account for both.
- A design session that runs a *second* first-preview build would still recreate the
  workspace. Today that cannot happen through the UI (the design window loads the
  current version's preview), but the hazard is real and is noted at
  `prepare_workspace`.

## Alternatives considered

- **Keep rebuilding, and feed the design changes back as extra prompt context.**
  Lossy by construction: it asks a model to re-derive an outcome we already have on
  disk, and it would sometimes come back different. The user's edits are not a
  suggestion.
- **Give the delivery build its own directory and leave the design workspace alone.**
  Fixes the history, keeps the real bug: the delivered app still would not be the app
  the user shaped.
- **Promote without re-judging, carrying the preview's honest status forward.** The
  cheapest option and the dishonest one — the status would describe an app as it was
  before the changes, and the design window is exactly where the changes happen.
- **Re-run Layers B and C at promotion time to recover the criteria.** Pays twice and
  risks a different plan; storing the plan with the app is deterministic and free.
