# Roadmap — from zero to a testable app

> Detailed, authoritative build plan: **docs/PROJECT-PLAN.md** (phases 0-12). Its phase
> numbers are canonical going forward. This ROADMAP is a high-level snapshot.

Status legend: ☐ not started · ◐ in progress · ☑ done

## Phase 0 — Setup & way of working  ☑
Goal: a repo we can work in, organised from day one.
Deliverable: repository + document skeleton + CLAUDE.md, first commit.

## Phase 1 — Vision, scope & features  ◐  ← in progress
Goal: decide who it's for and how it's positioned vs Lovable; brainstorm → prioritise
the feature set; choose MVP scope and the flagship differentiator.
Deliverable: completed PRD + prioritised feature list.

## Phase 2 — Architecture & decisions  ☐
Goal: system design across all categories; choose stack, sandbox, DB, hosting; define
the data model, security model, and cost model.
Deliverable: completed ARCHITECTURE.md + ADRs for the major choices.

## Phase 3 — Vertical slice  ☐
Goal: thinnest runnable path end-to-end — prompt → generation → sandbox → preview —
with an auth stub.
Deliverable: internal end-to-end prototype.

## Phase 4 — Core engine & differentiator  ☐
Goal: build out the agent and the chosen flagship loop for real, with guardrails and tests.
Deliverable: an engine that can handle real builds.

## Phase 5 — Product UI & project flow  ☐
Goal: dashboard, live preview, editor, version history.
Deliverable: a usable product surface.

## Phase 6 — Security, multi-tenancy & metering  ☐
Goal: tenant isolation, sandbox hardening, rate limits, usage/cost metering, billing stub.
Deliverable: a multi-user-safe version.

## Phase 7 — Testable alpha  ☐
Goal: closed testing, bug-fixing, onboarding, observability.
Deliverable: a testable app (the goal of this plan).

_Public launch, live billing, and full hardening come after the testable alpha and are
out of scope until we get there._
