# Spec — a migration reviewer

Produced by `agent-shape`. Hands over to `agent-baseline`, not to assembly.
Every section below is an artefact that procedure required.

**Run conditions (stated once, they qualify everything here):** this run was capped
at **two subagent dispatches total** and roughly twenty minutes. `agent-baseline`
asks for at least two independent unaided runs and `agent-assembly` asks for a
mechanical verifier *and* a separate tester — four dispatches minimum. The budget
was spent on the two that the evidence says cannot be done in-context at all: one
baseline observation, and one fresh tester who also ran the mechanical checks.
Deviations are listed in `RUN-NOTES.md`.

---

## 0 · Nothing already owns this

| Searched | Found | Bearing on this job |
|---|---|---|
| `.claude/agents/` (2 files) | `agent-builder`, `architect` | `architect` reviews *designs, diffs and layers against what they claim to be* and emits ADRs and review findings. It has no procedure for lock behaviour, backfill or rollback, and its one occurrence of the word "migration" (`architect.md:98`) is about the cost of a future migration, not about reviewing one. |
| `.claude/skills/` (6 skills) | `architecture-review`, `architecture-decision`, `system-decomposition`, `agent-*` | `architecture-review` is a general design-review procedure. Nothing in it reaches SQL, locks, or data. |
| `grep -ril migration .claude/ docs/` | 15 files (excluding this run's own directory; re-counted by the test dispatch — the original figure of 14 did not reproduce) | All either the agent-building skills using migration review as their *example*, or docs reporting the gap: `docs/REVIEW-PRODUCTION-READINESS.md:272` — *"No down migrations, no plan for a failed deploy."* |
| `/home/user/skills-repo/.claude/skills/` — the 84-talent library the reuse gate is supposed to run against | **absent in this session** (`ls: No such file or directory`) | The reuse check against the library **could not be run**. This is a gap in the evidence, not a clear result. |

**Verdict: author** — with the caveat above recorded rather than buried. The
knowledge base at `/home/user/skills-repo/knowledge/notes/` is likewise absent,
so no claim in these files cites it; where a measured claim appears it comes from
the three skills in this repo, quoted as they state it.

## 1 · The job, in one sentence and one artefact

> It reviews a pending migration set against the schema, the data and the code
> that will be running while it applies, and produces a findings list at
> `file:line` with a per-finding severity and one verdict: **ship**,
> **ship with changes**, or **do not ship**.

**Emits:** `docs/reviews/migrations/<migration-name>.md` — the findings table, the
per-statement lock table, the reversibility verdict, and what it did not check.

## 2 · Context diet

This agent **judges**; it does not propose. `agent-shape` step 2: generators are
starved, evaluators are saturated. So the diet is deliberately wide on the artefact
and narrow on other people's conclusions.

**Must see**
- the migration SQL under review, and every migration already in
  `apps/api/prisma/migrations/` — order and prior state decide what a statement means
- `apps/api/prisma/schema.prisma` — a migration without the matching schema change is
  a defect the SQL alone cannot show (`apps/api/CLAUDE.md`: *"Adding a column means a
  migration **and** a schema change — never one without the other"*)
- the code that reads and writes the affected tables — old code runs during the deploy
- how migrations are applied here: `prisma migrate deploy`, forward only, no down
  migrations (`apps/api/package.json:12`, `scripts/dev-up.sh:136`)
- ADR-0007 — PostgreSQL on Azure Flexible Server; lock and rewrite behaviour is
  version-dependent and read live, never recalled

**Must not see**
- **any prior verdict on the same migration** — the author's PR description, a
  previous review's conclusion, a "this is safe because" note. `agent-shape` step 2
  and `design-fixation-and-anchoring` both bear on this: a solution in the prompt
  produces source-bound restatements. The migration's own SQL comments are part of
  the artefact and are read as claims to check, not as findings.
- **any live database credential.** `DATABASE_URL`, connection strings, anything in
  `.env`. It reviews text; it never connects.

  **Correction, from the test dispatch:** an earlier version of this line claimed
  this was *"enforced by the absence of `Bash`"*. That is false and it is the exact
  antipattern this repo names — a must-never written as a sentence with a mechanism
  attached that does not do the work. Absent `Bash` stops the agent *connecting*; it
  does nothing about `Read`. `.claude/settings.json` denies `Read(./.env)` and
  `Read(./apps/engine/.env)` and **not** `apps/api/.env`, which is where
  `scripts/dev-up.sh:38` shows a real `DATABASE_URL` lives. Until
  `Read(./apps/api/.env)` and `Read(./apps/*/.env)` are added to that deny list,
  **this one is unenforced**, and it is listed as unenforced rather than dressed up.

## 3 · Split test — one agent

Applied in order; the first rule that fires decides.

| Rule | Fires? | Why |
|---|---|---|
| 1 · Opposite diets → separate | no | All three functions are evaluation. All saturated. |
| 2 · Independent quarry → separate | no | Different quarry, but the same artefact and the same diet; the differentiation is bought by three differentiated **procedures** inside one agent, which is what the ~35% figure in `requirements-discovery` is about. The thing that measured no better than nothing was the *undifferentiated* checklist. |
| 3 · More than three functions → split | no | Exactly three. A fourth would be the signal to split. |
| 4 · Author ≠ tester | **fires, outside the roster** | The reviewer never writes the fix and never writes its own evals. Both are separate dispatches, not a second rostered agent. |

**Roster: one agent, three skills.** Decided by rule 3 holding and rule 1 not firing.

## 4 · The three functions

Each is a procedure with its own quarry and its own failure table, and each ends
in something checkable.

| Function | Decides | Emits |
|---|---|---|
| `migration-blast-radius` | what this change breaks for the data and the code that already exist — constraints against existing rows, schema/SQL divergence, type narrowing, enum and column removal, old code running against new schema | findings rows at `file:line`, each with the concrete consequence |
| `migration-lock-risk` | what applying it does to a live database — the lock each statement takes, what that lock blocks, whether the table is rewritten, and whether the statement can run inside Prisma's transaction at all | a per-statement lock table: statement → lock mode → what it blocks → rewrite? → duration class |
| `migration-reversibility` | what gets us back — whether the change is reversible at all, whether the backfill is idempotent and batched, and what the forward-fix is given that there are no down migrations here | a reversibility verdict per statement, plus the forward-fix that must exist before it ships |

## 5 · Tool surface

| Tool | The job that needs it |
|---|---|
| `Read` | the migration, the schema, the calling code |
| `Grep` | find every read/write of an affected table; find the schema line for a changed column |
| `Glob` | enumerate the migration directory in order |
| `Write`, `Edit` | emit the review document — into the review root only, per §6 |
| `TodoWrite` | three procedures over a multi-statement set; the order is part of the method |
| `WebFetch`, `WebSearch` | lock and rewrite behaviour is **version-dependent** (a `NOT NULL DEFAULT` add rewrites the table before PostgreSQL 11 and does not after). This repo's standing rule is that a value which moves on its own is read live rather than carried; that rule is why these are here, and the lock table must cite the version it read. |

**Withheld, and what that makes impossible**
- **`Bash`** — it cannot connect to a database, apply or test a migration, or write
  past its gate with `echo >`. *A boundary is only as narrow as the widest tool*;
  granting `Bash` next to a path-scoped write gate would make the gate decorative.
- **`Agent`** — a reviewer that can dispatch can dispatch a worker that holds a
  shell, which is the same hole one hop away.
- **`NotebookEdit`** — no notebooks here; granted by omission is how surfaces grow.

## 6 · The wall

Prose does not hold these. `agent-shape` step 6: warnings failed in three studies
and backfired in a fourth. A `PreToolUse` hook runs before every permission check,
`bypassPermissions` included, and can only tighten.

| Must be impossible | Mechanism |
|---|---|
| Editing the migration it is reviewing | hook: deny writes to `apps/api/prisma/**`. This is the containment case that matters — a reviewer that fixes the thing it reviews is grading its own work. |
| Editing any source file | hook: writes allowed **only** under the review root |
| Editing its own definition, its skills, its hook, or settings | hook: deny `.claude/**` |
| Connecting to a database, or running anything | **absent `Bash`**, absent `Agent` |
| Escaping the review root by traversal or a prefix lookalike | hook: resolve the path, compare against the resolved root with a trailing separator |

Written as a proposal at `docs/round2-arm-a/hooks/migration-reviewer-scope.md`.
A human installs it. The privilege lines (`tools:`, `hooks:`) are designed here and
installed by a human for the same reason.

## 7 · Composition

- **Single agent, invoked on a migration set.** No round-table: 12 interventions,
  45 conditions, 0 of 62 significant.
- **Producer → independent verifier.** Whoever wrote the migration is not this
  agent, and this agent does not write the fix. The handoff both ways is a document.
- **The evals are written by a fresh subagent** that did not see the authoring.
- Depth 2 by construction: it holds no `Agent` tool, so it is a leaf.

## Open questions — not built, because no baseline row supports them

Recorded here rather than smuggled into a procedure as an opinion.

1. Should the reviewer own **CI enforcement** (a check that fails a PR whose
   migration has no review document)? That is a fourth function and therefore a
   second agent; see the three-skill rule.
2. **Zero-downtime deploy shape** (expand/contract over two releases) presumes a
   rolling deploy. Nothing is deployed today (`docs/REVIEW-PRODUCTION-READINESS.md`
   §7.2), so the reviewer states the requirement and does not assume a topology.
3. Whether a **`docs/decisions/` ADR** should record "no down migrations, forward-fix
   only" as a decision rather than an observed fact. Product/architecture call —
   `architect` owns it, not this agent.
