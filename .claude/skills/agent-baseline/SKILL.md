---
name: agent-baseline
description: "Use AFTER a spec exists and BEFORE writing an agent's skills — dispatches independent subagents to attempt the target job with no support at all, and records exactly what they get wrong. That observed failure list is the only legitimate content for the agent's procedures; anything not on it is speculation. Run this even when the failures seem obvious, because roughly 15% of tasks measurably get WORSE with a skill added, concentrated exactly where the model was already competent — and without a baseline you cannot tell which way yours pushed. NOT for designing what agents should exist (use agent-shape), NOT for writing the files (use agent-assembly), NOT for testing a finished agent (that is a separate dispatch at the end of assembly)."
---

# Watch it fail first

You cannot observe your own baseline. This procedure delegates the failure.

The reason is not ceremony. SkillsBench measured skills lifting task success from
33.9% to 50.5% overall — **and roughly 15% of tasks regressing**, concentrated
where the base model was already competent. Adding a procedure is not free and not reliably positive.

An earlier version of this line added *"software engineering was its weakest domain at
+4.5%"*. **That is v1 of the paper and three revisions have overtaken it** — an audit
fetched v4 Table 3 and read software engineering at **+11.6 pp**, with the weakest
domain **Mathematics & OR at +9.7 pp**. Stale, not invented: v1 does say +4.5. The
figure is removed rather than replaced, because it rests on one agent's single fetch
and has not been through `primary-source-verifier`; the two numbers above are the
load-bearing ones and they survived the same audit's disconfirming check. The
baseline is how you find out which way yours pushed.

Three of four architecture skills measured elsewhere in this project **did not
discriminate at all**, and one made the answer worse. That is the base rate you
are working against.

## 1 · Write the task the agent will actually face

Realistic, from this repo, with a real artefact expected. Not a toy. If the agent
will review migrations, hand over a real migration. The failure modes you are
hunting only appear under real conditions.

**Artefact:** the task prompt, verbatim, saved with the spec.

## 2 · Dispatch at least two independent runs, with nothing

Two, not one — a single run cannot separate a systematic failure from a bad draw.
Independent and parallel; **they must not see each other's work.** The measured
gap between instances is where the information is, and agents that converse
collapse toward one answer (0 of 62 comparisons significant across 12
interventions).

Give them the task, the repo, and no guidance. Ask for the artefact and a short
rationale — the rationale is where the reasoning that produced the mistake shows.

**Artefact:** N transcripts and N outputs.

### 2b · When you cannot dispatch at all

You may hold no `Agent` tool. This is not hypothetical and it is not rare: with
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` — the setting in the only environment this
loop has run in — nesting is off and **every agent is a leaf**. Four separate agents
reported it independently before anyone wrote it down here, and both real builds of
this loop hit it. `agent-assembly` has carried a clause for the same problem all
along; this step did not, so both builds improvised a substitute without the
procedure telling them they were permitted to.

Take these in order, and say in the artefact which one you used:

1. **Ask the session above you to dispatch.** It is not a leaf. Emit the exact task
   prompt you would have sent, verbatim, so the runs are the ones this step
   specifies and not an approximation of them.
2. **Use recorded real runs** — output produced by unaided attempts at this job that
   *already exists*, written by someone other than you, before this agent was
   proposed. This is **stronger** than a dispatched baseline on one axis: nobody
   constructed it to be a baseline, so it cannot have been shaped to the answer. It
   is weaker on another: you did not control the task. Cite every row at a
   `file:line` or a query.
3. **Neither.** Then you have no baseline, and the consequence is stated plainly and
   not worked around: **the agent's content is opinion.** It goes to the spec's open
   questions, the agent is not shipped as done, and the missing baseline is named in
   the spec as owed.

What you may **not** do is write a failure table from what you expect agents to get
wrong. That is the speculation this whole step exists to replace, and it is
indistinguishable from a real table once written down.

**Artefact:** which route, and — for route 1 — the verbatim prompt you handed up.

## 3 · Record what they got wrong — quoted, not summarised

Go through each output against the spec. For every failure write:

- **what they did**, quoted or at `file:line`
- **what the consequence is** — concretely, not "could cause issues"
- **whether both runs did it** — a failure both made is systematic; one is a draw

Watch particularly for the failures that look like competence:
- something granted by omission rather than by decision
- a boundary written as a sentence
- a step that ends in a consideration rather than an artefact
- a claim asserted rather than checked
- work that was never tested, or tested by whoever produced it

**Artefact:** the failure table. This is the deliverable.

## 4 · Separate what the agent must fix from what it need not

Not every failure is the agent's job. Sort each row:

| Verdict | Meaning |
|---|---|
| **teach** | the agent's procedure must prevent this |
| **wall** | prose will not hold it; it needs a hook or a tool that is absent |
| **out of scope** | real, but a different agent's job — record and route |
| **draw** | one run only, not reproduced; keep it, do not build on it |

**Only `teach` rows become procedure content. Only `wall` rows become mechanisms.**

## 5 · Say what the baseline did *well*

The honest half, and the one that gets skipped. Anything the runs got right
without help is somewhere your procedure can only add noise — that is exactly the
regression zone. Write it down and leave it alone.

**Artefact:** the leave-alone list.

## Handing over

`agent-assembly` builds only from the `teach` and `wall` rows. If a rule you want
to write has no row behind it, it is your opinion, and it goes in the spec's open
questions rather than in the agent.

## When this does not apply

- **The agent already exists and you are testing it, not building it.** A baseline
  answers "what goes wrong without this"; a finished agent needs an eval suite from
  a fresh tester instead.
- **The job has no artefact to judge.** If two runs cannot be scored against
  anything, you will collect opinions rather than failures, and opinions become
  procedure content that nothing can later refute.
- **The spec is not settled.** Baselining a job whose shape is still moving
  measures the wrong thing twice; go back to `agent-shape`.
- **The failures are already recorded from a real run.** A live run that went wrong
  is a better baseline than a synthetic one, because nobody constructed it. Use it
  and say where it came from.

Declining here is not a shortcut. A baseline you could not run is a spec whose
procedure content has to stay in the open-questions list until someone can.

