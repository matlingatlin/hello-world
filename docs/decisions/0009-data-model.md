# 0009. Data model

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 3.1

## Context
Phase 3 needs a persistence model for accounts, projects, the frozen spec/design/build
contracts, the wizard conversation, reference RAG, metering, and notifications — built on
Postgres/Azure with pgvector (ADR-0007), Clerk auth (ADR-0008), and git holding version
content (UX-FLOW).

## Decision
Adopt the schema in docs/DATA-MODEL.md. Key choices:
- **Everything is scoped by `workspace_id`** — tenant isolation lives in the data layer
  and is enforced in every query and in authorization.
- **Version *content* (the actual code) lives in git**; `build_version.git_sha` points to
  it, so the database stays light. Restores are non-destructive — they create a new
  build_version, never delete history.
- **JSONB** for evolving/nested structures (spec content, assumptions, honest_status,
  extracted reference data, audit metadata).
- **pgvector** for `reference_embedding` (retrieval).
- **Secrets** (API keys, tokens) live in the Azure secrets manager, never in the DB.
- **Billing/subscription tables are deferred to Phase 12**; `usage_event` already captures
  metering now.
- Standard: uuid primary keys, created_at/updated_at, soft-delete on projects, version
  numbers unique per project.

## Consequences
- Tenant isolation is structural, not bolted on (supports Phase 9 security).
- The DB is light and fast; heavy artifacts (code, files) live in git/object storage.
- Non-destructive versioning is native (matches the product promise).

## Alternatives considered
- Storing version code as DB blobs — rejected; git is the source of truth and gives the
  user real ownership/history.
- A separate vector DB from day one — rejected for MVP; pgvector suffices (ADR-0007).
