# Measuring whether an agent works

Conformance and containment are solved here: six control suites, 31 validator
controls, all green. Neither of them says an agent **does its job better than not
having it**, and that is the only question a release should actually turn on.

This document is the protocol for answering it, and the discipline for collecting
the data along the way.

---

## 1 · Variables and constants, and why the split is the whole design

`python3 .claude/validate/agents.py --factors` emits one JSON object per agent,
with every field prefixed:

- **`v_`** — a **variable**. We chose it and could have chosen otherwise, so it is
  a candidate cause when outcomes differ.
- **`c_`** — a **constant**. Fixed by the platform or the specification. Recorded
  as *context*, never treated as a factor.

**A constant is recorded so an old run stays interpretable.** When Anthropic
changes the description cap or the spawn depth, every run taken before the change
still has its conditions attached. A run whose environment was never written down
cannot be compared with anything later.

**A constant is never an explanation.** `c_spawn_depth: "1"` explains why no agent
can dispatch — it does not explain why one agent outperformed another, because it
was the same for both.

### The trap the split exposes immediately

Today's factor table:

| Agent | model | tools | preloads | body | built against |
|---|---|---|---|---|---|
| `agent-builder` | inherit | 9 | 3 | 1229 | pre-template |
| `agent-fitness-review` | inherit | 5 | 2 | 879 | pre-template |
| `architect` | inherit | 9 | 3 | 1138 | pre-template |
| `architect-rebuild` | inherit | 4 | 3 | 736 | pre-template |
| `domain-researcher` | inherit | 7 | 3 | 1084 | pre-template |
| `primary-source-verifier` | inherit | 5 | 2 | 1173 | pre-template |
| `rebuild-adjudicator` | inherit | 7 | 3 | 809 | pre-template |
| `rebuild-prospector` | inherit | 4 | 2 | 696 | pre-template |

**`v_model` is a variable with no variance.** Eight agents, one value. It cannot
explain any difference in outcome, and no amount of data will change that —
learning anything about model choice requires *deliberately varying it*, not
collecting more rows where it is `inherit`.

**`v_template_built_against` is the same.** All eight `pre-template`. The template
exists and nothing has been built to it, so its effect is unmeasurable until at
least one agent is.

That is what the split is for: it separates *we do not know yet* from *we cannot
know from this data*, and those need different responses. The first needs more
runs. The second needs a different experiment.

**One field earned its correction on the first run.** `v_template_version` read the
tree's current VERSION file — so every agent reported `1.0.0` while the registry
said `pre-template`. A field named for one thing carrying another would have had
any later analysis comparing a constant against itself. It is now
`v_template_built_against`, read from the registry where the decision lives, and
`c_template_version_in_tree` for the snapshot.

---

## 2 · The competence test

The design is an A/B, and the failure mode is well documented **here** rather than
in the literature: this project has run exactly one, and it returned **null**.

Its confounds, recorded at the time:

- **one task**
- **one run per arm**
- both arms carried the same `CLAUDE.md`, so the test asked whether the skills add
  anything over rules already in context
- the skilled arm was capped below the dispatches its own procedure requires

Every one of those is a design flaw, not a result. So:

### The protocol

**Before anything runs:**

1. **Write the criteria down, and commit them.** What counts as the agent having
   done the job — per criterion, checkable by someone who was not there. Criteria
   written after the run describe the run.
2. **Name the arms.** *With* the agent, and *without* it — the same task given to
   a general-purpose agent holding the same tools. If the arms differ in anything
   but the agent, that difference is the experiment and the agent is not.
3. **Fix n before you look.** Not one run per arm. **B147** observed the same
   negative control disagreeing with itself across two runs, twice, in unrelated
   agent pairs — so a single draw tells you about the draw. Three per arm is a
   floor, not a target.
4. **Pick the tasks from the agent's own trigger**, not from what it is good at.
   Two or three, and at least one that should be **out of its scope** — an agent
   that helps everywhere is not specialised, it is just present.

**Then:**

5. Run both arms. Neither arm's runner may be the evaluator.
6. **The evaluator neither built the agent nor ran the arms**, is given the
   criteria and the outputs with the arms **unlabelled**, and rules per criterion.
7. It must have caught its own class in `.claude/validate/calibration/` first.

**Then record it**, per §3, whatever the answer was. A null result recorded is
data; a null result quietly not written down is how a system convinces itself.

### What counts as a pass

The bar is stated in the agent's spec **before** the run. Absent that, the honest
outcome is `cannot-say`, and `cannot-say` is a finished answer.

**A null result is not a reason to keep the agent.** It is the finding that the
agent, as built, is not doing what it was built for — and the responses are: fix
the agent, fix the test, or cut it. Defending a null is how the sunk cost gets
paid twice.

---

## 3 · The run record

One JSON object per run, appended to `docs/measurements/runs.jsonl`. Never edited,
only appended — a corrected run is a **new record** citing the one it supersedes.

```json
{
  "run_id": "2026-08-29-migration-review-01",
  "date": "2026-08-29",
  "agent": "migration-review",
  "kind": "competence",
  "commit": "f0b5ca7",
  "task": "docs/measurements/tasks/migration-review-01.md",
  "criteria_committed_at": "e5e7d9a",
  "arms": {"with": 3, "without": 3},
  "evaluator": "general-purpose, blind to arm labels",
  "evaluator_calibrated_on": "cal-l1-grounding",
  "evaluator_caught_planted_defect": true,
  "results": [
    {"criterion": "every statement carries a ruling", "with": 3, "without": 1},
    {"criterion": "abstains where the dialect is undeclared", "with": 3, "without": 0}
  ],
  "verdict": "fit",
  "notes": "without-arm ruled confidently on statements whose engine was unstated"
}
```

`kind` is one of **`conformance`** (the validator), **`containment`** (control
rows), or **`competence`** (this protocol). Keeping them in one file with one field
separating them is deliberate: the temptation is to report a green containment
suite as evidence the agent works, and a shared schema makes that substitution
visible.

**Join key:** `agent` + `commit`. Configuration comes from `--factors` at that
commit; outcomes come from here. Neither file duplicates the other.

`criteria_committed_at` is the commit the criteria were written in. If it is not an
ancestor of `commit`, the criteria were written after the run and the record says
so on its face.

---

## 4 · What this cannot tell us yet, stated so nobody claims otherwise

**n is tiny.** Eight agents, a handful of runs, two variables with zero variance.
**No statistic computed on this will be significant, and none should be reported
as though it were.** The schema is the investment; the analysis is later.

**Nothing here measures the harness.** Every run happens under
`c_spawn_depth: "1"` with hooks absent in non-interactive sessions. Conclusions
drawn here transfer to a differently configured environment only as hypotheses.

**The evaluator is a model.** Model-versus-expert agreement on quality is measured
at **22–40%** where expert-expert is 60%, and the disagreement runs in opposite
directions rather than being merely noisy. That is why the criteria must be
checkable rather than judged, why the arms are unlabelled, and why the calibration
row exists. It does not make the evaluator reliable — it makes its unreliability
bounded and recorded.

**And the first thing to vary is not the model.** It is the template: one agent
built to the standard, measured against the same agent's `pre-template`
predecessor, is the only comparison currently available where the variable
actually varies.
