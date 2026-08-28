# Statement shapes → the question each one raises

**This file carries no durations, no lock names and no version numbers.** Those
move, and a number remembered inside a procedure is wrong on a schedule nobody
watches. Each row names what to look up live for the server version established at
step 2, and the trap that shape is known for.

| Shape | Look up for this version | The trap |
|---|---|---|
| `CREATE INDEX` | lock taken, and whether it blocks writes or reads | The concurrent form exists precisely because the plain form is not free. On a large table the build is O(rows). |
| `CREATE INDEX CONCURRENTLY` | its transaction restriction, and what an interrupted build leaves behind | It cannot live in a file that is wrapped in a transaction; and a failed build leaves an invalid index that must be dropped by hand. |
| `CREATE UNIQUE INDEX` (incl. partial) | as above, plus the failure mode on duplicate rows | **It is a data check disguised as DDL.** If existing rows violate it, the statement fails and the deploy fails. Whether duplicates exist is a data question, not a lock question — hand it to `migration-blast-radius`. |
| `ADD COLUMN` with a constant default | whether this version rewrites the table | The version boundary here is the single most commonly misremembered fact in migration review. |
| `ADD COLUMN` with a **volatile** default or an expression | whether the rewrite exemption applies | The exemption that makes the constant case free does not extend to every default. |
| `ADD COLUMN ... NOT NULL` with no default | what it does when the table is non-empty | Fails outright, or rewrites — either way it is not the same statement as the defaulted form. |
| `ALTER COLUMN TYPE` | rewrite, and whether any type pair is exempt | Rewrites plus a full-table lock; the exemptions are narrow and version-specific. |
| `ALTER COLUMN SET NOT NULL` | whether a validated check constraint can substitute for the scan | The two-step form exists because the direct form scans the table under lock. |
| `ADD CONSTRAINT ... FOREIGN KEY` / `CHECK` | the `NOT VALID` + `VALIDATE` split, and the lock each half takes | Adding and validating in one statement scans the whole table under a stronger lock than validating separately. |
| `ALTER TYPE ... ADD VALUE` (enum) | its transaction restriction on this version, and whether the new value is usable in the same transaction | Two different restrictions that changed in different releases; check both, not one. |
| `DROP COLUMN` / `DROP TABLE` | lock, and whether the storage is reclaimed | Cheap to execute and impossible to undo — the cost is in `migration-reversibility`, not here. |
| `UPDATE` / `INSERT ... SELECT` (a backfill) | nothing version-specific; the question is size | Row locks and transaction size, not DDL locks. An unbatched backfill of a large table holds locks and bloats until it finishes or is killed. Route the correctness half to `migration-blast-radius`. |
| `RENAME` anything | lock, and what the running application does | The lock is brief; the outage is that deployed code still uses the old name. That is a blast-radius finding. |

## The shape that is not in this table

If the statement's shape is not listed, do not map it to the nearest row here.
Look it up live, and add a row to this file naming what you found and where you
read it. A table that silently absorbs unfamiliar statements into familiar rows is
worse than a short table.
