# 0022. The migration reviewer agent

- **Status:** Proposed
- **Date:** 2026-08-28
- **Phase:** Phase 6 (security, multi-tenancy & metering) / continuous — the review gate that
  the migrations in Phase 6 and later need before they touch a database with customers in it.

## Context

`apps/api/prisma/migrations/` holds twelve migrations and will hold many more: ADR-0019
(deletion and retention) and ADR-0020 (builds as jobs) both imply schema work, and the
metering tables that decide what customers pay grow with every build. Three facts make an
unreviewed migration unusually dangerous here:

- **There is no down migration.** Prisma generates none and we apply with
  `prisma migrate deploy`. Recovery is forward-only or a restore.
- **CI never applies a migration.** `.github/workflows/ci.yml` typechecks and tests; no
  database step exists. A green build is no evidence whatsoever that a migration applies.
- **Two owners share one database.** Prisma owns the product tables, the engine creates and
  owns `library_*` at runtime. Nothing enforces that boundary but review.

A measured baseline (`docs/round2-arm-b/baseline.md`) shows the unaided model is already good
at lock and destructive analysis, and predictably bad at three things: severity inflation
(nine of thirteen findings marked blocking), systematically checking whether a statement's
premise about the current schema is even true, and naming which of the three recovery routes
applies. Those gaps — not the lock table — are why an agent rather than a checklist.

## Decision

Add a `migration-reviewer` subagent that reviews migrations before they ship and produces a
report with a ship / ship-with-changes / no-ship verdict, and cannot edit or apply anything.

- **Two preloaded skills**, under the three-module cap: `postgres-migration-hazards` (does
  this statement apply, what does it lock, what does it lose) and `migration-rollout-plan`
  (what order does it ship in, how is it backfilled, how do we get back).
- **`tools: Read, Grep, Glob, Write, TodoWrite`** — explicit, and deliberately without
  `Bash`. The absence is the enforcement: with no shell there is no `prisma migrate deploy`,
  no `psql`, and no way around the write gate. It costs the agent `git diff`, which the
  review does not need.
- **A PreToolUse write gate** (proposed, `docs/round2-arm-b/hooks/`) narrowing `Write` to
  `docs/reviews/`. The "never edit the migration you are reviewing" rule is a hook plus an
  absent tool, not a sentence.
- **Ten evals**, including a negative control (a safe migration must earn `ship` with zero
  blocking findings) and a containment case (asked to fix and apply, it must be *unable* to,
  not merely unwilling). Graded by a subagent that did not author the agent.

## Consequences

- A migration PR gains a review artefact under `docs/reviews/` that names the lock, the loss
  and the deploy order, with replacement SQL per finding — actionable, not advisory.
- The agent cannot verify anything empirically. It cannot count rows, run `EXPLAIN`, or prove
  a migration applies. Findings are therefore conditional on scale where scale matters, and
  the review is not a substitute for applying the migration to a restored copy of production.
  That gap is real and is the strongest argument for a future CI step that applies migrations
  against a seeded database — which would reduce this agent's remit, not replace it.
- Without `Bash` the agent depends on the caller pointing it at the right files, or on
  Glob/Grep finding them. Eval E7 covers the failure.
- Two skills is two more modules to keep true as Postgres and Prisma versions move. The
  version assumptions (PG 14+, Prisma 5) are stated in the skill so they can be re-checked.

## Alternatives considered

- **A checklist in `CLAUDE.md` instead of an agent.** Rejected: the baseline shows the
  problem is not missing knowledge, it is that the pass is not systematic and the severities
  are not calibrated. A checklist nobody is obliged to run does neither, and `CLAUDE.md` text
  reaches the main session but a measured canary probe in this repo found rules do not reach
  a subagent.
- **A lint rule / CI check over migration SQL** (`squawk`, `eugene`). Rejected as the primary
  mechanism, not as a complement: a linter catches the lock hazards, which is the half the
  model was already good at, and cannot check whether a `DROP`'s premise is true or whether
  the previous release survives a rollback. Worth adding alongside; it would let the agent
  spend its attention on the half no linter can reach.
- **Folding this into the `architect` agent.** Rejected: different remit, different failure
  table, and it would take that agent past the three-module cap. A fourth function is the
  signal that you have two agents.
- **Giving the agent `Bash` so it could run `git diff` and a linter.** Rejected: it makes
  "cannot apply a migration" unenforceable, and a reviewer that can apply what it reviews is
  not a reviewer.
