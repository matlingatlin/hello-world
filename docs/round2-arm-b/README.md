# migration-reviewer — the package

A subagent that reviews database migrations before they ship: lock and availability risk,
destructive and irreversible operations, backfill safety, rollback route, and whether the
currently deployed code survives the deploy window.

Everything here is **staged, not installed**. The run that produced it was constrained to
write only under `docs/round2-arm-b/`, so the paths below mirror where the files would
really go rather than being them.

| Staged here | Would live at | What it is |
|---|---|---|
| `agents/migration-reviewer.md` | `.claude/agents/migration-reviewer.md` | The agent: seven passes, a severity rubric, a fixed report format, and an explicit tool list with neither `Bash` nor `Write`. |
| `skills/postgres-migration-hazards/SKILL.md` | `.claude/skills/postgres-migration-hazards/SKILL.md` | Will it apply, what does it lock, what does it lose — a failure table with the safe rewrite per statement, plus this repo's Prisma/engine specifics. |
| `skills/migration-rollout-plan/SKILL.md` | `.claude/skills/migration-rollout-plan/SKILL.md` | Expand/contract sequencing, batched and resumable backfills, and the three recovery routes where no down migration exists. |
| `hooks/migration-review-write-gate.sh` + `hooks/README.md` | `.claude/hooks/` + `settings.json` | Proposed PreToolUse gate narrowing `Write` to `docs/reviews/`. Defence in depth only — the agent has no `Write` — and not installed; reconcile with the shared docs-only gate first. |
| `evals/migration-reviewer-evals.md` | `.claude/evals/` or `docs/` | Eleven cases, including the negative control (E2), the containment case (E4) and a direct test of the gate script (E11). Graded by a subagent that did not author the agent. |
| `evals/fixtures/*.sql` | alongside the evals | The hazardous migration and the deliberately-safe one, both written against the real Scio schema. |
| `test-report.md` | `docs/` | What the independent tester found in this package, what was fixed, and what was left. It found the containment claim overstated and a bypass in the gate; both are fixed here. |
| `baseline.md` | `docs/` | What an unaided review actually got right and wrong. The only legitimate source of content for the procedures. |
| `decisions/0022-the-migration-reviewer-agent.md` | `docs/decisions/0022-…` | The ADR. Proposed. |

## How it was built

Against the rules in `CLAUDE.md` for building agents in this repo:

- **`tools:` is explicit**, and `Bash` is deliberately absent — that absence is what makes
  "cannot apply a migration" true rather than merely promised.
- **Two preloaded skills**, under the three-module cap. A third function would be the signal
  that this is two agents.
- **The "must never" is an absent tool.** Neither `Bash` nor `Write` is on the list, so
  "cannot apply, cannot edit" is a property of the configuration rather than a promise. The
  first draft granted `Write` and relied on an uninstalled hook; the tester caught it, and
  removing the capability beat guarding it.
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
3. `mkdir -p docs/reviews` (with a `.gitkeep`) — the reports have to land somewhere. This
   run could not create it: it was confined to `docs/round2-arm-b/`.
4. Run the eval suite from a fresh subagent. **E2 (negative control) and E4 (containment)
   must pass** — the rest may take one failure. E4 is scored against the tool list, so
   re-run it after any change to `tools:`.
5. Move ADR-0022 to `docs/decisions/` and take it to Accepted only after step 3.
