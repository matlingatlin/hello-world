# The agent registry

Who released what, against which standard, on what evidence — and what is still
withheld.

**Why this exists.** B133 asked for it from one side (no owner, no version, no
withdrawal mechanism) and the pharmacopoeia division in
`docs/architecture-agent-factory.md` asked for it from the other: a manufacturer
keeps a **batch record** so anyone can reconstruct what was made and to what
standard, and a **Qualified Person** signs one release decision before anything
leaves. We had verdicts and no release.

**A verdict is an input to a release decision, not the decision.** `fit`,
`unfit` or `cannot-say` is what a reviewer produces. *Put this into use* is a
human's call, and until it is recorded, nobody can say whether an agent in
`.claude/agents/` was ever meant to be there.

---

## Status vocabulary

| Status | Means |
|---|---|
| `in use` | released deliberately, with the evidence named in its row |
| `provisional` | present and usable, but its evidence does not meet the bar. It runs at the caller's risk and the row says why |
| `withheld` | present in the tree and **not** to be used. Nothing enforces this — it is a note to a human |
| `retired` | superseded or cut. The row stays; the file may not |

Nothing here is a mechanism. `withheld` does not stop a call, and no hook can
make it: the roster is assembled from the files. The registry's job is to make
the *decision* visible, not to enforce it. Removing the file is the enforcement.

---

## The register

**Template `1.0.0` is superseded.** The first agent built to it —
`llm-component-architect` — found five defects in the standard by using it, and fixing
them made `1.1.0`. Its row still reads `1.0.0`, which is the truth: that is what it was
built against. **That is the versioning working, not a discrepancy to tidy.** A row
rewritten to the current version would erase the only fact that makes it useful.

**Template version** is the version of
`.claude/skills/agent-assembly/assets/template/` the agent was built against.
`pre-template` means the agent predates the standard entirely — it was written
before there was one, so nothing checked it against a form.

| Agent | Status | Template | Evidence | Released |
|---|---|---|---|---|
| `agent-builder` | `provisional` | `pre-template` | `docs/domain-research-test-results.md` — two real builds observed; its own three-skill ablation returned **null** | not recorded |
| `agent-fitness-review` | `withheld` | `pre-template` | **none.** Step 6 unmet; the one lens run is `docs/agent-review-agent-fitness-review-L5.md` and is not a fitness determination | no |
| `architect` | `provisional` | `pre-template` | repaired against a known defect list; **evals never run** (B125) | not recorded |
| `architect-rebuild` | `provisional` | `pre-template` | `docs/evals-rebuild-pair.md`; tester brief unmet (B129) | not recorded |
| `domain-researcher` | `provisional` | `pre-template` | `docs/research/evidence/c4-x1-run.md` — **C2, C3, X1, X2 pass**, 4 of 25 cases | not recorded |
| `llm-component-architect` | `withheld` | **`1.0.0`** | **none.** Step 6 unmet — `Agent` withheld at runtime, so no fresh tester could be dispatched. Spec at `docs/agent-spec-llm-component-architect.md`, brief at `docs/llm-component-architect-tester-brief.md` | no |
| `primary-source-verifier` | `provisional` | `pre-template` | `docs/research/evidence/c4-x1-run.md` — **C4, N2, X3, X4 pass**, and C4 is the case the whole design turns on | not recorded |
| `rebuild-adjudicator` | `provisional` | `pre-template` | `docs/evals-rebuild-pair-results.md` — 34 behavioural cases, **three fails** | not recorded |
| `rebuild-prospector` | `provisional` | `pre-template` | `docs/evals-rebuild-pair-results.md` — same run; its diet gate passes 34 control rows | not recorded |

**Nine agents, and not one has a recorded release.** That is the honest state
and it is the point of writing the register: every one of them is in the tree
because it was built, not because anyone decided it should be used.

---

## What this register makes visible

**`pre-template` on eight of nine is the refactor worklist.** The standard exists
and exactly one agent has been built to it. Each `pre-template` row is a candidate
for rewriting against `assets/template/`, and the version column will say when one
has been.

**`llm-component-architect` is the first `1.0.0` row**, which makes it the only
place where the template variable actually varies. What that comparison is worth
today is nothing, because its evidence cell is empty — a template version is a
statement about how an agent was built, not about whether it works.

**Two `withheld` rows, both for the same reason.** `agent-fitness-review` and
`llm-component-architect` are withheld because `agent-assembly` step 6 is unmet:
no subagent that did not author them has tested them, so nothing has established
that either can do its job. In both cases the build said so out loud rather than
reporting a green number.

**Nobody has run a competence test.** Every evidence cell above is conformance or
containment — *is it built correctly*, *can it exceed its remit*. Not one says the
agent does its job better than not having it. The only A/B this project has run
returned null, on one task with one run per arm.

---

## Releasing an agent

1. Its evidence meets the bar its spec states, and the bar was stated **before**
   the evidence was gathered.
2. The judge that produced that evidence caught its own class in
   `.claude/validate/calibration/` first.
3. A human decides, and writes the row: status, template version, evidence path,
   date, and who.
4. If it cannot be released, say which of 1–3 failed. `provisional` with a reason
   is an honest row; `in use` with no evidence is not.

## Withdrawing one

Set the row to `withheld` or `retired`, say why, and **delete or move the file** —
because the status column is a note and the file is the mechanism. A row that
says `withheld` beside an agent still in `.claude/agents/` is a decision nobody
carried out.
