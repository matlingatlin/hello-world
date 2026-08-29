---
name: agent-review-pass
description: "Use when reviewing one agent in .claude/agents/ against one named fault class - its content's grounding, the currency of what it cites, whether its wall matches what its body claims, whether anything routes into it, or whether the artefacts it promises exist. Forces exactly one lens per pass, a unit list before any finding, a query or file:line under every row, and a disconfirming check before a row is recorded. Produces the findings table. NOT for sweeping every fault class in one pass, which is the condition measured no better than no procedure at all; NOT for writing the verdict (agent-fitness-verdict); NOT for repairing what it finds."
---

# One pass, one lens, one findings table

A review that hunts everything finds what a reader already suspected. Differentiated
procedures hunting **one named fault class** outperformed undirected review by roughly
35% — 15–50% across replications — and **undifferentiated checklists measured no better
than no procedure at all**. That is the finding this whole procedure is built around,
and it overrides what a competent reviewer naturally does, which is read the artefact
top to bottom and note what seems wrong.

Two limits, so you do not over-trust the number: the effect was weakest on material the
reader already knew, with subjects reporting they *"fell back to their usual
technique"*; and one of two replications was not significant (21%, p = 0.21) while the
other was (30%, p = 0.0019). Reviewing a repository you have already read is exactly the
weak condition. Recording each step's artefact is what stops the fallback.

Open `references/lenses.md` at step 1 — it holds the five lenses and the procedure for
each. Open `references/mechanical-inputs.md` at step 2 — it holds what you must be
given rather than derive.

## 0 · Establish who wrote what, and abstain where you cannot judge

For every artefact you are about to open — the agent file, each preloaded skill, each
reference, the spec, the hook proposals, the eval record — say who authored it and
whether you can judge it. If you wrote it, you may not rule on it: a model critiquing
its own output with no external signal measures worse on every model and benchmark
tested. Its rows are `abstained`, and the document says which and why.

You cannot have authored an agent *file* — you cannot write under `.claude/` at all —
but you could have written a document under `docs/`. Check.

**Artefact:** a provenance table, one row per artefact — `artefact · author · auditable
or abstained`. If nothing abstains, say *"step 0 did not fire"* and say why.

## 1 · Declare exactly one lens

Open `references/lenses.md`. Choose the lens the request names. If the request names no
fault class, take **L1 · Grounding** first: it has the highest yield on this repo's own
recorded runs and it is the one a familiar reader is least likely to run unprompted.

Then write, verbatim, in the document:

> this pass is one lens and is not coverage; lenses not run: [the other four, named].

Anything you notice outside your lens is **one line of referral at the end**, not an
investigation. Coverage is the caller dispatching more of you, in parallel, on other
lenses. Widening your own pass is the checklist condition, and it buys nothing.

**Artefact:** the lens name, and the coverage sentence.

## 2 · Take the mechanical result; do not re-derive it

Open `references/mechanical-inputs.md`. It lists the programs that already decide part
of this question deterministically, and what each one covers.

You hold no `Bash`. So for every mechanical input the lens needs, one of two things is
true, and the document must say which:

- the caller handed you its **raw output**, which you quote; or
- it is missing, and you **stop the pass** and return the exact command for the caller
  to run and re-dispatch you with.

You do not simulate a checker by reading its source. Restating a rule in prose while
the program that implements it sits unreferenced is a recorded defect of this repo's own
loop, found independently by two audits; committing it one layer up, inside a reviewer,
would be worse, because a reviewer's output is what someone else trusts.

**Artefact:** for each required input — `command · raw output quoted, or MISSING and
handed up`.

## 3 · Enumerate the units before you look for anything wrong

The lens tells you what its unit is: a rule, a cited number, a stated impossibility, a
description pair, a promised artefact. Enumerate **all** of them first, with a count,
before forming any judgement. A review that starts from the first suspicious thing
reports what caught the eye; a review that starts from the denominator can report a
zero.

State the unit in words. *"A count of mentions is not a count of things"* — that exact
error was committed inside a checker written to catch it, because the unit was never
written down.

**Artefact:** `unit = …`, the count, and the query or listing that produced it.

## 4 · One row per unit

Every row carries: the unit; the quote or `file:line`; what the artefact actually shows;
and a verdict from the lens's own vocabulary. A row with no query behind it cannot be
re-run by anyone, which means it cannot be refuted, which means it is an opinion.

Zero-count rows are findings, not blanks. In a structured risk-discovery workshop, 57 of
82 risks were risks of omission against 25 of commission.

**Artefact:** the findings table, every row carrying its query or `file:line`.

## 5 · Disconfirm every finding before you record it

For each row you are about to mark as a problem, run one query designed to **kill** it:
a second vocabulary, a different spelling, the same claim under another name, the note
one hop away in a `related:` list, the earlier version of the source. Record the
disconfirming query and its result whether or not the finding survives.

This is not politeness. On this repo's two recorded audits it killed real drafts: one
auditor drafted *"+19.0pp is fabricated"* off an old version of a paper, fetched the
current one, got the figure exactly, and recorded `holds`; another narrowed a
three-section finding to one section the same way. A review that only accuses is not
calibrated — 26 of 34 checkable assertions held in one of those passes.

State the observation count behind any behavioural row. One green run is one
observation. *(`unevidenced` — whether to require repeated runs and report variance is
argued in a knowledge note that carries no per-claim verdict; this step asks you to
state the count, not to repeat.)*

**Artefact:** per finding — `disconfirming query · result · survives or killed`.

## 6 · Say what mechanism each surviving finding needs

Do not propose the fix. Classify what kind of thing would close it, because that is
what the reader has to decide:

| Class | Meaning |
|---|---|
| `mechanism` | it is written as prose and must be a hook or an absent tool to hold |
| `content` | a rule, number or claim to be corrected — a proposal a human applies |
| `unowned` | real, and belongs to a part that does not exist yet |
| `elsewhere` | a different part's job; name the part |

A finding whose only remedy is "the prompt should say not to" is `mechanism`, and the
row must say so — prose warnings failed in three studies and backfired in a fourth.

**Artefact:** a class on every surviving row.

## 7 · Hand over

The findings table plus the coverage sentence go to `agent-fitness-verdict`, which owns
the bar, the blind-spot list and the accounting. Do not write a verdict here — a review
that ends in findings and no verdict has ended in a stance, which is the shape this
loop's own terminal step was caught in.

**Artefact:** the completed table, handed to `agent-fitness-verdict`.

## When this does not apply

- **The agent does not exist yet.** What goes wrong *without* an agent is
  `agent-baseline`; what an agent should be is `agent-shape`.
- **The question is whether a cited source carries a claim.** That is
  `primary-source-verifier`, and it needs a tool surface this pass does not have.
- **The artefact is not an agent** — an ADR, a layer document, a PRD. The
  `design-claim-audit` skill owns document-level claim auditing, also one perspective
  per pass.
- **The question is whether adopting a surface is dangerous.** Security risk is
  `/home/user/skills-repo/.claude/skills/agent-surface-security-audit/`.
- **You are being asked to run every lens at once.** Decline and say why: that is the
  measured-null condition. Ask for parallel dispatches instead.
