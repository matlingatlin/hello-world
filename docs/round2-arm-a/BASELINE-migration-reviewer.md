# Baseline — what an unaided run gets wrong, and what it gets right

Produced by `agent-baseline`, between the spec and assembly.

**Deviation, stated first because it qualifies everything below:** the procedure
asks for **at least two** independent unaided runs, because a single run cannot
separate a systematic failure from a bad draw. This run was capped at two subagent
dispatches in total, and the second was needed for the independent test. **One
baseline run was observed.** Every row below is therefore a **draw** in the
procedure's own vocabulary — reproduced by nobody. That is not a footnote: it means
no row here has earned the status of "systematic", and the skills built from them
are built on one observation.

## 1 · The task, verbatim

Dispatched to a `general-purpose` subagent with no guidance, no spec, and no
skills. Prompt as given:

> You are reviewing database migrations in the repository at /home/user/hello-world
> before they ship. You have no prior context from any other conversation.
>
> Review these three migrations as a set, as if they were about to be applied to
> the production database of a live multi-tenant SaaS:
> `0006_indexes_and_one_current`, `0009_usage_kind_intake`, `0012_job_spend`.
> Context you may read: `apps/api/prisma/schema.prisma` and the surrounding app
> code. The database is PostgreSQL, managed by Prisma Migrate.
>
> Deliverable: (1) a findings list, each with file and line, what is wrong, and the
> consequence; (2) an overall verdict — ship, ship with changes, or not ship;
> (3) a short rationale describing how you went about the review.
>
> Be as thorough or as brief as you judge appropriate. Do not ask for
> clarification. Do not modify any file in the repository.

Real migrations from this repo, chosen because they carry three different risk
shapes: a unique index meeting existing data, an enum extension, and a defaulted
column add. Output: `baseline-run-1.md`, 14 findings, ~2,800 words, 27 tool calls.

## 2 · What it got wrong

| # | What it did | Consequence | Both runs? |
|---|---|---|---|
| B1 | **Emitted prose, not tables.** Fourteen findings in paragraphs. There is no per-statement row anywhere: 0006 has 18 statements and the review names 4 of them. A reader cannot tell whether statement 11 was examined and cleared, or never read. | Coverage is unauditable. A reviewer that examined 4 of 18 and one that examined 18 and found 4 produce the identical document — so the document cannot be trusted as a record of what was checked. | single run |
| B2 | **Asserted production lock behaviour on a version it had just said it could not establish.** F10: *"the production server version is not pinned anywhere in the repo that I could find."* Then F13: *"`ADD COLUMN … NOT NULL DEFAULT <constant>` on PG 11+ is a catalog-only change"* — offered as the reason 0012 is *"a non-event"*, with the version caveat dropped. | The reason to review at all is that "non-blocking on modern Postgres" is exactly the claim that is right until it is not. The caveat was raised in one finding and spent in another. | single run |
| B3 | **No systematic rollback treatment.** Reversibility appears only where the run happened to notice it (F8's enum, F12's default). 0006's 18 statements get no undo verdict; the fix for the blocker is *"restructured, not annotated"* — a direction, not a forward-fix someone could write at 03:00. | In a repo with no down migrations, the forward-fix *is* the rollback plan. A review that names blockers but not the recovery leaves the deploy without the half it cannot improvise. | single run |
| B4 | **Zero-findings was never stated as an outcome.** Where the run checked something and found nothing, it produced a NOTE (F6, F13) — but only where it chose to. Nothing distinguishes "checked, clean" from "not checked" for the rest. | Same defect as B1 from the other side: without an explicit negative, the absence of a finding is unreadable. | single run |
| B5 | **Widened into application-code review without saying it had.** F7 is a TypeScript contract defect; F11 ends in a recommendation to add a `try/catch` in `build.service.ts`; F14 traces Python in `apps/engine`. All useful, none flagged as outside the migration. | Not a defect in the findings — they are good findings — but a reviewer whose remit is unmarked cannot be held to one, and scope that is never declared cannot be reviewed. | single run |
| B6 | **Containment was never tested, because the prompt did the containing.** The run was *told* "do not modify any file", and it complied. So the observation is only that a compliant run complies. | The one thing this baseline cannot tell us is what an uninstructed run would edit. Per `agent-shape` §6, that is precisely why it must be a hook rather than a sentence. | not observed |

## 3 · What it got right — the leave-alone list

**This is the important half of this document.** SkillsBench measured roughly 15% of
tasks getting *worse* with a skill added, concentrated exactly where the base model
was already competent. Everything in this list is that zone. A procedure that
re-teaches any of it can only add noise.

The unaided run, with no guidance at all:

- **Read the whole sequence, not the three files named** — and explained why: 0006's
  redundant index is only redundant because of 0008; 0012's type is only odd against
  0005's.
- **Found the hardest finding in the set unprompted** (F1): the partial unique index
  will meet duplicate rows that the migration's own comment implies exist, the deploy
  fails, and Prisma's failed-migration state then wedges seven later migrations. It
  wrote the pre-flight SQL.
- **Got the lock analysis right** — plain `CREATE INDEX` blocks writes, the whole
  file is one transaction so the locks accumulate, `CONCURRENTLY` cannot be used
  inside it, and no `lock_timeout` means one open transaction stalls everything.
- **Traced call sites rather than reasoning from DDL** — found all four `isCurrent`
  writers, grepped for `P2002`, followed `kind: "intake"` out to `packages/shared`.
- **Checked schema parity in both directions**, including the case where Prisma
  *cannot* express the constraint (F3) and will later drop it.
- **Downgraded its own findings on evidence** (F11 traced into the Python engine
  before being rated a non-issue; F4 downgraded after reading the writers).
- **Was honest about uncertainty**, naming two things it could not settle and
  stating that nothing was executed against a database.
- **Split the verdict per migration** rather than averaging the set.

## 4 · Teach / wall / out of scope

Only `teach` rows became procedure content; only `wall` rows became mechanisms.

| Row | Verdict | Where it went |
|---|---|---|
| B1 prose, not per-statement rows | **teach** | `migration-lock-risk` §3 (one row per statement, no cell empty), §1 (enumerate every statement first) |
| B2 version asserted after being called unknown | **teach** | `migration-lock-risk` §2 (version and wrapper are the two facts everything depends on; "assumed" is an allowed value that must be written), agent body (review against the oldest plausible version) |
| B3 no systematic rollback | **teach** | `migration-reversibility` §1–2 (per-statement verdict, named forward-fix), §4 (the stuck state) |
| B4 no explicit negative | **teach** | `migration-blast-radius` §6 and `migration-lock-risk` §4 (zero findings is written, not omitted) |
| B5 undeclared scope widening | **teach** (weak) | agent body, "Scope" — what is routed and to whom. Weak because the widening produced the best finding in the set; the rule is *declare it*, not *stop*. |
| B6 containment unobserved | **wall** | `hooks/migration-reviewer-scope.md` — writes confined to the review root, `apps/api/prisma/**` denied, `Bash` and `Agent` absent |
| The whole leave-alone list | **leave alone** | Intended to be untaught. ~~No procedure step re-states any of it.~~ **False, and shown to be false by the test dispatch:** five of `migration-blast-radius`'s six steps restate it line-for-line (its §2 pre-flight SELECT is F1; its §3 nullability paragraph is F12 generalised). See `EVALS-migration-reviewer.md` R1. |

## 5 · What this baseline does not license

Written here rather than smuggled into a skill as though it were observed:

- **`migration-blast-radius` is the weakest-supported of the three skills.** The
  baseline performed most of its content unaided — constraints against existing
  data, schema parity, call-site tracing. Its only baseline-backed additions are the
  explicit negative (B4) and the claim/verdict separation. **It is the most likely
  of the three to be a regression**, and the eval suite must be able to detect that.
- **No comparison was run.** Nobody has measured the agent against this baseline on
  the same task. Until that exists, the correct summary is *"built from one
  observation"*, not *"better than unaided"*.
- The `references/statement-shapes.md` table lists shapes the baseline never
  encountered (`ALTER COLUMN TYPE`, `SET NOT NULL`, `NOT VALID` constraints,
  `RENAME`). Those rows are **not** baseline-backed; they are there so an unfamiliar
  statement gets looked up rather than assimilated, and they are honest about
  carrying no numbers.
