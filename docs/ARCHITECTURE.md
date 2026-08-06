# Architecture

> Status: skeleton. Filled in **Phase 2**. No tech-stack or design decisions are made
> yet — record each one as an ADR in `docs/decisions/` when taken.

## Overview
_System diagram + how the pieces fit together._  (Phase 2)

## Product layer
- Frontend / UI — prompt & chat, live preview, code/file view, dashboard.  (Phase 2)
- AI engine & agent — context pipeline, agent loop, model routing, guardrails.
  (Phase 2)
- Code execution & preview — sandbox, dev server, preview streaming.  (Phase 2)

## Platform layer
- Backend / API — orchestration, job queue, streaming, project & user management.
  (Phase 2)
- Data — database, object storage, secrets.  (Phase 2)
- Integrations — DB provisioning, GitHub export, deploy targets, MCP connectors.
  (Phase 2)
- Auth & security — see `SECURITY.md`.  (Phase 2)

## Business & ops layer
- Payments & metering — see `COSTS.md`.  (Phase 2)
- Infra / DevOps — hosting, CI/CD, observability, scaling.  (Phase 2)
- Compliance / legal — ToS, GDPR, IP/ownership of generated code, EU VAT.  (Phase 2)

## Tech stack
_TBD in Phase 2. Do not assume._
