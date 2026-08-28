---
name: blank-slate-positions
description: "Use when producing candidate directions for a product from a problem brief alone, with no access to how the product is currently built — turning a brief into falsifiable positions, explicit refusals, and mechanisms carried back from a non-software domain by a written relational map. Decides what could exist and what should be refused, never what is currently there. NOT for judging, deduplicating or ranking candidates (proposal-adjudication, selection-dossier), NOT for reviewing an existing design (architecture-review), NOT for making a recorded decision (architecture-decision)."
---

# Positions from the brief, and mechanisms from somewhere else

You have a problem brief and no description of any existing solution. Two things
follow, and both are counter-intuitive enough to state outright.

**Writing your own first sketch does not protect you from anchoring — it is
worse.** Fixation on a self-generated first concept measured **M = 0.32**
against **M = 0.24** for a *provided* example, F(1,165) = 4.4, p < 0.04, n = 185.
So step 1 is not a defence against narrowness, and you must not treat it as one.
It is there to make your assumptions visible so they can be argued with. The
defence is step 3, and it only works when it is **written down as a mapping**: a
vague instruction to look elsewhere measured nothing.

**Your brief is raw material, not requirements.** Identical content labelled
"ideas" rather than "requirements" measured originality **3.43 against 2.67**
(Mann-Whitney U = 116.5, p = 0.004, r = 0.428, n = 42, all from a software
background). The label alone. Read it as somebody's opening argument.

This procedure opens exactly one file, at step 3:
`.claude/skills/architecture-decision/references/far-domain-analogy.md`. It is
the only file besides your brief that you are permitted to read, and it carries
the four moves plus their limits. Do not work from its gist.

## 1 · Read the brief and write down what it does not say

Read `docs/rebuild/brief/*.md`. Then, before anything else, write the list of
things the brief **leaves undetermined** — the questions a person would have to
answer before any of this could be built, that the brief does not answer.

This step exists because of a measured asymmetry: a reader distributes attention
across the branches a document names, and what it does not name is close to
invisible. Given a fault tree with half its branches deleted, subjects assigned
**.140** to "all other problems" where the normative answer was **.468**, and
**1 subject in 55** assigned enough. Experience did not help — correlation with
detection τ = .058.

**Artefact:** the undetermined list. Each row is a question, not a topic, and
each is marked `assumed <X> for this run` or `left open`. An assumption you made
and did not write down will read as a finding later.

## 2 · Take positions, each with its refusal

A position is a claim someone could disagree with. Not "the product should be
easy to use" — *"the person never sees a file tree, and if they ask for one the
answer is no, because the moment they are managing files they are doing the job
they came here not to do."*

For each position write:

- **The claim**, in one sentence, in the language of the problem. No product
  name, no protocol, no vendor, no layer.
- **What it refuses.** Non-goals are the half of scope that never gets written
  down, and a position with nothing on this line is a preference, not a position.
- **What would make it wrong.** A named observation, not "if users disagree".
- **The moment of trust.** Where in the person's experience this position is
  either earned or lost, and what has to be true at that moment.

Do not group positions by any structure you were given. If the brief implies a
sequence of stages, that sequence is a hypothesis, and a position that the
sequence should be different is one of the positions you can take.

**Artefact:** the position list. No count is set and none may be inferred:
quotas act as ceilings — told "5–7" people produced 7, told "at least 20" they
produced 21, told nothing they produced **29**. Stop when you stop having
positions, not when you reach a number.

## 3 · The far-domain relational map

Open `.claude/skills/architecture-decision/references/far-domain-analogy.md` and
run its four moves against the **function in the brief**, not against your
positions: strip the technology nouns, name one non-software domain that
performs the same function, fill the relational map both columns, carry back
exactly one mechanism per domain in that domain's own words.

This is the largest measured lever available to you — far-domain structured
analogy moved design fixation **52.4% → 26.9%** (p < 0.001, 73 practising
professionals), and cross-domain structural analogy moved LLM idea diversity
**+90–173%** with novel-solution rate **1.6% → 50.4%**, compute-matched. The
reference file carries the limits, including that the LLM result is one paper,
one domain, unreplicated. Read them; direction is measured, magnitude is not.

Two domains worked properly beat six listed. A row of the map you cannot fill on
our side **is the finding** — it is usually the mechanism the domain treats as
mandatory and this problem has never been given.

**Artefact:** the filled map, plus a carry-back table. Every row ends in a new
position, an addition to the step-1 undetermined list, or an explicit
`does not transfer, because …`. **An empty result is a result and is written
down; a missing table is not.** In the study behind this step, **~15% of runs
silently skipped the differentiation step and declared the ideas already
varied** — those runs are discarded rather than read, so the absence of this
table costs you the whole run.

## 4 · Name the framing of each candidate

Before you emit, label each position and each carried-back mechanism with the
kind of opportunity it claims to be — one of `bridge two disconnected things`,
`synthesise or unify`, `remove something`, `invert an assumption`,
`serve an actor nobody serves`, `change what is measured`, `other: <name it>`.

You are labelling, not fixing. The reason is measured: across 11,683 papers and
9 model configurations given identical context, LLMs framed opportunities as
"bridge two disconnected things" **47.1–64.2%** of the time against a human
**12.1%**, and "synthesise/unify" **22.5–38.7%** against **5.1%** — a 4–5×
over-concentration, with normalised entropy 0.550–0.758 against 0.926.
Individually each such candidate reads fine; the distribution is the defect, and
it is only visible once the labels are on the page.

Do **not** delete or rewrite candidates to flatten the distribution. The
adjudicator does that arithmetic with the full corpus in front of it. Your job
is to make it possible.

**Artefact:** one framing label per candidate, and the count per label.

## 5 · Emit

Write one file to `docs/rebuild/candidates/<run-id>.md` containing: the
undetermined list, the positions, the relational map, the carry-back table, the
framing counts, and one closing line naming what you would have wanted to read
and could not. You cannot read this file back — that is deliberate, and the
external signal is the adjudicator, not another pass of your own.

**Artefact:** the file, and its path in your final message.

## When this does not apply

- You have been given the existing design, or you can open it. Then you are not
  a blank slate and this procedure's evidence does not apply to you; hand the
  job to `architecture-decision`, which is built for a saturated context.
- The question is whether an option is good. That is `proposal-adjudication`.
- One decision with a known option set. That is `architecture-decision`, and it
  runs the same analogy pass from the other side.
