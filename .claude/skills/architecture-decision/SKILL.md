---
name: architecture-decision
description: Turn an architectural question into a recorded decision. Derives the constraints that actually bind from load, failure, money and team shape; forces a real option set including the option not taken; names the falsifier that would reverse the choice; and emits an ADR. Use when choosing a stack, a datastore, a boundary, a protocol, a tenancy model, an auth model or a deployment shape, and when re-opening a decision that a new constraint has invalidated. Not for reviewing an existing design (use architecture-review) or for splitting a system into parts (use system-decomposition).
---

# Deciding, and being able to say why later

A decision you cannot reverse on evidence is a preference. This skill is the
procedure that turns a question into an ADR carrying its own falsifier.

Every step below **emits a named artefact**. That is deliberate and it is the
part most easily skipped. Fischhoff's 1978 fault-tree experiments measured what
happens when you merely *raise* a missing consideration: subjects moved the
probability they assigned to "everything else" from .078 to .468 when the
branch was restored — but when simply asked to think harder, they roughly
doubled it, and 1 of 55 got it right. Expertise made no difference. Directing
attention at the omitted branch moved .227 to .346: real, and a fraction of
the gap. A consideration you thought about and did not write down did not land.
So each rule here ends in a number, a name, a row, or a deleted line.

## 0 · Refuse the question as asked, once

Architectural questions arrive pre-narrowed. "Postgres or Mongo" has already
decided that the system stores documents in a database it operates.

**Artefact:** one sentence naming the decision that the question assumes has
already been made, and whether it has. If it has, cite where (ADR number, doc
line). If it has not, that is the decision to make first — stop and say so.

## 1 · Derive the constraints that bind

Not a checklist of qualities. A constraint binds only if you can state the
number and the source. Work these five, and mark each one **measured**,
**estimated**, or **unknown**:

| Constraint | The question that produces a number | If unknown |
|---|---|---|
| Load | Requests, rows, bytes, concurrent tenants at the horizon you are designing for — and the horizon | Say what you will design for and what breaks past it |
| Failure | What is unacceptable to lose, for how long, and who notices | Say who decides, and that they have not |
| Money | Cost per unit of the thing users do, at that load, on this option | Estimate and mark it estimated |
| Team | How many people, in how many groups, will own the parts | Count the groups. This one is never unknown |
| Reversal | What it costs to undo this in six months | Cheap, expensive, or one-way |

**Artefact:** a five-row table with a value and a provenance mark in every row.
An `unknown` is an acceptable row and a silently omitted row is not.

Two of these are load-bearing beyond their appearance:

**Team shape is the strongest-evidenced predictor in the literature.** Nagappan
et al. (ICSE 2008) measured eight organisational metrics against post-release
failures on 3,404 Windows Vista binaries: 86.2% precision, 84.0% recall,
beating code churn, complexity, coverage, dependencies and pre-release bugs —
all five code-metric families. If the boundary you are drawing does not match
the group boundary that will own it, you are choosing to pay Conway's tax and
you should say so in the ADR rather than discover it. (Note the direction of
the evidence: organisation *predicts* defects. The inverse Conway manoeuvre —
reshaping the org to get the architecture — is widely repeated and, as far as
this skill's sources go, never measured. Do not cite it as if it were.)

**Reversal cost decides how much of this procedure you owe.** A cheap,
one-file, one-week reversal does not deserve a four-option comparison. Say the
cost and scale the rigour to it, in writing.

## 2 · Force the option set

Three is the floor, and the third is the one that hurts:

1. The obvious option.
2. The obvious option's main rival.
3. **The option that removes the need for the decision.** Not building it.
   Buying it. Doing it in the database you already run. Doing it manually until
   the load justifies the machinery.

**Artefact:** each option gets one line on *what it costs when it is wrong* —
not what it costs. Every option looks fine on its happy path; that is why the
happy path does not discriminate.

Then, before comparing: **the SEI's Mission Thread Workshop technical report
(CMU/SEI-2009-TR-012) classified the risks its workshops surfaced and found 57
risks of omission against 25 of commission** (two raters, kappa .82). Two out
of three architectural risks were things not there rather than things there
wrongly. The same report found *no relationship* between the business goals
stated up front and the risks actually discovered — so a goals list will not
find them for you.

**Artefact:** name one thing that is in none of your options. If you cannot,
you have not looked; go back to step 1's `unknown` rows, which is where
omissions hide.

## 3 · Choose, and write the falsifier

The choice is one paragraph. The falsifier is the part with value.

**Artefact:** a sentence of the form *"Reverse this when X"*, where X is
something a person or a monitor could observe. `p99 write latency above N ms at
M tenants`. `More than one team needing to deploy this independently`.
`The vendor's price per unit crossing $K`. Not "if it doesn't scale".

If you cannot write an observable X, the decision is not falsifiable and you
must say so in the ADR under `Consequences`, in those words. That sentence is
what lets a future session re-open the decision without re-litigating it.

## 4 · Check the choice against the seven ways architectures fail

These are not a quality checklist. Each is a failure mode with a measured
source and each asks for an artefact.

| # | Failure mode | The question | Artefact |
|---|---|---|---|
| 1 | **Mishandled signalled errors.** Yuan et al. (OSDI 2014) traced 198 randomly-sampled failures in five distributed systems: 92% of catastrophic failures came from incorrect handling of errors that were *explicitly signalled in software*, and 58% of those were catchable by simple testing of the handler | Which error paths does this option create, and does any of them log-and-continue, catch-all, or `TODO`? | Name each new error path and its handler. A path with no named handler is a finding |
| 2 | **Metastable failure.** Huang et al. (OSDI 2022) found retry-induced work is the sustaining effect in over half of studied metastable failures: load returns to normal and the system stays down, because the retries are now the load | What retries here, how many times, with what backoff and what cap? | The retry policy, in numbers, or an explicit "no retries" |
| 3 | **The wrong overload signal.** WeChat's DAGOR ran five years in production: the signal that works is *request queuing time*, not CPU or memory, and it shed load ~50% better than CoDel | When this is overloaded, what does it measure to know, and what does it drop first? | The signal, the threshold, and what gets dropped |
| 4 | **Dormant code reactivated.** Knight Capital repurposed a flag that a dead 8-year-old code path still read, deployed to 7 of 8 servers, and lost $460M in 45 minutes | Does this option reuse a name, flag, column or route that something else still reads? | The grep you ran, and its result |
| 5 | **Quadratic resource growth.** AWS Kinesis, Nov 2020: per-peer threads meant fleet-wide thread count grew with the square of the fleet; a small capacity addition crossed an OS thread limit; ~17 hours | What in this option grows faster than linearly in tenants, peers, files, or fleet size? | The term, and the limit it will hit first |
| 6 | **Boundary crossed the wrong way.** The dependency you are creating points from the stable thing to the volatile one, or from a lower layer up | Draw the arrow. Which way does it point? | The arrow, and the module names at both ends |
| 7 | **The computed signal nobody sees.** A value the system honestly computes and then drops before it reaches a person | What does this option compute that no consumer reads? | The value, and either its consumer or a backlog item |

Failure mode 7 is not generic. It is the single most repeated pattern in this
codebase's own as-built analysis: `validate_plan` produces nine rule ids and
returns them to nothing; `checks_passed` is computed, typed, transmitted and
never rendered; `/usage/allowance` has no consumer; five curation endpoints
have no UI. The as-built document's own conclusion is that *a rebuild which
only surfaced what is already computed would deliver most of the claimed
differentiator without inventing anything.* Assume this system's default
failure is computing the truth and dropping it.

## 5 · Emit the ADR

Copy `docs/decisions/0000-adr-template.md`, number sequentially, and fill:

- **Status** — Proposed unless a human has agreed. Proposed is not a weaker
  decision; it is an honest one.
- **Context** — the step-1 table, provenance marks intact.
- **Decision** — the choice, one paragraph.
- **Alternatives** — all three options, each with its when-it-is-wrong line.
  The option that removes the decision is never omitted, even when obviously
  rejected: its absence is what makes a future reader assume it was never seen.
- **Consequences** — the step-4 artefacts, and the falsifier from step 3.

## When this skill does not apply

- The decision is already recorded and nothing has changed. Cite the ADR.
- The reversal cost is one file and one hour. Decide, note it in the commit,
  move on. Ceremony proportional to consequence.
- It is a coding choice, not an architectural one. If no second party has to
  live with it, it is not architecture.
