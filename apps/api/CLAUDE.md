# apps/api — NestJS + Prisma

The boundary between the browser and the engine. It owns identity, tenancy,
persistence and metering; it owns no product reasoning — that is the engine's.

## Tenancy is application-layer, and that is a habit, not a wall

A Prisma `$extends` client stamps and filters `workspace_id` on the scoped
models (`auth/workspace-scope.ts`). **Child rows — spec, design and build
versions, messages, build jobs — are not scoped at the data layer.** They are
safe only because every service resolves the project through the scoped client
first, which throws for somebody else's project, and only then touches children
by `projectId`.

Follow that order. One `buildVersion.findMany({ where: { projectId } })` on the
raw client reads across tenants with nothing to stop it.
`test/tenant-discipline.spec.ts` is the fence: a service that reaches for the
unscoped client fails the suite and has to justify itself in that test's
allow-list.

## Money

Every path that spends must meter, including the ones that do not finish.
`BuildService.run` accumulates spend per `package` event and writes a usage row
on **every** exit — succeeded, failed and cancelled — and the figure also lands
on the `build_job` row. A cancellation that forgave the cost would be an
exploitable hole; an external review found exactly that and it is closed.

`ensureCanStart` asks `UsageService.allowance()` before work begins:
`SCIO_WORKSPACE_PERIOD_CAP_USD` over the UTC calendar month, default $50, and a
`409` naming the real figures when there is no room.

Metering must never throw into the build. Log a failed ledger write; do not
raise it.

## Auth

Dev auth means **the bearer token is the identity** (`dev:someone@example.com`).
A different email is a different workspace. It logs a warning on boot for a
reason — it must never be on in production.

## Migrations

`prisma migrate deploy`, numbered directories under `prisma/migrations/`. The
generated client is a build artifact: a `git pull` does not regenerate it, so
`prisma generate` runs before `migrate deploy` in `scripts/dev-up.sh`. Adding a
column means a migration *and* a schema change — never one without the other.

## Tests

`npx vitest run` from this directory. They are in-process: supertest against the
Nest app with a fake engine. That is fast and it is also the blind spot — these
tests cannot see CORS, StrictMode, or anything a browser does. Bugs that only a
running browser finds are normal here; click through before believing a feature
works.

Contracts shared with the app live in `packages/shared`, never duplicated.
