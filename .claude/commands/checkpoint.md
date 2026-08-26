---
description: Document, changelog and commit everything changed since the last commit
---

Run the checkpoint protocol from `CLAUDE.md`. The repo is the single source of
truth, and "done" means built + tested + documented + committed — so nothing
below is optional and none of it is a formality.

For everything that has changed since the last commit:

1. **Update the docs that the change makes stale.** PRD, UX-FLOW, ARCHITECTURE,
   PROJECT-PLAN, DATA-MODEL, SECURITY, COSTS — whichever the change actually
   touches. A doc that now describes something untrue is the bug this step
   exists to prevent: the external review of 2026-08-22 caught ROADMAP claiming
   per-period metering was built when it was not.
2. **If a product or architectural decision was made, add an ADR** in
   `docs/decisions/`, copied from `0000-adr-template.md`, numbered sequentially,
   with its status set. Do not settle an open decision silently — CLAUDE.md
   names the feature set, the differentiator and the stack as not-yet-decided.
3. **Update status in `docs/ROADMAP.md` and `docs/BACKLOG.md`.** Per-item status
   lives in BACKLOG. If something is open, say what it is *waiting on* — a
   decision, a real run with a key, or infrastructure — because "todo" hides
   that difference.
4. **Append an entry to `docs/CHANGELOG.md`** under `[unreleased]`, newest
   first, with the date, what changed and why. Write what a reader needs to
   understand the change, not a list of files.
5. **Commit and push.** Conventional Commits (`feat:`, `fix:`, `docs:`,
   `chore:`). The subject line says what is now true for a user, not which
   function moved. Push to `master`.

Before committing, run the suites — `/suites` does this — and report the real
numbers in the commit message. If a suite is red, say so and stop; do not
commit over it, and never describe a red suite as green.

Never commit a key, a generated app, or PGDATA.

Finish by printing a one-line summary of what landed.
