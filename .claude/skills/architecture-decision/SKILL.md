---
name: architecture-decision
description: Turn an architectural question into a recorded decision. Derives the constraints that actually bind from load, failure, money and team shape; crosses one far domain before naming options; forces a real option set including the option not taken; names the falsifier that would reverse the choice; and emits an ADR. Use when choosing a stack, a datastore, a boundary, a protocol, a tenancy model, an auth model or a deployment shape, and when re-opening a decision that a new constraint has invalidated. Not for reviewing an existing design (use architecture-review) or for splitting a system into parts (use system-decomposition).
---

# Deciding, and being able to say why later

A decision you cannot reverse on evidence is a preference. This skill turns a
question into an ADR carrying its own falsifier.

**Every step emits a named artefact, and the artefact is the mechanism, not the
packaging.** Fischhoff's subjects, shown a fault tree with half its branches
deleted, assigned "everything else" **.140** where the normative answer was
**.468** — 30% of the gap. With attention explicitly directed at what was
missing they reached .217, still under half. One subject of 55 assigned enough,
and detection was uncorrelated with experience (τ = .058). A consideration you
thought about and did not write down did not land.

Three files this procedure opens, and when:

| File | Opened at |
|---|---|
| `references/far-domain-analogy.md` | step 2a, every time |
| `references/failure-modes.md` | step 4, every time |
| `references/evidence.md` | when you are about to put a number or a citation in an ADR |

## 0 · Refuse the question as asked, once

Architectural questions arrive pre-narrowed. "Postgres or Mongo" has already
decided that the system stores documents in a database it operates.

**Artefact:** one sentence naming the decision the question assumes has already
been made, and whether it has. If it has, cite where — ADR number, doc line. If
it has not, that is the decision to make first: stop and say so.

## 1 · Derive the constraints that bind

Not a checklist of qualities. A constraint binds only if you can state the
number and the source. Work these five, marking each **measured**,
**estimated** or **unknown**:

| Constraint | The question that produces a number | If unknown |
|---|---|---|
| Load | Requests, rows, bytes, concurrent tenants at the horizon you are designing for — and the horizon | Say what you will design for and what breaks past it |
| Failure | What is unacceptable to lose, for how long, and who notices | Say who decides, and that they have not |
| Money | Cost per unit of the thing users do, at that load, on this option | Estimate and mark it estimated |
| Team | How many people, in how many groups, will own the parts | Count the groups. This one is never unknown |
| Reversal | What it costs to undo this in six months | Cheap, expensive, or one-way |

**Artefact:** a five-row table with a value and a provenance mark in every row.
An `unknown` is an acceptable row; a silently omitted row is not.

Two rows carry more than they look. **Team shape** is the strongest-evidenced
predictor of post-release failure in this literature (86.2% precision, 84.0%
recall, beating all five code-metric families) — a boundary that does not match
the group boundary that will own it is a cost you record, not one you discover.
**Reversal cost decides how much of this procedure you owe**: say the cost, then
scale the rigour to it in writing. Both, with their limits and the direction of
the evidence, are in `references/evidence.md`.

## 2 · Force the option set

### 2a · Cross one far domain before you name an option

Open `references/far-domain-analogy.md` and run its four moves. Do this
**before** writing the option list, not after it as a sanity check.

This is the largest measured lever in the procedure — structured far-domain
analogy moved design fixation from 52.4% to 26.9% in 73 professionals
(p < 0.001), and cross-domain structural mapping raised generated-idea diversity
by 90–173%. Two things make it work, and both are in the reference: the domain
has to be far (near-domain examples anchor, far-domain examples feed), and the
mapping has to be **relational and written down** — a vague "look elsewhere"
measured nothing.

Naming your own first idea and then broadening is not an alternative to this
step. A **self-generated** first concept anchors *harder* than a provided
example (0.32 vs 0.24, p < 0.04). You cannot un-anchor yourself by trying.

**Artefact:** the two-or-three-row carry-back table — `domain → mechanism →
became`. "Produced nothing not already in the set" is a legitimate row. A
missing table is not: ~15% of runs in the closest measured study silently
skipped the step and declared the output already varied.

### 2b · Three options, and the third is the one that hurts

1. The obvious option.
2. The obvious option's main rival.
3. **The option that removes the need for the decision.** Not building it.
   Buying it. Doing it in the database you already run. Doing it by hand until
   the load justifies the machinery.

Plus anything step 2a carried back.

**Artefact:** each option gets one line on **what it costs when it is wrong** —
not what it costs. Every option looks fine on its happy path, which is why the
happy path does not discriminate.

Then, before comparing: two of three architectural risks are risks of
**omission** (57 vs 25 across the SEI's workshops, kappa .82), and that report
found no relationship between the goals stated up front and the risks found — so
a goals list will not surface them for you.

**Artefact:** name one thing that is in none of your options. If you cannot, you
have not looked; go back to step 1's `unknown` rows, which is where omissions
hide.

## 3 · Choose, and write the falsifier

The choice is one paragraph. The falsifier is the part with value.

**Artefact:** a sentence of the form *"Reverse this when X"*, where X is
something a person or a monitor could observe. `p99 write latency above N ms at
M tenants`. `More than one team needing to deploy this independently`. `The
vendor's price per unit crossing $K`. Not "if it doesn't scale".

If you cannot write an observable X, the decision is not falsifiable and you say
so in the ADR under `Consequences`, in those words. That sentence is what lets a
future session re-open the decision without re-litigating it.

## 4 · Check the choice against the seven ways architectures fail

Open `references/failure-modes.md`. Each mode has a measured source, a question
and a required artefact:

| # | Failure mode | Artefact it demands |
|---|---|---|
| 1 | Mishandled signalled errors (92% of catastrophic failures) | each new error path, with its handler named |
| 2 | Metastable failure from retries | the retry policy in numbers, or an explicit "no retries" |
| 3 | The wrong overload signal | the signal, the threshold, and what gets dropped |
| 4 | Dormant code reactivated | the grep you ran, and its result |
| 5 | Quadratic resource growth | the growth term, and the limit it hits first |
| 6 | Boundary crossed the wrong way | the arrow, and the module names at both ends |
| 7 | The computed signal nobody sees | the value, and either its consumer or a backlog item |

**Artefact:** seven rows. `none in scope` is a row; an omitted row is not.

Mode 7 is not generic — it is this codebase's most repeated defect, and the
reference names four confirmed instances. Assume this system's default failure
is computing the truth and dropping it.

## 5 · Emit the ADR

Copy `docs/decisions/0000-adr-template.md`, number sequentially, and fill:

- **Status** — Proposed unless a human has agreed. Proposed is not a weaker
  decision; it is an honest one.
- **Context** — the step-1 table, provenance marks intact.
- **Decision** — the choice, one paragraph.
- **Alternatives** — all options, each with its when-it-is-wrong line, plus the
  step-2a carry-back rows. The option that removes the decision is never
  omitted, even when obviously rejected: its absence is what makes a future
  reader assume it was never seen.
- **Consequences** — the step-4 artefacts, and the falsifier from step 3.

Any number or study you cite here is checked against `references/evidence.md`
first. A citation carried from memory is how the wrong Fischhoff figure got into
this file and into ADR-0021.

## When this skill does not apply

- The decision is already recorded and nothing has changed. Cite the ADR.
- The reversal cost is one file and one hour. Decide, note it in the commit,
  move on. Ceremony proportional to consequence.
- It is a coding choice, not an architectural one. If no second party has to
  live with it, it is not architecture.
