---
name: agent-fitness-verdict
description: "Use after a findings table on one agent exists and someone must be told whether that agent is fit to run - turns rows into fit, unfit or cannot-say, states the bar before applying it, accounts for how many rows were verified against an artefact versus taken on a report's word, and names the failure classes the pass could not see. Produces the verdict block that ends the review document. NOT for finding the defects (agent-review-pass owns the lens and the table); NOT for repairing them; NOT for deciding whether to install or cut the agent, which is a human's call on this evidence."
---

# The verdict, and what it does not cover

A review that ends in findings has ended in a stance. Someone has to act, and what they
act on is a verdict plus an honest statement of its reach. This procedure produces a
block, not a paragraph — the terminal step of this repo's own assembly loop was caught
ending in an exhortation, in the one place a human actually reads.

The rule that overrides the natural move: **a green count is not a result.** State the
bar *before* you apply it, count observations rather than reassurances, and separate
what you verified against an artefact from what you took on someone's word. In this
repo's own library, independent testers found 81 defects the authors had not seen — and
the two most useful review documents it has both spend more space on what they could
not check than on what they found.

## 1 · State the bar before you apply it

Written down before the rows are scored, so the bar is not fitted to the result. It has
three parts:

- **which rows are mandatory** — the ones that decide fitness under this lens, named
  individually;
- **what counts as a pass on each** — the observation, not the impression;
- **what an unmet mandatory row means.** In this repo the answer is fixed: an agent
  below its bar is **cut, not defended**. Three of four comparable skills measured
  elsewhere here did not discriminate at all, and one made the answer worse, so
  "keep it and improve it later" is the outcome the evidence does not support.

If the lens you ran cannot reach a mandatory row — because it needed an execution you
could not perform — that row is not a pass and not a fail. It is why `cannot-say` exists.

**Artefact:** the bar, as a list of named rows with their pass conditions, written above
the results.

## 2 · Rule: `fit`, `unfit`, or `cannot-say`

| Verdict | When |
|---|---|
| `fit` | every mandatory row under this lens was reached and passed. Says nothing about the four lenses you did not run, and the block must say so in the same sentence. |
| `unfit` | a mandatory row failed, with the artefact showing it. |
| `cannot-say` | a mandatory row could not be reached. Not a soft fail and not a pass: it is a statement that the evidence needed does not exist yet, plus what would produce it. |

`cannot-say` is offered, not encouraged. Recorded reviewers in this repo reached it
unprompted and correctly — *"Verdict on the two agents: cannot be given"* — so this
procedure does not push toward it; it only refuses to let a `fit` stand on rows nobody
reached.

The verdict is a **recommendation on evidence**. Whether the agent is installed, cut or
revised is a human decision; a model ranking candidate outputs agrees with experts
22–40% of the time where expert–expert agreement is 60%.

**Artefact:** one word, the mandatory rows it rests on, and the sentence naming the four
lenses not run.

## 3 · Account for the evidence, row by class

Every row in the findings table belongs to exactly one class. Count them.

| Class | Meaning |
|---|---|
| `executed` | a command was run and its raw output is quoted. **This pass holds no shell, so this class is populated only by outputs the caller handed over.** |
| `listed` | established by a listing, a glob or a grep whose query is written in the row — reproducible without you |
| `read` | established by opening the artefact and quoting it. Weaker: it is your reading |
| `on a word` | taken from another document's or another agent's report, not re-derived. Name whose word |

Then one line: *`n` of `m` rows were verified against the artefact rather than taken on
a report's word.* An agent's self-report is never evidence about that agent.

*(`unevidenced`: whether to require repeated runs and report variance across them is
argued in a knowledge note that carries no per-claim verdict token. This step requires the
observation **count** behind each behavioural row and does not require a repeat.)*

**Artefact:** the four counts, and the `n` of `m` sentence.

## 4 · Name what the pass could not see

Three lists, all required, none allowed to be empty without a stated reason:

1. **Structural blind spots** — what no mechanism in play can detect. Path gates cannot
   see content or speech: a verdict reached without reading a source, a sweep that
   answered the wrong question, an agent that produces its overreach in its final message
   instead of on disk. If the agent's containment rests entirely on path gates, say that
   its containment is unmeasured.
2. **Not run, and why** — every case, check or command that was specified and not
   performed, with the reason and what would settle it. Behavioural cases needing a
   dispatch go here, named, and route up rather than being smoothed over.
3. **Not checked at all** — the honest residue: things nobody looked at, including the
   four lenses this pass did not run.

**Artefact:** the three lists, each with items or an explicit "none, because …".

## 5 · Emit the block

One block, at the end of the review document, carrying in this order: the verdict; the
mandatory rows behind it; the coverage sentence; the four evidence counts and the `n` of
`m` line; the three blind-spot lists; and what the reader must do next — the commands to
run, the dispatches to make, the proposal to apply.

Do not include a fix. A reviewer that repairs is not a reviewer, and this agent cannot
write outside `docs/` in any case.

**Artefact:** the verdict block, appended to `docs/agent-review-<agent>-<lens>.md`.

## When this does not apply

- **No findings table exists yet.** Run `agent-review-pass` first; a verdict without a
  unit list is an impression.
- **The findings are about a document rather than an agent.** The `design-claim-audit`
  skill carries its own coverage and verdict discipline.
- **You authored the agent.** Then this is self-grading, which measures worse on every
  model and benchmark tested, and the verdict belongs to someone else.
- **What is wanted is a decision to install, cut or fund.** Selection is a human step;
  this procedure supplies the evidence for it and stops.
