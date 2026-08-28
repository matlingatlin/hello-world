---
name: migration-lock-risk
description: "Use when a migration is about to be applied to a database that has traffic on it — an index added, a column added or altered, a constraint added, a type changed, an enum extended, or any DDL someone calls non-blocking. Decides, per statement, which lock it takes, what that lock blocks, whether the table is rewritten, and whether the statement can run inside the migration tool's transaction at all. Emits a per-statement lock table, not a verdict on the whole file. NOT for whether the change breaks existing data or code (use migration-blast-radius), NOT for how to get back (use migration-reversibility), NOT for schema design (that is architect's job)."
---

# What this does to a database with traffic on it

A migration file is read as a unit and applied as a sequence. The unit view is
where the danger hides: one statement in fifteen holds an `ACCESS EXCLUSIVE` lock,
or cannot run inside a transaction at all, and the other fourteen are irrelevant to
what happens at 09:00 on a Tuesday. **The artefact is a table with one row per
statement.** A paragraph about the file is not an output of this procedure.

The rule that overrides what a competent reader naturally does: **do not answer
lock questions from memory.** Lock, rewrite and transaction behaviour is
version-dependent — the same `ADD COLUMN ... NOT NULL DEFAULT` rewrites the whole
table on one major version and is a catalogue update on the next. A remembered
answer is right often enough to be trusted and wrong exactly where it costs an
outage. Read it live, and cite the version you read it for.

Open `references/statement-shapes.md` at step 3. It says which question each
statement shape raises; it deliberately carries no lock durations or version
numbers, because those move.

## 1 · Enumerate the statements

Every executable statement in the file, in order, numbered, at `file:line`.
Comments are not statements — but a comment that makes a safety claim is recorded
now as a claim to be checked, with its line.

**Artefact:** the numbered statement list, and the claim list.

## 2 · Establish the two facts the whole table depends on

- **The server version.** From the repo (ADR, IaC, compose file, connection
  target). If it cannot be established, say so in the document and answer every
  later question for the **oldest plausible version**, marked as such.
- **The transaction wrapper.** Does the tool wrap this file in one transaction?
  For `prisma migrate deploy` in this repo, look it up live for the version in
  `apps/api/package.json`; do not assume either way.

**Artefact:** two lines — version (with where it came from), wrapper (with where it
came from). "Assumed" is an allowed value and must be written as such.

## 3 · One row per statement

For each statement, opening `references/statement-shapes.md` for the shape:

| Column | What goes in it |
|---|---|
| # / `file:line` | the statement |
| lock mode | the named lock, for the version from step 2 |
| blocks | **reads? writes? both?** — the operational fact, not the lock's name |
| rewrite | does the table get rewritten, or is this catalogue-only |
| duration class | O(1) catalogue change · O(rows) scan or build · unbounded (waits on another session) |
| source | where the behaviour was read, with the version |

A row whose `blocks` cell says "may block" is not finished. Reads, writes, or both.

**Artefact:** the lock table, every statement present, no cell empty.

## 4 · Find the statements that cannot run where they are

Some DDL cannot run inside a transaction block, and some cannot run in the same
transaction that created what it uses. When the wrapper from step 2 and the
statement disagree, the migration **fails on apply** — the loudest possible
outcome, but only if someone looked. Check each statement against the wrapper, not
against the file as a whole.

For each conflict: the statement, what the tool does when it errors mid-deploy, and
what state that leaves the migration history in.

**Artefact:** the conflict list, with the resulting state named. Empty is a valid
and common result — write "none", not nothing.

## 5 · The queue behind the shortest lock

A lock held for milliseconds still queues. An `ACCESS EXCLUSIVE` request waits
behind the longest-running transaction currently touching that table, and
**everything arriving after it queues behind the request**, reads included. A
"fast" statement therefore stalls the table for as long as the slowest query in
flight, which is where "instant" migrations take sites down.

For every statement taking an exclusive lock: name the longest-running query that
touches that table (search the code for it), and say whether a `lock_timeout` and
a retry are set. If they are not, that is a finding.

**Artefact:** per exclusive-lock statement — the longest query found at `file:line`,
and present/absent for `lock_timeout`.

## 6 · Verdict per statement, then per file

`safe on a live database` · `safe with a stated precondition` (name it —
`lock_timeout`, off-peak, a separate file) · `not safe as written` (name the shape
that would be).

The file's verdict is the worst statement's verdict. A single unsafe statement does
not average out against fourteen safe ones.

**Artefact:** the verdict column, and one sentence naming the statement that set
the file's verdict.

## When this does not apply

- **No live traffic** — a fresh database, or a table that does not exist yet in any
  deployed environment. Say that is why, and stop; the lock table would be noise.
- The change is application code, not DDL. Different job.
- The question is whether the change is *correct* — `migration-blast-radius`.
- The question is how to get back — `migration-reversibility`.
