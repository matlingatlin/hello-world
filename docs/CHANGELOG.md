# Changelog
Running log of decisions and changes for Scio. Newest first.
See CLAUDE.md, "Documentation & checkpoint protocol", for how this is maintained.

## [unreleased]

### Added
- 2026-08-07 — Layer B defined (ADR-0012 + docs/LAYER-B.md) and generated-app stack locked
  (ADR-0011: Next.js + TypeScript + Tailwind + Supabase). Layer B manufactures the prompt
  substrate: the whole, a machine-readable architecture graph, and the generation playbook,
  with rule-based validation before generation.
- 2026-08-08 — Layer A built in the engine (apps/engine — the engine scaffold now exists:
  Python + FastAPI + Pydantic, ruff + pytest, .env.example, /health): the INTAKE-SCHEMA
  as typed models (FieldMeta with value/source/confidence/provenance, DownstreamTag enum,
  AppSpec with core / conditional / defaulted-and-flagged fields), is_buildable() per the
  gate rule, trigger detection (incl. multiple-roles and sensitive-data derived triggers),
  downstream-tag mapping for Layer C, and POST /intake/validate returning the verdict +
  what's still needed. 21 tests + lint green; service boot verified live. No extraction/LLM
  calls yet (4.3); matrix + multi-pass is the next engine kickoff (B031).
- 2026-08-07 — Layer A intake schema defined (ADR-0010 + docs/INTAKE-SCHEMA.md): six core
  fields + conditional follow-ups + non-goals, per-field metadata (value/source/confidence/
  provenance), downstream build-area tags, and the is_buildable gate rule. Part of a
  three-layer model: A intake -> B understanding -> C build plan.
- 2026-08-08 — Phase 3.5a real React app, step 1 (apps/app): Vite + React + TS + Tailwind
  scaffold with the DESIGN.md tokens as CSS variables (light default + dark toggle, fonts
  loaded), design-system components from the prototype (buttons, status chips, sidebar,
  topbar, state cards, logo tile), React Router shell, Clerk sign-in guarding the app, and
  a typed API client (@scio/shared) that attaches the Clerk JWT and surfaces 401/400/network
  errors. Projects (GET, with loading/empty/error states) and Create (POST → back to list)
  are wired end-to-end; remaining screens are placeholders for step 2 (B022). Degrades
  gracefully without Clerk keys (config notice) or backend (error state + retry). Build +
  8 frontend tests green; full-stack run documented in apps/app/README.md.
- 2026-08-08 — Phase 3.4 project CRUD (apps/api): first real persisted endpoints —
  POST/GET/PATCH/DELETE /projects with workspace-scoped access via the 3.3 scoping
  (create stamps workspace_id, list excludes soft-deleted and sorts newest first,
  cross-tenant access is 404), class-validator DTOs in @scio/shared with a global
  ValidationPipe (400 on invalid bodies), soft-delete via deleted_at, and OpenAPI
  schemas for all five endpoints. Proven by an e2e test suite (fake identity, two
  workspaces): full lifecycle, validation, 401, cross-tenant isolation — 20 tests green.
  This completes the Phase 3 backend foundations (auth + projects).
- 2026-08-08 — Phase 3.3 backend auth (apps/api): Clerk session-JWT verification behind a
  swappable IdentityVerifier interface (ADR-0008), global auth guard with @Public()
  exemptions (/health, Clerk webhook stub), get-or-create provisioning (first authenticated
  request creates the user AND their MVP one-per-user workspace in a transaction), and
  request context (@CurrentUser/@CurrentWorkspace) wired through every module. Tenant
  scoping is now enforced at the data layer via a WorkspaceScope Prisma extension that
  filters/stamps workspace_id on scoped models. Proven with a fake verifier in tests
  (13 passing) + live 401/public-route checks; no real Clerk keys in this environment.
- 2026-08-08 — Phase 3.2 backend skeleton (apps/api): NestJS + Prisma with the full
  DATA-MODEL schema (12 models + pgvector reference_embedding, initial migration,
  docker-compose Postgres), typed API contract in packages/shared (@scio/shared),
  Swagger at /docs, GET /health with DB connectivity, module stubs for
  workspace/user/auth/project/spec/design/build/deployment/reference/usage/notification,
  and an SSE stream stub. Build, boot, health and tests verified green. Auth logic and
  CRUD deliberately left for 3.3/3.4.
- 2026-08-07 — Phase 3.1 data model defined (ADR-0009 + docs/DATA-MODEL.md): workspace-scoped
  tenant isolation, git-backed version content, JSONB for spec/whole/status, pgvector for RAG,
  deployment + notification tables added, billing deferred to Phase 12.
- 2026-08-07 — Phase 2 app-shell prototype complete: every screen clickable with mocked
  data (projects, create/type-select, wizard + wholeness panel, spec gate, involvement,
  design mode with numbered annotation, build view, reveal + honest status, live feedback,
  versions, ship/export, settings, error & empty states, notifications) -> apps/app/prototype.html.
- 2026-08-07 — Phase 1 (brand) complete: logo (assets/logo/scio-logo.svg, concept B tile
  monogram) and first marketing site (apps/website/index.html). Design tokens already in
  docs/DESIGN.md.
- 2026-08-07 — Phase 0.2 stack decisions: cloud Azure (ADR-0004), sandbox ACA dynamic
  sessions (ADR-0005), backend Node/TS + Python engine (ADR-0006), database Postgres on
  Azure (ADR-0007), auth Clerk (ADR-0008).
- 2026-08-07 — Established the full planning baseline in the repo: repo + docs, CLAUDE.md
  (with the documentation & checkpoint protocol), wedge (ADR-0001), name Scio (ADR-0002),
  visual identity (ADR-0003) + docs/DESIGN.md, the customer journey (docs/UX-FLOW.md), and
  the full build plan (docs/PROJECT-PLAN.md).

### Next
- Build Layer B in the engine (architecture graph + playbook + validation), and build the engine's provider abstraction + matrix + multi-pass (B031). Then Layer C.
