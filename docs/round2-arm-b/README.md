# migration-reviewer — the package

A subagent that reviews database migrations before they ship: lock and availability risk,
destructive and irreversible operations, backfill safety, rollback route, and whether the
currently deployed code survives the deploy window.

Everything here is **staged, not installed**. The run that produced it was constrained to
write only under `docs/round2-arm-b/`, so the paths below mirror where the files would
really go rather than being them.

| Staged here | Would live at | What it is |
|---|---|---|
| `agents/migration-reviewer.md` | `.claude/agents/migration-reviewer.md` | The agent: five passes, a severity rubric, a fixed report format, an explicit tool list without `Bash`. |
| `skills/postgres-migration-hazards/SKILL.md` | `.claude/skills/postgres-migration-hazards/SKILL.md` | Will it apply, what does it lock, what does it lose — a failure table with the safe rewrite per statement, plus this repo's Prisma/engine specifics. |
| `skills/migration-rollout-plan/SKILL.md` | `.claude/skills/migration-rollout-plan/SKILL.md` | Expand/contract sequencing, batched and resumable backfills, and the three recovery routes where no down migration exists. |
| `hooks/migration-review-write-gate.sh` + `hooks/README.md` | `.claude/hooks/` + `settings.json` | Proposed PreToolUse gate narrowing `Write` to `docs/reviews/`. Not installed; reconcile with the shared docs-only gate first. |
| `evals/migration-reviewer-evals.md` | `.claude/evals/` or `docs/` | Ten cases, including the negative control (E2) and the containment case (E4). Graded by a subagent that did not author the agent. |
| `evals/fixtures/*.sql` | alongside the evals | The hazardous migration and the deliberately-safe one, both written against the real Scio schema. |
| `baseline.md` | `docs/` | What an unaided review actually got right and wrong. The only legitimate source of content for the procedures. |
| `decisions/0022-the-migration-reviewer-agent.md` | `docs/decisions/0022-…` | The ADR. Proposed. |

## How it was built

Against the rules in `CLAUDE.md` for building agents in this repo:

- **`tools:` is explicit**, and `Bash` is deliberately absent — that absence is what makes
  "cannot apply a migration" true rather than merely promised.
- **Two preloaded skills**, under the three-module cap. A third function would be the signal
  that this is two agents.
- **The "must never" is a hook and an absent tool.** The prose in "Out of remit" is there for
  the model, not as the enforcement.
- **No persona.** The agent file is procedures, failure tables and a rubric.
- **Nothing was graded by its author.** One subagent produced the unaided baseline; a
  different one, which did not write any of this, tested the finished package.
- **Every procedure traces to an observed failure**, recorded in `baseline.md`. What the
  unaided model already did well is deliberately not "taught" — that is where a skill
  regresses quality.

## To install

1. Read `hooks/README.md` and reconcile the gate with the existing shared docs-only write
   gate (commit `e60a5fd`) rather than adding a near-duplicate.
2. Move the files to the paths in the table above.
3. Run the eval suite from a fresh subagent. **E2 (negative control) and E4 (containment)
   must pass** — the rest may take one failure.
4. Move ADR-0022 to `docs/decisions/` and take it to Accepted only after step 3.
