# Run notes — how this was built, and where it departs from the procedure

Everything in `docs/round2-arm-a/` is a **staged mirror**. Nothing here is
installed: the agent is not in `.claude/agents/`, the skills are not in
`.claude/skills/`, and the hook is a proposal, not an executable. Installation
paths are given at the end.

## The procedure, as run

| Skill | What it produced |
|---|---|
| `agent-shape` | `SPEC-migration-reviewer.md` — reuse gate, job sentence, context diet, split test, three functions, tool surface, the wall, composition |
| `agent-baseline` | `BASELINE-migration-reviewer.md` — one unaided run against three real migrations, its failure table, and the leave-alone list |
| `agent-assembly` | the agent file, three skills, one reference file, the hook proposal, and a delegated test |

## Placement table (`agent-assembly` §1) — every spec item, one tier

| Tier | What went there |
|---|---|
| 0 · agent body | identity; the boundary and its mechanism; what must not be read as a conclusion; the map of three functions; where knowledge is queried; scope and routing |
| 1 · `skills:` | the three procedures — `migration-blast-radius`, `migration-lock-risk`, `migration-reversibility`. Exactly the cap; a fourth would be the signal to split the agent |
| 2 · `CLAUDE.md` | nothing added. Migration conventions already bind at `apps/api/CLAUDE.md` ("Migrations") and are *queried*, not copied. `.claude/rules/` was not used: measured here not to reach a subagent |
| 3 · `references/` | `migration-lock-risk/references/statement-shapes.md` — opened at step 3 only |
| 4 · `assets/` | none. The output is one review document whose shape the three skills' artefact lines already fix; a template would add a tier for nothing |
| 5 · hook | `hooks/migration-reviewer-scope.md` — the write gate, proposed for a human to install |

## Deviations from the procedure, and what each costs

The run was capped at **two subagent dispatches** and roughly twenty minutes. The
procedures ask for at least four. The budget went to the two that cannot be done
in-context at all — you cannot observe your own baseline, and an author cannot
grade its own work.

| Asked for | Done | What is lost |
|---|---|---|
| `agent-baseline` §2: **≥ 2** independent unaided runs | **1** | Every failure row is a **draw** — one observation, not reproduced. A systematic failure and a bad draw are indistinguishable in this data, and the skills are built on it. This is the most significant gap in the run. |
| `agent-assembly` §5: a **separate** dispatch for mechanical verification | folded into the tester's dispatch | The tester both verifies mechanically and evaluates. Still independent of the author, but one perspective rather than two. |
| `agent-assembly` §3: independent parallel authoring of the three skills | authored together, in one context | The three share vocabulary (statement, finding, verdict), which is the case the procedure allows for joint authoring — but it was not a free choice here, and the fan-out diversity was not bought. |
| `agent-shape` §0: reuse gate against the 84-talent library | **could not run** | `/home/user/skills-repo/` does not exist in this session. `.claude/agents/` and `.claude/skills/` were searched and are clear; the library was not. If a talent there already owns migration review, this run would not have found it. |
| A measured **baseline-vs-agent comparison** on the same task | **not run** | Nobody has shown this agent beats an unaided run. Given how strong the baseline was, that is the open question, not a formality. |

Also not done, deliberately: no ADR was added, no `CHANGELOG.md` entry, no
`ROADMAP`/`BACKLOG` update, and nothing outside `docs/round2-arm-a/` was touched —
the run's instructions confined every file to this directory, which overrides the
repo's usual checkpoint protocol for this commit.

## The honest summary

The unaided baseline was **good** — it found the hardest defect in the set without
help, traced call sites into two languages, and was candid about what it could not
settle. The failure rows that survived are mostly about the **shape and
auditability** of the output rather than about missing findings: per-statement
coverage, an explicit negative, a rollback plan, and not spending a version caveat
one paragraph after raising it.

That is a real but narrow value proposition, and it is exactly the profile
`agent-baseline` warns about: roughly 15% of tasks measurably get *worse* with a
skill added, concentrated where the model was already competent. `migration-blast-radius`
is the skill most exposed to that, and it is named as such in the baseline document
so the test can go looking for it rather than around it.

**Do not install this agent on the strength of these documents.** The bar is in
`EVALS-migration-reviewer.md`, written by a subagent that did not author any of
this, and an agent below its bar is cut, not defended.

## If it passes: installation

A human does this — `tools:`, `hooks:` and `model:` are privilege lines, and an
agent that can write them can attach or remove a wall.

1. `docs/round2-arm-a/agents/migration-reviewer.md` → `.claude/agents/migration-reviewer.md`
2. `docs/round2-arm-a/skills/*` → `.claude/skills/*` (keep the `references/` subdirectory)
3. The script in `docs/round2-arm-a/hooks/migration-reviewer-scope.md` →
   `.claude/hooks/migration-reviewer-scope.sh`, `chmod +x`, then **re-run its control
   table in place**. A gate that was never exercised where it will run is an assumption.
4. Create `docs/reviews/migrations/` — it is the only path the agent may write to,
   and the gate denies a write whose parent does not exist as surely as one that is
   out of bounds.
