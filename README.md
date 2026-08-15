# AI App Builder (working name)

A web-based AI app builder — a competitor to Lovable — targeting 2026-and-beyond
capabilities. This repository is in planning; application code arrives in later phases.

## How this repo works
Planning and decisions are made in dedicated PM/architecture sessions and executed
here in Claude Code. Everything of substance lives in `docs/`.

Start here:
- `docs/ROADMAP.md` — the plan and current phase.
- `docs/PRD.md` — what we're building and for whom (filled in Phase 1).
- `docs/ARCHITECTURE.md` — how it's built (filled in Phase 2).
- `CLAUDE.md` — working rules for this repo.

## Run it locally

The whole product — engine, api, app and a real Postgres — comes up in one
command, with no Clerk, no hosted database, no Docker and no API key:

```bash
scripts/dev-up.sh     # then open http://127.0.0.1:5173 and sign in with any email
scripts/dev-down.sh
```

See `docs/RUNBOOK-LOCAL.md` for what it starts, how dev auth works, and what
differs on the free path. `docs/RUNBOOK-FIRST-RUN.md` covers running it against
a real model.

## Status
Phase 0 complete: repository and document skeleton in place. Next: Phase 1.
