# @scio/api — backend skeleton

NestJS + Prisma against the schema in `docs/DATA-MODEL.md` (ADR-0009). Skeleton stage:
structure, DB schema, health, typed contract, module stubs. Auth (Clerk) is phase 3.3;
project CRUD is 3.4.

## Run locally

```bash
# 1. Start Postgres (with pgvector) from the repo root
docker compose up -d db

# 2. Configure
cp .env.example .env

# 3. Apply the migration and generate the client
pnpm prisma:migrate     # runs prisma migrate deploy against DATABASE_URL
pnpm prisma:generate

# 4. Start
pnpm dev                # http://localhost:3000/health · /docs (Swagger)
```

Without a database the app still boots; `GET /health` then reports `db: "not_configured"`.

## Layout

- `prisma/schema.prisma` — the data model; migrations in `prisma/migrations/`.
- `src/health` — liveness + DB connectivity.
- `src/prisma` — Prisma service (lazy connect).
- `src/modules/*` — one module per domain (controller + service, stubbed with TODOs).
  Tenant scoping: every query must filter on `workspace_id` — noted at each stub.
- `src/modules/stream` — SSE plumbing for later engine output.

The API contract types live in `packages/shared` (`@scio/shared`) and are shared with the
future frontend. Swagger serves the live contract at `/docs`.

## Auth (phase 3.3)

All routes require a Clerk session JWT (`Authorization: Bearer …`) except `@Public()`
ones (`/health`, `/auth/webhooks/clerk`). The flow:

1. `AuthGuard` (global) verifies the token via the swappable `IdentityVerifier`
   interface (`src/auth/identity-verifier.ts`) — Clerk is one implementation
   (ADR-0008); tests use a fake.
2. First authenticated request get-or-creates the local user AND their workspace
   (one per user in MVP) in a transaction (`ProvisioningService`).
3. The guard attaches `{ userId, workspaceId }`; handlers read it via
   `@CurrentUser()` / `@CurrentWorkspace()`.
4. Services use `WorkspaceScope.forWorkspace(workspaceId)` — a Prisma extension
   that filters/stamps `workspace_id` on scoped models. Tenant isolation starts here.

Set `CLERK_SECRET_KEY` in `.env` for real verification; without it, protected routes
reject with 401.
