---
name: migration-reversibility
description: "Use when deciding whether a migration can be undone and what happens if the deploy has to be abandoned halfway — a dropped column, an extended enum, a backfill, a constraint added, or any change in a repo with no down migrations. Also use when asked what the rollback plan is, whether an application release can be rolled back past a migration, or whether a partly-applied migration leaves the deploy stuck. Emits a per-statement reversibility verdict, the named forward-fix, and the point past which the application cannot be rolled back. NOT for lock and downtime (use migration-lock-risk), NOT for what the change breaks in existing data and code (use migration-blast-radius)."
---

# What gets us back

Rollback is the question a review answers last and a deploy asks first. In this
repo there is no down migration to fall back on — `prisma migrate deploy` runs
forward only (`apps/api/CLAUDE.md`, `apps/api/package.json`), which
`docs/REVIEW-PRODUCTION-READINESS.md:272` records as an open gap rather than a
solved problem. So "we can roll back" is not available as an answer, and a review
that does not say what *is* available has left the deploy without a plan.

The rule that overrides the natural reading: **reversibility is a property of each
statement, not of the migration.** A file that adds a column and drops another is
half trivially reversible and half permanently not, and the file-level answer —
whichever one you pick — is wrong about half of it.

Two questions are distinct and both must be answered, because people answer the
first and believe they have answered the second:

1. **Can the schema change be undone?** (structure)
2. **Can the data it destroyed or coerced be recovered?** (content)

Dropping a column is reversible in one minute and irreversible forever, depending
on which question is asked.

## 1 · Per-statement reversibility verdict

For every statement, in order:

| Verdict | Meaning |
|---|---|
| `reversible` | one statement undoes it, and no data is lost by undoing it |
| `reversible, data lost` | structure returns; rows written since do not |
| `irreversible` | the database offers no inverse at all — an extended enum has no `DROP VALUE`; a coerced type has no un-coercion |
| `n/a` | nothing to undo (a pure read, or an idempotent no-op) |

**Artefact:** the verdict column, every statement present, at `file:line`.

## 2 · Name the forward-fix, because there is no down migration

For every statement that is not `reversible`: what is the migration a human writes
at 03:00 to get out of this? Name it concretely enough to be written — the
statement, the data source it recovers from, and whether that source still exists.

"Restore from backup" is an acceptable answer **only** with the recovery window and
what is lost inside it. Anything else is a wish.

**Artefact:** forward-fix per non-reversible statement, or the explicit line
`no forward-fix exists — this is one-way`, which is a legitimate finding and often
the most valuable line in the document.

## 3 · The point of no return for the application

A migration and a release are two deployments. Ask: **once this migration is
applied and traffic has flowed, can the previous application version still run?**
Usually the danger is not the schema but the rows the new code has written — a new
enum value, a new status string, a column the old client's generated types do not
know — that the old code cannot deserialize.

Find the read paths that would meet that data, at `file:line`, and say what they do
when they meet it. Then state the boundary in one sentence: *"After this ships and
the first <row shape> exists, the API cannot be rolled back past release X without
<consequence>."*

**Artefact:** the point-of-no-return sentence, or `the previous release keeps
running` with the read paths checked.

## 4 · What a half-applied deploy leaves behind

A migration can fail on contact with production data. Establish, for the tool as
this repo configures it — read it live, do not assume — whether the file is applied
in one transaction, and then answer:

- Does a mid-file failure roll back the statements before it, or leave them applied?
- What does the migration tool record, and does that state **block subsequent
  migrations** until a human intervenes?
- If it does: how many migrations are behind this one, and is application code for
  any of them already shipping?

A deploy that stops with later migrations unapplied while the release goes out is
worse than a deploy that fails cleanly, and it is invisible unless someone counts.

**Artefact:** the stuck-state description, the command that clears it, and the
count of migrations behind this one.

## 5 · Backfills are their own question

Any `UPDATE`, `INSERT ... SELECT` or defaulted column that writes to existing rows:

- **Idempotent?** Can it be run twice without a different result? A rerun after a
  partial failure is the normal recovery path, so a non-idempotent backfill is a
  one-shot with no retry.
- **Batched?** An unbatched write over a large table holds locks and grows the
  table until it finishes or is killed.
- **Recoverable?** Does it overwrite a value that existed? If yes, where is the old
  value after the write — and if the answer is "nowhere", that is data loss, even
  though the migration only wrote a default.
- **Right?** A default written into historical rows asserts a fact about the past.
  Check whether that fact is true, and whether the column can express "unknown"
  instead. This is where a `NOT NULL DEFAULT 0` destroys the difference between
  "was zero" and "was never recorded", permanently and silently.

**Artefact:** per backfill — idempotent y/n, batched y/n, prior value recoverable
y/n, historical assertion true/false/unknowable.

## 6 · The verdict line

One sentence the deploy runner can act on: what the rollback plan **is**, or that
there is none and the change is one-way. If it is one-way, say what must be true
before it ships — the pre-flight query, the backup checkpoint, the release ordering.

**Artefact:** the rollback plan, or the explicit statement that there is none.

## When this does not apply

- A migration that only creates objects that nothing has used yet in any deployed
  environment: everything is `reversible` and the procedure is a formality. Say so
  in one line rather than filling the table.
- The repo has real down migrations and a tested rollback path — then this
  procedure's premise is wrong, and it must be rewritten before it is trusted.
- The question is duration or locking — `migration-lock-risk`.
- The question is correctness against existing rows — `migration-blast-radius`.
