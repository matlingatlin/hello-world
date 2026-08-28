# Baseline — what an unaided review of a migration actually gets wrong

One subagent, no skills, no agent definition, no checklist, was given
`evals/fixtures/0013_billing_period_hazardous.sql` plus the repo and asked to review it. The
point of the run is that a procedure may only contain what was *observed* to fail: roughly
one task in seven measurably gets worse when a skill is added, concentrated exactly where
the model was already competent, and without a baseline you cannot tell which way yours
pushed.

## Already competent — do not teach these

The unaided review found, unprompted and correctly:

- `DROP COLUMN project.deleted_at` breaks six live query paths and destroys data — and it
  checked the file's "soft delete never shipped" comment against the source and found it
  false, citing `project.service.ts:114` and five read paths.
- `RENAME COLUMN` is not survivable under rolling deploys; needs expand/contract.
- Whole-table `UPDATE` + non-concurrent `CREATE INDEX` + five `ACCESS EXCLUSIVE` locks held
  across one Prisma transaction is an outage; `CONCURRENTLY` cannot run inside it.
- No `lock_timeout`, so a slow reporting query makes the first `ALTER` queue everything.
- `schema.prisma` drift will be reverted by the next `migrate dev`.

**Consequence for the package:** the lock table in `postgres-migration-hazards` is not there
to teach lock analysis. It is there to make it *exhaustive and cheap* on a long file, and to
hold the exact safe rewrite so the finding ships with a patch rather than a warning. The
statements a review must NOT flag (`ADD COLUMN ... NOT NULL DEFAULT <constant>` is
catalog-only) matter as much as the ones it must.

## Observed failures — this is what the agent exists to fix

1. **Severity inflation.** Nine of thirteen findings were marked blocking, including
   `schema.prisma` drift, "five unrelated changes in one file", a missing rollback note, and
   un-updated docs. All real; none can lose data or break the running system. When
   everything blocks, the author cannot find the finding that ends their week.
   → the three-level rubric in the agent, with the inflation case named explicitly.
2. **Premise checking was done, but only by luck of ordering.** It caught the false "never
   shipped" comment on the statement it happened to investigate first, and then found two
   more untrue assertions (`ADD CONSTRAINT` on an FK that already exists from `0001_init`;
   `SET NOT NULL` on a column that is already `NOT NULL`) only while chasing other findings.
   Nothing in an unaided review makes that a *pass*, so on a longer file it is a coin flip.
   → Pass 0 in the agent, and the "will this even apply?" section in the hazards skill.
3. **No named recovery route.** It said "no down migration or rollback plan" but never
   distinguished *forward fix* from *prepared compensating migration* from
   *restore-from-backup-and-lose-every-write-since*. Those are different conversations with
   an operator, and the third is what makes a `DROP` different in kind.
   → the three routes in `migration-rollout-plan`, required by name in the report.
4. **The compatibility test was implicit.** It reasoned about old code against new schema
   correctly, and never asked the other half: does the *previous* release still run if the
   code is rolled back and the schema stays? → both halves, in writing, Pass 4.
5. **Recommended rejection over iteration.** "My recommendation is to reject rather than
   iterate" is not a reviewable output — the author cannot act on it. Every finding needs the
   replacement SQL. → the report's `Change:` field is mandatory per finding.

## Findings the baseline produced that the draft package had missed

Folded back in, because a baseline measures the builder too:

- A constant `DEFAULT` that is never dropped silently misfiles every *future* row — a
  correctness bug on a billing table that no lock analysis would surface.
- A derived `TEXT` column with no `CHECK` and no `GENERATED ALWAYS AS ... STORED` can drift
  from its source; and deriving a month from `TIMESTAMP(3)` *without* time zone misfiles the
  boundary hours of every month.
- A statement that aborts does not merely roll back: Prisma marks the migration failed and
  the deploy pipeline stops until someone runs `prisma migrate resolve` by hand.
- This repo guards migrations with `IF NOT EXISTS` (0006, 0008, 0010, 0011, 0012); a file
  that does not cannot be retried after a partial manual apply.
- A new index can be redundant against an existing one (`0008` already covers
  `(workspace_id, created_at)`), and a second index on the hottest insert path is not free.
