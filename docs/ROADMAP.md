# Roadmap — from zero to a testable app

> Detailed, authoritative build plan: **docs/PROJECT-PLAN.md** (phases 0-12). Its phase
> numbers are canonical going forward. This ROADMAP is a high-level snapshot.

Status legend: ☐ not started · ◐ in progress · ☑ done

**As of 2026-08-22.** This snapshot had said phases 2 to 6 were not started, while the repo
held twenty ADRs, an engine that has completed real builds, a working design window and
per-tenant metering. It is corrected below. Where a phase is marked ◐, the named gap is what
is actually missing — not a guess.

## Phase 0 — Setup & way of working  ☑
Goal: a repo we can work in, organised from day one.
Deliverable: repository + document skeleton + CLAUDE.md, first commit.

## Phase 1 — Vision, scope & features  ◐  ← in progress
Goal: decide who it's for and how it's positioned vs Lovable; brainstorm → prioritise
the feature set; choose MVP scope and the flagship differentiator.
Deliverable: completed PRD + prioritised feature list.
_The PRD, the strategy and the differentiator are settled and have been built against for
weeks. What is genuinely still open is the last line of the original goal: MVP scope,
non-goals and the metrics that say whether it worked (B005) — plus pricing (B063), which the
estimate screen is waiting on._

## Phase 2 — Architecture & decisions  ☑
Goal: system design across all categories; choose stack, sandbox, DB, hosting; define
the data model, security model, and cost model.
Deliverable: completed ARCHITECTURE.md + ADRs for the major choices.
_Done: ADR-0001…0020. Three are Proposed and need the planning chat — 0018 (what Ship,
Refine and Settings are), 0019 (deletion and retention), 0020 (builds as jobs)._

## Phase 3 — Vertical slice  ☑
Goal: thinnest runnable path end-to-end — prompt → generation → sandbox → preview —
with an auth stub.
Deliverable: internal end-to-end prototype.
_Done: new project → wizard → review → design window → build → reveal runs end to end, on
real models and on the free stand-in path._

## Phase 4 — Core engine & differentiator  ◐
Goal: build out the agent and the chosen flagship loop for real, with guardrails and tests.
Deliverable: an engine that can handle real builds.
_Built: A→B→C, the matrix + multi-pass relay, the vision loop and its guardrails, the
component library with contribute-back, and the design window. Open: the estimate is
calibrated against an output-only price and needs a real run (B115), and the reveal has no
quality gate yet (B048)._

## Phase 5 — Product UI & project flow  ◐
Goal: dashboard, live preview, editor, version history.
Deliverable: a usable product surface.
_Built: projects, wizard, spec review with corrections, design window with routes and
versions, build, reveal, and "get the code". Open: Versions, Settings and Notifications are
still placeholders, and what they should be is ADR-0018._

## Phase 6 — Security, multi-tenancy & metering  ◐
Goal: tenant isolation, sandbox hardening, rate limits, usage/cost metering, billing stub.
Deliverable: a multi-user-safe version.
_Built: workspace scoping that fails closed (and a test that fences it — a service reaching
for the unscoped client fails the suite), an allow-listed sandbox environment with memory, CPU
and PID limits, per-build **and** per-period metering with a spend ceiling — a cancelled or
failed build is billed for what it actually spent — a throttler keyed by workspace rather than
by IP, project deletion that deletes, and a first pass over prompt injection. Open: account
deletion (ADR-0019), a network policy for build containers (B118), and a sandbox that isolates
in production rather than sharing the host (B122) — which waits on B079's deploy target._

## Phase 7 — Testable alpha  ☐
Goal: closed testing, bug-fixing, onboarding, observability.
Deliverable: a testable app (the goal of this plan).
_Blocked on one thing: nobody outside the sandbox can open it (B079). The whole stack runs on
localhost or in a Codespace; there is no deployment, so there is nothing for a tester to visit._

_Public launch, live billing, and full hardening come after the testable alpha and are
out of scope until we get there._
