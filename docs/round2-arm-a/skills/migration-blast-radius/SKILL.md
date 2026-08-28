---
name: migration-blast-radius
description: "Use when reviewing a migration for what it breaks in data and code that already exist — a constraint or unique index meeting rows that are already there, a column or enum value removed, a type narrowed, a backfill that writes a wrong value, or a schema file and a SQL file that no longer say the same thing. Also use when asked whether the running application survives the window between the migration applying and the new code deploying. Emits findings at file:line, each with the concrete consequence and the query that would settle it. NOT for lock and downtime analysis (use migration-lock-risk), NOT for rollback (use migration-reversibility)."
---

# What it breaks that is already there

A migration is written against the schema in the author's head. It is applied
against rows that exist and executed alongside code that is already deployed. This
procedure reads those two, not the intention.

The rule that overrides the natural reading: **a migration file is not the unit of
review; a statement plus the rows it will meet is.** The most expensive findings in
this class are invisible in the SQL — a `UNIQUE` index is valid SQL and correct
design and still fails on apply, because the duplicates it forbids are already in
the table. Every constraint in a migration is a **claim about existing data**, and
a claim about data is settled by a query, not by reading.

## 1 · Read the claims, then set them aside

Migrations here carry long comments explaining why they are right. List each claim
with its line — "the invariant four code paths promised", "non-blocking", "safe
because". You will check each one at step 5.

The reason for the separation is measured: a solution held in context produces
narrow, source-bound restatements. A well-argued comment is the strongest form of
that pull. Record the claims so you can check them rather than absorb them.

**Artefact:** the claim list, at `file:line`. Empty is a real answer.

## 2 · Every constraint is a query against existing data

For each `UNIQUE`, `NOT NULL`, `CHECK`, `FOREIGN KEY`, primary key, or type
narrowing: write **the exact SELECT that returns the rows which would break it**,
and say what happens when it returns more than zero.

This is the step that produces the findings nobody else produces, and it is the one
that is skipped, because the constraint reads as obviously desirable. Desirable and
appliable are different questions.

Then ask the second half, which is skipped even more often: **who repairs the rows
the constraint cannot accept?** A constraint prevents new violations. It does not
fix old ones — and if the migration's own comment says the old code could produce
them, then the rows are there, and the migration is incomplete without a repair
step.

**Artefact:** per constraint — the SELECT, the consequence of a non-zero result,
and named repair or `repair missing`.

## 3 · The SQL and the schema file must say the same thing

Every column, type, nullability, default and enum value the SQL touches, checked
against the ORM schema (`apps/api/prisma/schema.prisma`) at `file:line` on both
sides. In this repo the rule is explicit — *"Adding a column means a migration and
a schema change — never one without the other"* (`apps/api/CLAUDE.md`).

Check the nullability decision against **how the same concept is modelled
elsewhere**. Where one table stores a value as nullable so that absence is a claim
rather than a number, and another stores it `NOT NULL DEFAULT 0`, the second cannot
distinguish "spent nothing" from "we never knew". For rows that already exist and
are backfilled with the default, that distinction is destroyed permanently — which
is a data-loss finding, even though nothing was deleted.

**Artefact:** a match/mismatch line per touched column, with both `file:line`s; and
a nullability note wherever two tables model the same concept differently.

## 4 · The old code runs during the window

Between the migration applying and the new code being live, **deployed code runs
against the new schema.** For each affected table, grep every read and write in the
application and sort them:

| Class | Meaning |
|---|---|
| tolerant | old code neither writes the changed column nor depends on its absence |
| breaks-on-apply | old code writes a now-forbidden value, or reads a column that is gone |
| breaks-on-rollback | new data is written that old code, if redeployed, cannot read |

A column added with a default is usually tolerant. A removal, a rename, a
narrowing, or a new value in an enum is usually not — an added enum value is
written by new code and can reach old readers with a narrower type.

**Artefact:** the table → class table, each class backed by a `file:line`.

## 5 · Check each claim from step 1

Confirmed, contradicted, or unverifiable — each with what you checked it against.
A claim that cannot be checked from the repo is a finding in its own right: the
migration is asserting something no reader can verify.

**Artefact:** claim → verdict → evidence.

## 6 · Findings

One row each: `file:line` · what is wrong · the concrete consequence · severity
(**blocks the deploy** · **corrupts or loses data** · **breaks the running app** ·
**degrades**) · what would fix it.

"Could cause issues" is not a consequence. Name the row, the query, or the request
that fails.

**Artefact:** the findings table. **Zero findings is a valid outcome** and must be
written as an explicit line — "no blast-radius findings; checked constraints
against existing data, schema parity, and N call sites" — never as an omitted
section.

## When this does not apply

- The table is new in this migration and no deployed code touches it: steps 2 and 4
  are vacuous. Say so; do not manufacture rows.
- The concern is duration or locking — `migration-lock-risk`.
- The concern is undo — `migration-reversibility`.
- The concern is whether the schema *design* is right at all — that is `architect`,
  and it arrives as an ADR, not as a review finding.
