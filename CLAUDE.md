# Project: AI App Builder (working name)

A web-based AI app builder — a competitor to Lovable — aiming for capabilities that
make sense for 2026 and beyond.

**Status:** Phase 0 complete (repo + docs scaffolded). Next: Phase 1 — vision, scope
& features. Always check `docs/ROADMAP.md` for the current phase before starting work.

## Not yet decided — do not invent
The feature set, the flagship differentiator, and the tech stack are OPEN and will be
decided in later phases (features in Phase 1; architecture/stack in Phase 2). Do not
assume, choose, or hard-code any of them. If a task seems to require such a decision,
stop and flag it, and propose an ADR in `docs/decisions/` rather than deciding silently.

## How we work
- **Phase discipline.** Work on one phase at a time; deliver that phase's artifact;
  don't jump ahead. The roadmap is the source of truth for order.
- **Doc-driven.** Direction and decisions live in `docs/`. When a decision is made,
  record it (update the relevant doc and add an ADR). Keep docs current.
- **Best-practice engineering** (this is also the product's ethos): small, focused
  commits with clear messages; readable, tested code once code exists; no dead code;
  security and cost considered from the start, not bolted on.
- **Roles.** Product and architecture direction is set in planning sessions (the
  "PM"), then executed here. You may and should push back on feasibility, cost, or scope.

## Repo map
- `docs/PRD.md` — product requirements (users, problem, features, scope). Phase 1.
- `docs/ARCHITECTURE.md` — system design across all categories. Phase 2.
- `docs/ROADMAP.md` — the phased plan (0 → testable app). Maintained continuously.
- `docs/BACKLOG.md` — prioritised work items with status.
- `docs/SECURITY.md` — security & threat model.
- `docs/COSTS.md` — cost & metering model.
- `docs/decisions/` — ADRs (one architectural decision per file).

## Conventions
- Commits: Conventional Commits style (`feat:`, `fix:`, `chore:`, `docs:` …).
- ADRs: copy `docs/decisions/0000-adr-template.md`, number sequentially, set status.
- Keep `README.md` and `docs/ROADMAP.md` status current as phases complete.

## Documentation & checkpoint protocol (always on)
This project auto-documents. The repo is the single source of truth.

- Definition of done = built + tested + **documented + committed**. Never leave completed
  work uncommitted.
- After every task, step, or decision:
  1. Update the relevant doc(s) (PRD, UX-FLOW, ARCHITECTURE, PROJECT-PLAN, ...).
  2. If it is an architectural or product decision, add an ADR in docs/decisions/.
  3. Update status in ROADMAP and BACKLOG.
  4. Append an entry to docs/CHANGELOG.md (date, what changed, why).
  5. Commit (Conventional Commits) and push.
- "/checkpoint" = run steps 1-5 for everything changed since the last commit, then print a
  one-line summary. Do this whenever asked to "checkpoint" or "save".
- Planning happens in the planning chat; writing happens here. When the chat hands over a
  decision or checkpoint, apply it and run the checkpoint routine so it lands in the repo.
- Optional enforcement: a git pre-commit or pre-push hook, or a CI check, can flag when
  CHANGELOG or docs were not updated (verify exact hook syntax against current Claude Code docs).
