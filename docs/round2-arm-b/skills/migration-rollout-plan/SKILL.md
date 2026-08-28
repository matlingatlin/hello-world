---
name: migration-rollout-plan
description: Decide the order a schema change ships in, how its data is backfilled, and what happens when it goes wrong. Use when a migration is destructive, renames or retypes something, needs a data backfill, or must survive a code rollback — and whenever a review must say more than "this statement is slow". Covers expand/contract sequencing, batched backfills, and forward-only recovery where no down migration exists. Not for lock analysis of a single statement (use postgres-migration-hazards).
---

# Migration rollout plan

A migration is not a file, it is a window. During deploy, the old code and the new schema
are live **at the same time** — usually for minutes, longer if the deploy is paused or
rolled back. The question this module answers is: what does the running system look like at
every moment between "migration applied" and "all instances on the new code", and how do we
get back if we stop halfway.

## The compatibility test

For every migration, answer both, in writing:

1. **Old code, new schema** — the deploy window. Does the currently running release still
   work after this migration applies, and before any new code ships? A dropped column, a
   renamed column, a narrowed type, or a new `NOT NULL` column the old code does not write
   all fail here.
2. **New code, old schema** — the rollback. If the new release is reverted but the schema
   stays (it will: there is no down migration), does the *previous* release still work?

If either answer is no, the change must be split. That is what expand/contract is.

## Expand / contract

Three releases, never one:

| Phase | Migration | Code |
|---|---|---|
| **Expand** | add the new column/table/index, nullable and unread | new code writes BOTH old and new; reads old |
| **Migrate** | backfill the new column in batches; add constraints `NOT VALID` then `VALIDATE` | reads switch to new; still writes both |
| **Contract** | drop the old column, drop the dual-write constraints | old name unreferenced anywhere |

Rules that make it work:

- **Contract only after a full release has run without touching the old name.** Grep proves
  the current source no longer reads it; it does not prove no *deployed* instance does.
  The gap is the point of the wait.
- A rename is always three phases. There is no safe one-step rename on a live table.
- A type change is always three phases, with the same reasoning: new column, dual-write,
  backfill, swap reads, drop.
- Each phase ships in its own migration file, in its own release. Two phases in one file is
  the same bug as one step.

## Backfills

A backfill is data, not schema, and belongs in its own migration or its own job:

- **Batch it.** `UPDATE ... WHERE id IN (SELECT id FROM t WHERE new_col IS NULL LIMIT 5000)`
  in a loop, committing per batch, with a pause between batches. One `UPDATE` over the whole
  table holds row locks and one long transaction, bloats the table, and — under Prisma's
  per-file transaction — holds every DDL lock in the same file for its whole duration.
- **Make it resumable and idempotent.** Filter on `WHERE new_col IS NULL` so a re-run after a
  crash finishes the job instead of redoing it. A backfill that cannot be re-run safely is a
  blocking finding.
- **Bound it.** Say roughly how many rows and how long. "Unknown, possibly hours, inside the
  deploy" is not a plan.
- **Never leave a `NOT NULL` waiting on a backfill in the same file.** Set the constraint in
  the phase *after* the backfill has completed and been verified.
- Backfilling a column the old code does not yet write means the backfill is racing new
  inserts. Either dual-write first (expand phase) or re-run the backfill after the switch.

## Recovery, where there is no `down`

Prisma generates no down migration and this repo applies with `prisma migrate deploy`. So
"rollback" means one of these, and the review must name **which**:

1. **Forward fix** — a new migration that undoes the change. The default, and the only one
   that works for anything additive.
2. **Compensating migration prepared in advance** — for a risky change, write the reverse
   migration *before* shipping and put it in the PR. Cheap insurance for a constraint or an
   index; impossible for a `DROP`.
3. **Restore from backup** — the only recovery from a `DROP COLUMN`/`DROP TABLE`/`TRUNCATE`
   that has been vacuumed, and it costs the whole database's writes since the backup. If a
   change's only recovery is a restore, say so in those words; it is what makes destructive
   changes different in kind, not degree.

For any destructive statement, require in the PR: the evidence the data is unread (grep of
the source *and* a stated release since it was last written), the backup/PITR window that
would cover a mistake, and a named contract phase this belongs to. Absent any of the three,
the finding is blocking.

## Deploy order

State it explicitly, because it is not always "migration first":

- **Additive change** → migration first, then code. Safe.
- **Destructive change** → code first (a full release that stops using the thing), then the
  migration in a later release. Never the same deploy.
- **A migration that takes minutes** → apply it out of band, before the release, not inside
  the deploy step where a health check will time out and start a rollback loop mid-DDL.

## What the ship note must contain

A migration is reviewable only if the PR says: what phase this is, what the deploy order is,
how long it is expected to hold locks, how the backfill is bounded, and which of the three
recovery routes applies. When those are missing, the answer is not to guess them — ask for
them as required changes, and review the SQL on its worst-case reading in the meantime.
