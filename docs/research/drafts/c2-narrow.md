# Draft — c2-narrow

Produced by `domain-researcher`, 2026-08-29. **This is a draft, not a note.** It
carries the scope contract, then the note body, then the full claim table the note
body compresses. Nothing here is verified. `primary-source-verifier` rules row by
row against the claim table.

---

# 1 · Scope contract

## 1.1 · Identifier and commission

| Field | Value |
|---|---|
| `<id>` | `c2-narrow` |
| Commission file | `/home/user/hello-world/docs/research/commissions/c2-narrow.md` |
| Candidate sentence (verbatim) | "it reviews a database migration file and produces a findings list at file:line with a verdict." |
| Commissioned by | **not stated in the commission file.** The template's `Commissioned by:` and `Sweep:` fields are absent. Recorded as a gap, not reconstructed. |
| Sweep | not stated; no re-commission section present, so read as a first sweep |

The commission also carries one question of its own: *"what goes wrong in database
migrations that is detectable in a static migration file?"* That is Q1 below.

## 1.2 · Question list

Each row names the decision a good answer lets `agent-shape` take.

| # | Question | The decision it serves |
|---|---|---|
| Q1 | Which migration operations take locks that block reads or writes, and is that determinable from the DDL statement text alone? | Which rules the agent can implement at all against a static file |
| Q2 | Which operations rewrite the whole table, and what distinguishes the rewriting form from the cheap form of the same statement? | Severity ranking, and whether a rule can fire on a statement keyword or must inspect its arguments |
| Q3 | What in a migration file breaks the *running application* rather than the database? | Whether the agent needs application-code context, or is confined to the migration file |
| Q4 | What makes a statement unsafe because of its *file or transaction context* rather than the statement itself? | Whether findings are statement-scoped (one `file:line`) or need file-level state |
| Q5 | Does the correct verdict depend on engine and engine version, and can that be read from the migration file? | Whether the agent needs a declared dialect/version input, and what it must abstain on without one |
| Q6 | What must a findings list carry for a developer to act on it, and what false-positive budget does a review-time checker have? | The finding schema: verdict vocabulary, fix suggestion, severity, and the tolerance the evals must hold it to |
| Q7 | What is *not* decidable from the migration file and needs a runtime fact? | The agent's abstention boundary — directly, the containment eval case |
| Q8 | Is there measured evidence that static migration linting prevents incidents? | Whether the agent's value claim is evidenced or is an opinion |

## 1.3 · Out-of-scope list, with reasons

| Area | Why the candidate sentence does not need it |
|---|---|
| **Database index design** | **Requested mid-task by the caller; deliberately not swept.** The artefact is a findings list about a migration file. Choosing *which* index a schema should have is a design decision taken with knowledge of the query workload, and it is not a property of the file under review. Widening the sweep here is the exact failure recorded at `docs/decomposition-agent-pipeline.md` §5. Needs its own commission — see §1.6. |
| **Query planning / EXPLAIN analysis** | Same. Requires a plan from a live database with live statistics; the migration file contains none. Nothing in the candidate sentence emits a plan or a query rewrite. |
| ORM and model design | The agent reviews the migration artefact, not the model layer that generated it. Would change the input type. |
| Runtime backfill orchestration (batching, throttling, resumability) | The safe pattern is that the backfill is *not* in the migration; the finding is "this file contains a backfill", which is Q1/Q2 territory. How to run one well is an operations procedure with a different artefact. |
| Engine selection, sizing, capacity planning | A decision taken before any migration exists. `CLAUDE.md` reserves stack decisions for Phase 2 and forbids deciding them here. |
| Migration-tool selection (Flyway / Liquibase / Alembic / ActiveRecord) | Only their *file format* is in scope, because it determines what the agent parses. Which tool to adopt is a stack decision. |
| Security review of migrations (`GRANT`, RLS, ownership) | Plausibly statically detectable and plausibly in scope, but the candidate sentence does not name it and this sweep gathered no evidence on it. Flagged so a later stage can commission it rather than assume it was covered. |
| Data-warehouse / NoSQL schema evolution | Different failure modes and different artefacts; the candidate sentence says "database migration file" in the relational DDL sense, which is what every source reached addresses. |

## 1.4 · A finding about the commission itself — recorded, not acted on

The evidence contradicts one implicit assumption in the candidate sentence. Rows
R3, R5, R12, R14 and R23 show that **the same DDL statement gets opposite verdicts
under PostgreSQL and MySQL, and under different major versions of PostgreSQL** —
and the migration file does not, in general, state which engine or version it will
run against. The sentence "it reviews a database migration file and produces a
findings list with a verdict" therefore under-specifies the agent's input: without a
declared dialect and version, a large share of the rule set can only abstain.

This is written here as a scope row. It is not acted on, and no second sweep is
started on the strength of it. `agent-shape` decides.

## 1.5 · Extend or author

**Verdict: `author database-migration-review`.**

Queries run against `/home/user/skills-repo/knowledge/notes/` before any web search:

| Query | Where | Result |
|---|---|---|
| Read `INDEX.md` in full | `/home/user/skills-repo/knowledge/INDEX.md` | 26 notes across 8 sections. No database, data-layer or migration section. Section 3b (domain evidence) covers ideation, fixation, LLM generation, requirements, architecture. |
| `migration\|schema\|ALTER TABLE\|downtime\|rollback\|database\|SQL\|index\|query plan` (case-insensitive) | all notes | 22 hits across 9 files, all incidental — `--postgres` as a Graphify CLI flag, "index" as in `INDEX.md`, "database" as in a vendor feature list |
| `migration\|ALTER TABLE\|Postgres\|MySQL\|schema change` (case-insensitive) | all notes | 5 hits, all in `graphify-features.md` and `graphify-assessment.md`, all describing a code-graph tool's Postgres *introspection* flag |
| Symptom vocabulary check: `lock`, `downtime`, `outage` | all notes | `architecture-evidence.md` covers outage mechanisms at the distributed-systems level (retry storms, metastable failure) and explicitly names *"Data — the whole data discipline"* as a gap it does not fill (`architecture-evidence.md:99`) |

No note owns this topic, and the nearest note names it as a known hole. Author.

**Cost of the alternative, for the record:** had this been `extend`, the addition
would have had to arrive as a patch a human applies, because nothing downstream in
this pipeline may rewrite an existing note. It is `author`, so that cost is not
incurred — but the reciprocal link into `architecture-evidence.md` *is* such a
patch, and it is in the back-link table at §4.

## 1.6 · What a second commission would have to say

Not written by me, and not started. Recorded so the shaping stage can act:

- Index design and query planning (the caller's mid-task request) is **wider** than
  `c2-narrow`, not narrower. Per `docs/decomposition-agent-pipeline.md` §5 the one
  permitted follow-up sweep is a *narrower* one, so this needs whoever owns the
  pipeline to authorise it as a new commission, with its own candidate sentence and
  its own `<id>`.
- Security review of migration DDL, if wanted, is the natural narrower second sweep.

## 1.7 · Search log

Protocol: `literature-review` §2–5 (search plan, log, dedup order, staged
screening). Additions in force: prefer the primary source and record when not at
one; cap lookup attempts at ~3 per source and state the uncertainty rather than
looping.

Date range: no lower bound (engine documentation is current-version); languages:
English; publication types: engine documentation, tool documentation, peer-reviewed
papers.

Inclusion: the source states a behaviour of a database engine under a DDL
operation, or states a rule a migration checker applies, or measures something about
static-analysis findings. Exclusion: blog restatements of engine documentation;
search snippets (`literature-review` §Pitfalls: *"Do not treat search snippets as
evidence"*); vendor marketing.

| Database / site | Date | Query or URL | Result | Screening outcome |
|---|---|---|---|---|
| postgresql.org/docs/current | 2026-08-29 | `sql-altertable.html` | fetched | included — primary, engine behaviour |
| postgresql.org/docs/current | 2026-08-29 | `explicit-locking.html` | fetched | included — primary |
| postgresql.org/docs/current | 2026-08-29 | `sql-createindex.html` | fetched | included — primary |
| dev.mysql.com/doc/refman/8.4 | 2026-08-29 | `innodb-online-ddl-operations.html` | fetched | included — primary |
| squawkhq.com/docs | 2026-08-29 | `/rules`, `/require-concurrent-index-creation`, `/renaming-column`, `/constraint-missing-not-valid`, `/ban-concurrent-index-creation-in-transaction`, `/adding-required-field`, `/require-lock-timeout`, `/safe_migrations` | 8 pages fetched | included — primary for the tool's own rule set; **secondary** for the engine behaviour it describes |
| github.com | 2026-08-29 | `ankane/strong_migrations` README | fetched | included — primary for the gem's rule set; secondary for engine behaviour |
| web search | 2026-08-29 | `empirical study database schema evolution co-evolution application code Qiu Li Su FSE 2013` | 10 results | primary located, **not reached** — see §5 |
| web.cs.ucdavis.edu | 2026-08-29 | `~su/publications/fse13-db-study.pdf` | attempt 1 — PDF returned as undecodable binary | excluded, unavailable full text |
| dl.acm.org | 2026-08-29 | `10.1145/2491411.2491431` | attempt 2 — HTTP 403 | excluded, unavailable full text |
| semanticscholar.org | 2026-08-29 | paper page `5f814359…` | attempt 3 — empty body | excluded; cap reached, uncertainty stated in §5 |
| web search | 2026-08-29 | `empirical study "schema migration" failures production incidents measurement percentage open source projects` | 9 results, none a primary measurement of migration-caused incidents | see §5 |
| web search | 2026-08-29 | `evaluation of database migration linter squawk strong_migrations precision recall false positives study` | 8 results, all tool docs or blog comparisons | see §5 |
| web search + cacm.acm.org | 2026-08-29 | `"Lessons from Building Static Analysis Tools at Google" pdf "effective false positive"`; then 3 fetch attempts at `cacm.acm.org/research/…`, `m-cacm.acm.org/…/fulltext`, `cacm.acm.org/magazines/…/fulltext` | all 403 | **primary unreached**; row R25 rests on a named third-party summary and says so |
| web search | 2026-08-29 | `Bessey "A Few Billion Lines of Code Later" CACM 2010 false positive rate developers ignore warnings quote` | 8 results; page not opened | excluded — snippet only, no quote, therefore no row. See §5 |

Deduplication: applied in the order DOI → arXiv/PMID → exact title → normalised
title + first author + year. **0 duplicates removed** — the reached set is 13
distinct documentation pages and 1 summary page, no overlap.

Long-source handling: `deep-reading` §1–5 was **not** invoked. No source reached was
long enough to need it; all were single documentation pages read in one pass. Its
§6–7 were not run and must not be — those are the self-test and the self-assigned
`status: verified`.

**Stopping condition, as met:** every question Q1–Q8 carries either a claim row or
an explicit "not found measured" row. No source target was set and none was met.

---

# 2 · The note body (candidate for promotion)

```yaml
---
title: Database migrations — what a static reviewer can and cannot see
sources:
  - url: https://www.postgresql.org/docs/current/sql-altertable.html
    note: PostgreSQL documentation, ALTER TABLE, "current" channel. MOVING POINTER — re-fetch and pin a major version before use
    fetched: 2026-08-29
  - url: https://www.postgresql.org/docs/current/explicit-locking.html
    note: PostgreSQL documentation, Explicit Locking, table-level lock modes. MOVING POINTER — re-fetch
    fetched: 2026-08-29
  - url: https://www.postgresql.org/docs/current/sql-createindex.html
    note: PostgreSQL documentation, CREATE INDEX, "Building Indexes Concurrently". MOVING POINTER — re-fetch
    fetched: 2026-08-29
  - url: https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html
    note: MySQL 8.4 Reference Manual, InnoDB Online DDL Operations (version-pinned)
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/rules
    note: Squawk, linter for PostgreSQL migrations — rule index
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/require-concurrent-index-creation
    note: Squawk rule, require-concurrent-index-creation
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/renaming-column
    note: Squawk rule, renaming-column
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/constraint-missing-not-valid
    note: Squawk rule, constraint-missing-not-valid
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/ban-concurrent-index-creation-in-transaction
    note: Squawk rule, ban-concurrent-index-creation-in-transaction
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/adding-required-field
    note: Squawk rule, adding-required-field
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/require-lock-timeout
    note: Squawk rule, require-lock-timeout
    fetched: 2026-08-29
  - url: https://squawkhq.com/docs/safe_migrations
    note: Squawk, "Safe Migrations" — safety requirements and lock-queue rationale
    fetched: 2026-08-29
  - url: https://github.com/ankane/strong_migrations
    note: ankane/strong_migrations README, Rails migration safety gem — rule set
    fetched: 2026-08-29
  - url: https://alastairreid.github.io/RelatedWork/papers/sadowski:cacm:2018/
    note: THIRD-PARTY SUMMARY of Sadowski, Aftandilian, Eagle, Miller-Cushon & Jaspan 2018, "Lessons from Building Static Analysis Tools at Google", CACM 61(4). The primary was NOT reached — 3 fetch attempts, all HTTP 403
    fetched: 2026-08-29
status: unverified
tags: [database, migrations, schema-change, static-analysis, failure-modes, measured-vs-repeated]
related: ["[[architecture-evidence]]"]
---
```

## Database migrations — what a static reviewer can and cannot see

Written 2026-08-29 for commission `c2-narrow`. **Every row below carries MEASURED (a
study, report or documentation page with numbers or a stated behaviour exists and
was read and quoted) or REPEATED (widely asserted, no measurement found).** The
distinction is the content; the summary is not.

One reading note that applies to the whole note. Engine *documentation* is a primary
source for the engine's behaviour, and rows resting on it are MEASURED-as-documented
with a fetch date. A migration linter's documentation is primary for **its own rule
set** and secondary for the engine behaviour it explains; rows are labelled
accordingly and never silently promoted.

### The failure modes that are visible in the file

Three separable classes, and they are separable because they need different evidence
to rule on.

**Class 1 — the statement takes a lock that stops traffic.** In PostgreSQL,
`ALTER TABLE` defaults to the strongest lock there is, and that lock excludes
readers, not only writers (R1, R2). A plain `CREATE INDEX` is gentler — writes
block, reads do not (R8). In MySQL 8.4 the picture is per-operation and published as
a table: adding a secondary index permits concurrent DML, changing a column's data
type does not (R12, R14).

**Class 2 — the statement rewrites the table.** The same keyword can be free or
catastrophic depending on its arguments. `ADD COLUMN` with a non-volatile `DEFAULT`
is a metadata change and is *"very fast even on large tables"*; `ADD COLUMN` with a
volatile default, a stored generated column, an identity column or a constrained
domain type *"will cause the entire table and its indexes to be rewritten"* (R3,
R4). `ALTER COLUMN TYPE` normally rewrites, with a narrow binary-coercible exception
(R5). This class is the strongest argument that a migration checker cannot match on
statement type alone — it has to read the arguments.

**Class 3 — the statement is fine for the database and breaks the application.**
Renaming a column *"may break existing clients"* (R19); dropping one, in Rails,
*"can cause exceptions until your app reboots"* because the ORM caches the column
list (R20); adding a `NOT NULL` column with no default breaks old application code
that does not know about it on `INSERT` (R23). Both sources assert these as design
rationale with no measurement behind them, so all three are REPEATED. They matter
anyway: they are the class where the database reports success and the incident
happens somewhere else, which is precisely the class a reviewer of the *file* is
positioned to catch and a monitor of the *database* is not.

### The verdict is not a property of the statement

Two findings sit above the rule set and constrain the agent's shape.

**Context, not the statement, decides.** `CREATE INDEX CONCURRENTLY` *"cannot"* be
performed within a transaction block (R9), and Squawk ships a rule whose entire job
is that conflict (R22). In the other direction, Squawk's concurrency requirement
*"ignores indexes added to tables created in the same transaction"* (R21) — a
statement that is a finding in one file is not a finding in another, and the
difference is several lines above it. A finding at `file:line` is therefore emitted
from file-level state, not from a line-level match.

**Engine and version decide.** Changing a column's type rewrites in PostgreSQL and
blocks reads and writes (R5); in MySQL it is *"only supported with `ALGORITHM=COPY`"*
and does not permit concurrent DML (R14). Renaming is online in MySQL when the type
and nullability are unchanged (R15) while in PostgreSQL the database-side cost is
not the issue at all (R19). And the safe form of `ADD COLUMN ... NOT NULL DEFAULT`
depends on a PostgreSQL version boundary (R23 with R3). **This is an inference
across rows R3, R5, R12, R14, R15 and R23, not a quoted claim** — but it is the one
with the largest consequence: a migration file usually does not state its target
engine or version, so an agent given only the file has to be told, or abstain.

### What a findings list has to carry

| Claim | Verdict | Number |
|---|---|---|
| Code-review-time checks should sit under 10% *effective* false positives, where an effective false positive includes a real fault the developer did not understand and so did not act on | **REPEATED** — the primary (Sadowski et al., CACM 61(4), 2018) was **not reached**; 3 fetch attempts, all HTTP 403. Row rests on a named third-party summary | <10% |

That is the only evidence this sweep reached on actionability, it is second-hand,
and it should be treated as a pointer to a source somebody must open rather than as
a number. It is recorded because the alternative — writing "findings must be
actionable" with nothing behind it — is the shape this base is trying to stop.

### The abstention boundary

Every row below is a case where the file is not sufficient and the quoted source
says why. This is the most directly usable section for an agent's containment case.

| The question the rule needs answered | Why the file cannot answer it | Row |
|---|---|---|
| Is this table large enough for a rewrite to matter? | The rewrite rows state the mechanism, not a threshold; on an empty or new table the same statement is free | R3, R4, R5 |
| Does the table currently contain NULLs in this column? | `SET NOT NULL` scans the table and fails if any record is NULL — a data fact | R6 |
| Is a long-running query holding a conflicting lock right now? | The blocking cascade depends on live sessions | R24 |
| Does any application code still reference this column? | The breakage is in a deployed artefact, not in the migration | R19, R20 |
| Is this index build going to collide with another concurrent build? | *"only one concurrent index build can occur on a table at a time"* — a concurrency fact | R11 |
| Did a previous concurrent build leave an INVALID index behind? | Database state from a *prior* run | R10 |

### Prior art that already does this statically

Two tools implement the rule sets above against migration text, which is direct
evidence that the class of check is implementable in a static reviewer: Squawk
(PostgreSQL, rules listed on its rule index) and `strong_migrations` (Rails). Row
R17 and R18 carry the counts, with the query that produced them.

Note also `/home/user/skills-repo/.claude/skills/expand-contract-migration/` — an
existing skill in this project's own repo covering the multi-step safe-change
pattern these rules keep pointing at. It is repo prior art, not a source, and no
claim below rests on it.

### What could not be found measured

See §5, carried verbatim into any promoted note.

---

# 3 · Claim table

Column meanings per `claim-evidence-extraction` §3. Empty cells are the output.
"Primary?" records whether the row's source is the thing itself.

| # | Q | Claim | Source | Primary? | Locator | Quote | What was measured | Effect size | Sample / population | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | Q1 | In PostgreSQL, `ALTER TABLE` acquires ACCESS EXCLUSIVE unless a subcommand is noted otherwise, and a multi-subcommand statement takes the strictest lock any subcommand needs | postgresql.org/docs/current/sql-altertable.html | yes | Notes | "An `ACCESS EXCLUSIVE` lock is acquired unless explicitly noted. When multiple subcommands are given, the lock acquired will be the strictest one required by any subcommand." | documented behaviour, not an observation | | | Docs "current" channel; version not pinned. Re-fetch against a pinned major version | **MEASURED** (documented behaviour) |
| R2 | Q1 | ACCESS EXCLUSIVE conflicts with every lock mode including ACCESS SHARE, so it blocks reads as well as writes | postgresql.org/docs/current/explicit-locking.html | yes | Table-level Lock Modes, ACCESS EXCLUSIVE | "Conflicts with locks of all modes (`ACCESS SHARE`, `ROW SHARE`, `ROW EXCLUSIVE`, `SHARE UPDATE EXCLUSIVE`, `SHARE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, and `ACCESS EXCLUSIVE`). This mode guarantees that the holder is the only transaction accessing the table in any way." | documented behaviour | | | moving pointer, re-fetch | **MEASURED** (documented behaviour) |
| R3 | Q2 | `ADD COLUMN` with a **non-volatile** DEFAULT stores the default in metadata and is fast even on large tables | postgresql.org/docs/current/sql-altertable.html | yes | Notes | "When a column is added with `ADD COLUMN` and a non-volatile `DEFAULT` is specified, the default value is evaluated at the time of the statement and the result stored in the table's metadata, where it will be returned when any existing rows are accessed. The value will be only applied when the table is rewritten, making the `ALTER TABLE` very fast even on large tables." | documented behaviour | | | "fast" is unquantified — the source states no time bound. Version boundary not stated on this page | **MEASURED** (documented behaviour) |
| R4 | Q2 | `ADD COLUMN` with a volatile DEFAULT, a stored generated column, an identity column, or a constrained domain type rewrites the whole table and its indexes | postgresql.org/docs/current/sql-altertable.html | yes | Notes | "Adding a column with a volatile `DEFAULT` (e.g., `clock_timestamp()`), a stored generated column, an identity column, or a column with a domain data type that has constraints will cause the entire table and its indexes to be rewritten. Adding a virtual generated column never requires a rewrite." | documented behaviour | | | no duration or size threshold given | **MEASURED** (documented behaviour) |
| R5 | Q2 | `ALTER COLUMN TYPE` normally rewrites the table and its indexes, with a binary-coercible / unconstrained-domain exception | postgresql.org/docs/current/sql-altertable.html | yes | Notes | "Changing the type of an existing column will normally cause the entire table and its indexes to be rewritten. As an exception, when changing the type of an existing column, if the `USING` clause does not change the column contents and the old type is either binary coercible to the new type or an unconstrained domain over the new type, a table rewrite is not needed." | documented behaviour | | | whether a given type pair is binary coercible is not in the migration file | **MEASURED** (documented behaviour) |
| R6 | Q1, Q7 | `SET NOT NULL` scans the entire table unless a valid CHECK constraint already proves no NULL can exist | postgresql.org/docs/current/sql-altertable.html | yes | Notes | "`SET NOT NULL` may only be applied to a column provided none of the records in the table contain a `NULL` value for the column. Ordinarily this is checked during the `ALTER TABLE` by scanning the entire table, unless `NOT VALID` is specified; however, if a valid `CHECK` constraint exists (and is not dropped in the same command) which proves no `NULL` can exist, then the table scan is skipped." | documented behaviour | | | whether such a CHECK exists is schema state, not file state | **MEASURED** (documented behaviour) |
| R7 | Q1 | `ADD CONSTRAINT ... NOT VALID` skips the table scan and commits immediately | postgresql.org/docs/current/sql-altertable.html | yes | Notes | "The main purpose of the `NOT VALID` constraint option is to reduce the impact of adding a constraint on concurrent updates. With `NOT VALID`, the `ADD CONSTRAINT` command does not scan the table and can be committed immediately." | documented behaviour | | | | **MEASURED** (documented behaviour) |
| R8 | Q1 | A normal `CREATE INDEX` blocks writes but not reads for the duration of a single table scan | postgresql.org/docs/current/sql-createindex.html | yes | Building Indexes Concurrently | "Normally PostgreSQL locks the table to be indexed against writes and performs the entire index build with a single scan of the table. Other transactions can still read the table, but if they try to insert, update, or delete rows in the table they will block until the index build is finished." | documented behaviour | | | duration depends on table size — not in the file | **MEASURED** (documented behaviour) |
| R9 | Q4 | `CREATE INDEX CONCURRENTLY` cannot be run inside a transaction block, while a regular `CREATE INDEX` can | postgresql.org/docs/current/sql-createindex.html | yes | Building Indexes Concurrently | "Another difference is that a regular `CREATE INDEX` command can be performed within a transaction block, but `CREATE INDEX CONCURRENTLY` cannot." | documented behaviour | | | | **MEASURED** (documented behaviour) |
| R10 | Q7 | A failed concurrent index build leaves an INVALID index behind that is ignored for queries but still costs update overhead | postgresql.org/docs/current/sql-createindex.html | yes | Building Indexes Concurrently | "If a problem arises while scanning the table, such as a deadlock or a uniqueness violation in a unique index, the `CREATE INDEX` command will fail but leave behind an \"invalid\" index. This index will be ignored for querying purposes because it might be incomplete; however it will still consume update overhead." | documented behaviour | | | detecting the leftover requires database state | **MEASURED** (documented behaviour) |
| R11 | Q7 | Only one concurrent index build can run on a table at a time, and no schema modification is allowed while any index is building | postgresql.org/docs/current/sql-createindex.html | yes | Building Indexes Concurrently | "Regular index builds permit other regular index builds on the same table to occur simultaneously, but only one concurrent index build can occur on a table at a time. In either case, schema modification of the table is not allowed while the index is being built." | documented behaviour | | | | **MEASURED** (documented behaviour) |
| R12 | Q1, Q5 | In MySQL 8.4 InnoDB, adding a secondary index permits concurrent DML and does not rebuild the table | dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html | yes | Index Operations table | "The table remains available for read and write operations while the index is being created." | documented behaviour | Permits Concurrent DML: Yes; Rebuilds Table: No | | version-pinned to 8.4; other versions not checked | **MEASURED** (documented behaviour) |
| R13 | Q2, Q5 | In MySQL 8.4 InnoDB, dropping a column permits concurrent DML but **does** rebuild the table | dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html | yes | Column Operations table | table row: Permits Concurrent DML **Yes**, Rebuilds Table **Yes** | documented behaviour | | | the row is a table cell, not a sentence — the verifier should confirm the cell values directly | **MEASURED** (documented behaviour) |
| R14 | Q2, Q5 | In MySQL 8.4 InnoDB, changing a column's data type does **not** permit concurrent DML, rebuilds the table, and is only supported with ALGORITHM=COPY | dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html | yes | Column Operations table | "Changing the column data type is only supported with `ALGORITHM=COPY`." | documented behaviour | Permits Concurrent DML: No; Rebuilds Table: Yes | | | **MEASURED** (documented behaviour) |
| R15 | Q3, Q5 | In MySQL 8.4, renaming a column is online only if the data type and `[NOT] NULL` attribute are unchanged | dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html | yes | Column Operations table | "To permit concurrent DML, keep the same data type and only change the column name. When you keep the same data type and `[NOT] NULL` attribute, only changing the column name, the operation can always be performed online." | documented behaviour | | | | **MEASURED** (documented behaviour) |
| R16 | Q2, Q5 | In MySQL 8.4, adding a column does not permit concurrent DML when the column is auto-increment | dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html | yes | Column Operations table | "Concurrent DML is not permitted when adding an auto-increment column. Data is reorganized substantially, making it an expensive operation. At a minimum, `ALGORITHM=INPLACE, LOCK=SHARED` is required." | documented behaviour | | | | **MEASURED** (documented behaviour) |
| R17 | Q1 | Squawk implements 40 named rules over PostgreSQL migration SQL text | squawkhq.com/docs/rules | yes (for the tool) | rule index page | rule slugs listed include "adding-field-with-default", "ban-drop-column", "changing-column-type", "constraint-missing-not-valid", "require-concurrent-index-creation", "renaming-column", "require-lock-timeout" | count of named rule slugs | 40 | | **This is a count I made, not a number the source states.** Query: fetch of `/docs/rules` on 2026-08-29; unit = one rule slug listed on that page. The verifier should recount | **MEASURED** (documented behaviour), count derived |
| R18 | Q1, Q3 | `strong_migrations` names 20 operation classes it treats as unsafe in Rails migrations | github.com/ankane/strong_migrations | yes (for the gem) | README, unsafe-operations headings | headings include "Removing a column", "Changing the type of a column", "Renaming a column", "Adding a check constraint", "Adding an index non-concurrently", "Backfilling data", "Setting NOT NULL on an existing column" | count of unsafe-operation headings | 20 | | **Count derived by me from the fetched heading list, not stated by the source.** Unit = one heading. Recount on verification | **MEASURED** (documented behaviour), count derived |
| R19 | Q3 | Renaming a column may break existing clients | squawkhq.com/docs/renaming-column | primary for the tool's rationale; **secondary** for the client-breakage behaviour | rule page, Problem | "Renaming a column may break existing clients." | nothing — asserted as design rationale | | | no measurement offered; "may" is unquantified | **REPEATED** |
| R20 | Q3 | In Rails, dropping a column can raise exceptions until the app reboots, because ActiveRecord caches the column list at runtime | github.com/ankane/strong_migrations | primary for the gem's rationale; secondary for ActiveRecord behaviour | README, "Removing a column" | "Active Record caches database columns at runtime, so if you drop a column, it can cause exceptions until your app reboots." | nothing — asserted as rationale | | | framework-specific; does not generalise beyond Rails | **REPEATED** |
| R21 | Q4 | A concurrency requirement rule must exempt indexes on tables created in the same transaction — i.e. it needs file-level context | squawkhq.com/docs/require-concurrent-index-creation | yes (for the tool) | rule page | "This rule ignores indexes added to tables created in the same transaction." | documented tool behaviour | | | | **MEASURED** (documented behaviour) |
| R22 | Q4 | The transaction context, not the statement, decides whether `CREATE INDEX CONCURRENTLY` is legal — and a linter can check exactly that | squawkhq.com/docs/ban-concurrent-index-creation-in-transaction | yes (for the tool); engine constraint independently confirmed at R9 | rule page | "While regular index creation can happen inside a transaction, this is not allowed when the `CONCURRENTLY` option is used." | documented tool behaviour | | | | **MEASURED** (documented behaviour) |
| R23 | Q3, Q5 | Adding a NOT NULL column with no default fails on a populated table and breaks application code unaware of the column; a non-volatile DEFAULT on Postgres 11+ is the safe form | squawkhq.com/docs/adding-required-field | primary for the rule; **secondary** for the engine behaviour (the engine side is independently at R3) | rule page, Problem / Solution | "Adding a new column that is `NOT NULL` and has no default value to an existing table effectively makes it required." | nothing measured; rationale plus a version boundary | | | the "Postgres 11+" boundary was paraphrased on the fetched page rather than quoted — the verifier should re-read for a verbatim version statement | **REPEATED** |
| R24 | Q1, Q7 | A migration waiting for an ACCESS EXCLUSIVE lock queues subsequent queries behind it; a short `lock_timeout` (~1s) and `statement_timeout` (~5s) plus retry is the recommended mitigation | squawkhq.com/docs/safe_migrations, squawkhq.com/docs/require-lock-timeout | primary for the recommendation; no primary measurement of the cascade reached | "Safety requirements" | "Set a short `lock_timeout` (e.g. 1 second) within Postgres when running your migrations."; "Set a `statement_timeout` (e.g. 5 seconds) to prevent runaway migrations from using too many resources & holding locks for too long."; "You must configure a `lock_timeout` to safely apply migrations." | nothing — a recommendation | 1s / 5s are the source's examples, **not measured optima** | | the cascade mechanism is asserted, not measured; the numbers are illustrative and must not be repeated as thresholds | **REPEATED** |
| R25 | Q6 | Code-review-time static checks should have under 10% *effective* false positives, where an effective false positive includes a real fault the developer did not understand and did not act on | alastairreid.github.io/RelatedWork/papers/sadowski:cacm:2018/ — **a third-party summary** | **NO.** Primary = Sadowski, Aftandilian, Eagle, Miller-Cushon & Jaspan, "Lessons from Building Static Analysis Tools at Google", CACM 61(4), 2018. **NOT REACHED** — 3 fetch attempts, all HTTP 403 | summary page | "Code review checks should have less than 10% effective false positives (but still need to be understandable, actionable and easy to fix)." | not established — the summary does not say whether 10% is measured, a policy, or a rule of thumb | <10%, kind of number **unknown** | not stated in the summary | **The highest-risk row in this table.** The number is quoted from a summary, not from the study. Whether 10% is an observed rate or a normative target is exactly the distinction that produced this project's Fischhoff error. Do not promote without opening the primary | **REPEATED** |

**Verdict counts:** MEASURED 20 (R1–R18 documented behaviour, of which R17 and R18
carry counts I derived rather than quoted; R21, R22) · REPEATED 5 (R19, R20, R23,
R24, R25) · total 25 rows.

---

# 4 · Back-link table

`related:` is a graph and one author writes one side of it. I cannot edit an
existing note; these are the lines a human applies.

| Neighbour | Exists? | Names this note back? | The exact `related:` line a human would add |
|---|---|---|---|
| `architecture-evidence` | **yes** — `/home/user/skills-repo/knowledge/notes/architecture-evidence.md` | **no** | in its frontmatter line 24, replace with:<br>`related: ["[[design-fixation-and-anchoring]]", "[[requirements-discovery]]", "[[subagents]]", "[[agent-design-template]]", "[[database-migration-review]]"]`<br>Rationale: its gap table at line 99 names *"Data \| The whole data discipline"* as absent; this note fills one cell of it |
| `INDEX.md` | yes | n/a — it is the map of content | add under a new or existing domain-evidence heading:<br>`- [[database-migration-review]] — what a static reviewer of a migration file can see, what needs the live database, and why the verdict depends on engine and version` |

No other note in the base contains database or migration vocabulary (see §1.5
queries), so no further reciprocal links are claimed. **No wikilink in this draft
points at a note that does not exist** — `architecture-evidence` was confirmed
present by reading it, which is the check the base currently fails in four places.

---

# 5 · What could not be found measured

Distinguish this from §1.3: below is "we looked and found nothing"; §1.3 is "we did
not look, and here is why".

| Question | What was searched | Finding |
|---|---|---|
| Q8 — does static migration linting prevent incidents? | `evaluation of database migration linter squawk strong_migrations precision recall false positives study` (2026-08-29, 8 results: tool docs and blog comparisons only) | **No evaluation of any migration linter was found.** No precision, recall, false-positive rate, or incident-reduction measurement exists in the reached literature for Squawk, `strong_migrations`, or any comparable tool. Every rule in R17–R23 is a tool author's judgement about a documented engine behaviour, not a measured intervention. **Consequence for `agent-shape`:** the agent's rules are well-grounded in engine behaviour and entirely ungrounded in outcome. A claim that the agent "prevents outages" would have nothing behind it |
| Q8 — how often do migrations cause production incidents? | `empirical study "schema migration" failures production incidents measurement percentage open source projects` (2026-08-29, 9 results) | **Nothing measured found.** No source reached measures the incidence or cost of migration-caused outages. The frequency premise of the whole agent is unevidenced by this sweep |
| Q2, background — how often do schemas change, and do code and schema co-evolve? | Qiu, Li & Su, "An Empirical Analysis of the Co-evolution of Schema and Code in Database Applications", ESEC/FSE 2013. **3 fetch attempts, cap reached:** `web.cs.ucdavis.edu/~su/publications/fse13-db-study.pdf` (PDF returned as undecodable binary; local PDF rendering unavailable), `dl.acm.org/doi/10.1145/2491411.2491431` (HTTP 403), Semantic Scholar paper page (empty body) | **Primary not reached; no claim row written.** A search-engine gloss states "ten popular large open-source database applications, totaling over 160K revisions" — **this number is not in this draft's claim table and must not be quoted as evidence**, because I did not open the paper. It is recorded only as a pointer for whoever can reach it |
| Q6 — what false-positive rate do developers tolerate in a static findings list? | `Bessey "A Few Billion Lines of Code Later" CACM 2010 false positive rate developers ignore warnings quote` (2026-08-29, 8 results). **The page was not opened.** | **No row written.** Search snippets describe a "below 20%" false-positive target and a claim that developers mark misunderstood real bugs as false positives. Per `literature-review` §Pitfalls — *"Do not treat search snippets as evidence"* — none of this is in the claim table. If Q6 matters to the agent's design, this source and Sadowski et al. both need opening by someone who can reach them |
| Q6 — what verdict vocabulary and severity scheme do migration reviewers use? | Covered incidentally by the Squawk and `strong_migrations` fetches; no source reached states a severity model or a finding schema | **Nothing found.** Neither tool's documentation, as reached, defines severity levels or a finding schema. The agent's verdict vocabulary would be invented, and that belongs in the spec's open questions rather than presented as practice |
| Q5 — how does a reviewer learn the target engine and version? | No source reached addresses this; it surfaced as an inference across R3, R5, R12, R14, R15, R23 | **Nothing found.** No convention was located for declaring the target engine inside a migration file. This is the largest unresolved input-design question for the agent |

---

# 6 · Handoff

- **Status:** `unverified`. Nothing in this file is evidence yet.
- **Claim count:** 25 rows — 20 MEASURED, 5 REPEATED. Two rows (R17, R18) carry
  counts I derived rather than quoted, and both say so.
- **Next:** `primary-source-verifier`, an agent that did not write these rows,
  opens each source and rules row by row. It writes `verified_by:`. I do not, and I
  am the last agent who could have claimed to have checked this, which is why I have
  not.
- **Verifier's priority order, by risk:** R25 (number quoted from a summary, kind of
  number unknown — the Fischhoff shape) · R17 and R18 (derived counts) · R23
  (version boundary paraphrased, not quoted) · R13 (a table cell, not a sentence) ·
  the four PostgreSQL `docs/current` rows, which are moving pointers and must be
  re-fetched against a pinned major version rather than trusted.
- **Then:** `agent-shape` reads §1.3, §1.4 and §5 to decide what the agent can be
  asked to do, and whether to commission the security sweep (narrower, permitted) or
  escalate the index-design/query-planning request (wider, needs the pipeline owner).
