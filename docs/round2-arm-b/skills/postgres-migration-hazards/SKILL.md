---
name: postgres-migration-hazards
description: Decide whether a Postgres schema change can be applied to a live database without an outage. Use when reviewing a migration file, a `prisma migrate` diff, or any DDL that will run against a database with traffic on it — ADD/ALTER/DROP COLUMN, CREATE INDEX, ADD CONSTRAINT, type changes, renames. Names the lock each statement takes, what that lock blocks, and the rewrite that avoids it. Not for query tuning and not for choosing a data model.
---

# Postgres migration hazards

A migration is safe when three things are true: it takes no lock that blocks traffic for
longer than the request timeout, it loses no data that cannot be recovered, and the schema
it leaves behind is one that BOTH the currently running code and the next release can talk
to. This module covers the first. Sequencing and recovery are `migration-rollout-plan`.

## How to read a statement

Every DDL statement takes a lock on the table. What matters is not the lock's name but two
questions: **what does it block**, and **how long does it hold**. An `ACCESS EXCLUSIVE`
lock held for 2 ms is fine. The same lock held for a full-table scan on `usage_event` is an
outage — and worse, a lock request *queues*, so a blocked DDL statement blocks every reader
behind it too (the "lock queue pile-up": one slow `ALTER` stops all reads on the table even
though `ALTER` was only waiting).

Assume Postgres 14+ (this repo: Azure Flexible Server, ADR-0007). Assume the table under
review is large unless a row count says otherwise; `usage_event`, `message`,
`reference_embedding` and `build_job` grow with traffic and are never small in production.

## The failure table

| Statement | Lock / cost | Why it hurts | Safe form |
|---|---|---|---|
| `ADD COLUMN x TEXT` (nullable, no default) | ACCESS EXCLUSIVE, catalog-only, O(1) | Safe. Do **not** flag it. | as written |
| `ADD COLUMN x TEXT NOT NULL DEFAULT 'a'` | ACCESS EXCLUSIVE, catalog-only, O(1) since PG 11 | Safe — the default is stored in the catalog, no rewrite. Flagging this as a table rewrite is the most common false positive in migration review. | as written |
| `ADD COLUMN x uuid NOT NULL DEFAULT gen_random_uuid()` | full table rewrite | The default is **volatile**, so every row is written. Rewrite + ACCESS EXCLUSIVE for the duration. | add nullable → backfill in batches → `SET NOT NULL` via validated CHECK |
| `ALTER COLUMN x SET NOT NULL` | ACCESS EXCLUSIVE + full scan | Scans every row to prove no NULLs, holding a lock that blocks reads and writes. | `ADD CONSTRAINT c CHECK (x IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT c` (SHARE UPDATE EXCLUSIVE, does not block writes) → `SET NOT NULL` (then O(1): PG 12+ trusts the validated constraint) → drop the CHECK |
| `CREATE INDEX` | SHARE lock: **blocks all writes** for the whole build | On a hot table this is a write outage lasting as long as the build. | `CREATE INDEX CONCURRENTLY` — but see the transaction rule below |
| `DROP INDEX` | ACCESS EXCLUSIVE, fast | Fine on time, but it is a performance cliff, not a schema change: the queries that used it now scan. | `DROP INDEX CONCURRENTLY`; check what used it first |
| `ADD CONSTRAINT ... FOREIGN KEY` | ACCESS EXCLUSIVE on **both** tables + full scan of the child | Two tables locked, one scanned. The parent lock is the one people miss. | `... NOT VALID` (catalog-only, still enforced for new rows) then `VALIDATE CONSTRAINT` in a separate statement/migration |
| `ADD CONSTRAINT ... CHECK` | ACCESS EXCLUSIVE + full scan | same | `NOT VALID` → `VALIDATE` |
| `ALTER COLUMN TYPE` | full table rewrite + index rebuilds | Rewrites the whole table under ACCESS EXCLUSIVE. Exceptions that are catalog-only: `varchar(n)` → `varchar(m>n)` or `text`, and `numeric` precision *increases*. Narrowing is never free and can fail mid-way. | new column → dual-write → backfill → swap (expand/contract) |
| `RENAME COLUMN` / `RENAME TABLE` | ACCESS EXCLUSIVE, fast | The lock is not the problem. The old name disappears *instantly*, so every running instance of the old code breaks the moment it commits. There is no deploy ordering that makes a rename safe on its own. | never rename in place on a live table — add the new name, dual-write, migrate readers, drop the old one in a later release |
| `DROP COLUMN` / `DROP TABLE` | ACCESS EXCLUSIVE, fast | Irreversible. The data is gone and a rollback of the *code* cannot bring it back. | see `migration-rollout-plan` — drop only after the column has been unread for a full release |
| `TRUNCATE` | ACCESS EXCLUSIVE, fast, unrecoverable | Almost never belongs in a migration. | block it |
| `UPDATE`/`DELETE` over a whole table | row locks + one long transaction | Holds locks and bloats the table; on this repo it also holds every DDL lock in the same file (see below). | batch it, outside the DDL — `migration-rollout-plan` |
| `VACUUM FULL`, `REINDEX` (non-concurrent), `CLUSTER` | ACCESS EXCLUSIVE for the duration | Full outage on the table. | `REINDEX CONCURRENTLY`, or an operational task, not a migration |

## Three rules that override the table

1. **`CONCURRENTLY` cannot run inside a transaction.** Prisma wraps each migration file in
   one. So a `CREATE INDEX CONCURRENTLY` in a normal Prisma migration fails at apply time —
   the migration must be the *only* statement in its file and be marked as non-transactional
   (Prisma: `-- CreateIndex` in a file applied with `prisma db execute`, or a separate
   migration whose sole statement is the concurrent build). Flag the pairing, not just the
   missing keyword. A concurrent build can also fail and leave an **invalid index** that is
   never used and must be dropped by hand — the rollout note must say so.
2. **The whole file is one lock window.** Prisma runs the file in a single transaction, so
   locks taken by statement 1 are held until statement 9 commits. A cheap `ALTER` that sits
   after a 40-second backfill in the same file holds its ACCESS EXCLUSIVE lock for 40
   seconds. Judge the file, not the statement.
3. **Always ask for a lock timeout.** Any migration touching a table with traffic should set
   `SET lock_timeout = '3s'` (and often `statement_timeout`) at the top, so a statement that
   cannot get its lock fails fast instead of forming a queue behind itself. Its absence on a
   hot-table migration is a finding.

## The pass that comes first: will this statement even apply?

Measured on this repo's baseline run: three of seven statements in a realistic hazardous
migration asserted something about the current schema that was **not true**. That class is
invisible to a lock analysis, and it is cheaper to catch than any of the hazards above.
Before judging risk, check every statement against `apps/api/prisma/schema.prisma` and the
existing files in `apps/api/prisma/migrations/`:

- **Object already exists.** `ADD CONSTRAINT "x"` where `x` was created in an earlier
  migration raises `42710 duplicate_object` and aborts the file. Changing a constraint means
  `DROP CONSTRAINT` then `ADD` — `ADD` alone silently does not achieve the change even in
  the imagination of the author. Same for a re-created index or column.
- **The statement is a no-op.** `SET NOT NULL` on a column that is already `NOT NULL`, an
  index that duplicates an existing one. Harmless alone; as a signal it means the file was
  written from memory rather than from the schema, and every other statement in it now needs
  the same check.
- **The premise is false.** "This column is unused" / "this never shipped" — grep the source
  before believing it. A `DROP` justified by a false premise is the single most expensive
  finding a review can miss.
- **A failed migration blocks the next deploy.** Prisma marks the file failed and refuses to
  proceed until someone runs `prisma migrate resolve` by hand. A statement that will abort is
  therefore not "it just rolls back" — it stops the deploy pipeline.
- **Repo convention: guard with `IF NOT EXISTS`.** Migrations 0006, 0008, 0010, 0011 and 0012
  all do. A file without guards cannot be retried after a partial manual apply.

## Two more hazards that are correctness, not availability

- **A constant `DEFAULT` that is never dropped.** `ADD COLUMN period TEXT NOT NULL DEFAULT
  '2026-08'` backfills history correctly and then stamps *every future row* with a value that
  is wrong and never errors. If a default exists only to make the column addable, the same
  migration must `ALTER COLUMN ... DROP DEFAULT` after the backfill, and the code that writes
  the real value must already be deployed.
- **A denormalized column with no constraint keeping it true.** A `TEXT` column derived from
  another column can drift the moment anything writes it by hand, and accepts `'2026-8'` and
  `''` equally. Prefer `GENERATED ALWAYS AS (...) STORED`, or a `CHECK`. And a derivation
  over a `TIMESTAMP(3)` *without* time zone (what `0001_init` created) silently misfiles every
  row in the boundary hours of a month — ask which zone the business calendar is in.

## This repo's specifics

- **Two schema owners, one database.** Prisma owns the product tables
  (`apps/api/prisma/schema.prisma`); the engine creates and owns `library_*` at runtime
  (`apps/engine/src/scio_engine/library/store.py`). A Prisma migration that touches a
  `library_*` table, or engine DDL that touches a product table, is a boundary violation and
  a blocking finding regardless of its lock profile.
- **Migrations are applied by `prisma migrate deploy`** (`apps/api` script `prisma:migrate`,
  and `scripts/dev-up.sh`). There is **no down migration** — Prisma does not generate one.
  Recovery is forward-only or a restore; a review that assumes a rollback exists is wrong.
- **CI does not apply migrations** (`.github/workflows/ci.yml` runs typecheck and tests, no
  database step). So "CI is green" is *no evidence at all* that a migration applies. Any
  claim that a migration is proven by CI is a finding.
- **A `schema.prisma` edit without a matching migration** (or vice versa) is drift:
  `prisma migrate deploy` will not fix it and the next `migrate dev` will try to reset.
  Check both sides of every change.
- **Partial unique indexes carry invariants**, not just speed:
  `spec_version_one_current_per_project` and its siblings (migration 0006) are what make
  "exactly one current version" true. A migration that drops, replaces or widens one of them
  is removing an enforced invariant, and that is a blocking finding even though the DDL is
  cheap.
- **Every table is workspace-scoped** (`docs/DATA-MODEL.md`). A new table without a
  `workspace_id` (or a documented path to one) breaks tenant isolation; a new index on a
  hot read path that omits `workspace_id` as its leading column usually will not be used by
  the scoped queries that actually run.

## What "large" means when nobody will tell you

You cannot query the production database from a review. Do not guess a row count and do not
ask for one as a condition of finishing. Say what the finding depends on instead: *"if
`usage_event` exceeds ~1M rows this scan holds an ACCESS EXCLUSIVE lock for seconds — the
safe form costs nothing at either size, so take it."* A rewrite that is free at small scale
and mandatory at large scale should simply be recommended.
