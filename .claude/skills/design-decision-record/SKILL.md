---
name: design-decision-record
description: "Use when a shape question about Scio has to be decided and written down — a datastore, a tenancy model, a queue, a boundary, a protocol, a build target — or when someone asks for an ADR, asks 'should we use X or Y', or is about to build on a decision nobody has ratified. Decides one question, names the unsettled decisions it stands on, and emits an ADR at docs/decisions/ with a rejection reason per rejected option. NOT for reviewing a design already made (design-claim-audit), NOT for deciding where a boundary goes (seam-placement), NOT for product scope, pricing or feature priority — those go back to the planning chat as open questions."
---

# Recording a decision that can be argued with later

An ADR is only worth writing if a later reader can tell whether it was wrong. Three
things make that possible and are the only three this procedure enforces: **what the
decision stands on**, **why each rejected option was rejected**, and **what would
have to be observed for the decision to be wrong**.

The rule that overrides the natural approach: **before deciding, look for the place
the decision has already been made.** In this repository decisions have repeatedly
been written in prose and never promoted into the register — the MVP definition sat
complete in a review document while the backlog tracked it as open, and the clearest
statement of the core loop, twelve numbered steps, was recorded nowhere. A new ADR
that re-decides a settled question is worse than no ADR, because now there are two.

The ADR conventions are settled and not restated here. Copy the shape from
`docs/decisions/0000-adr-template.md`. Statuses of other ADRs are read **verbatim**.

## 1 · Find the governing decision

`Glob docs/decisions/*.md`. Read `/home/user/scio/docs/as-built/01-DECISIONS.md` for
the register with its statuses. Identify which existing ADRs this question sits
under or would supersede.

**Artefact:** the ADR numbers this question is governed by, or the line
`no governing ADR — this is a new decision`, plus the glob you ran.

## 2 · List what it stands on that is not settled

Every ADR in the chain from step 1 whose status is `Proposed` or `Partly
implemented`. Three of twenty are in that state and anything downstream of them is
standing on an open question.

If the question cannot be answered without one of them, **stop and say so** — emit
the dependency, not a decision.

**Artefact:** one row per unsettled decision: number, status verbatim, and what this
decision would inherit from it. Or the line `stands on no unsettled decision`.

## 3 · Search for the decision already made in prose

Grep the places decisions have leaked to: `docs/*.md`,
`/home/user/scio/docs/as-built/*.md`, `docs/decisions/`. Use at least two
differently-worded queries for the subject — a decision written in someone else's
vocabulary will not match yours.

If you find it: the ADR **promotes** that text and cites where it was found. If you
do not: record the negative with the queries, so the next reader knows the search
happened rather than assuming it did.

**Artefact:** either `already decided at <file:line>` with the quoted passage, or
the two-or-more query strings you ran and the count each returned.

## 4 · Check the question is at the right level

Ask what the question presupposes. If the answer changes depending on a decision
upstream, the upstream one is the real question. The intake schema was criticised
for its vocabulary when the answerable question was whether ADR-0001's wedge still
held — redesigning intake first would have been the wrong work.

**Artefact:** `answerable here`, or `upstream: ADR-NNNN must be settled first` — and
in the second case stop, and emit that instead of a decision.

## 5 · Options, each with a rejection reason that costs something

At least two real options. For each rejected one, name **what it would have cost**
concretely — a migration, a vendor lock, a class of bug, an operational burden. Not
"less suitable", not "does not fit our needs". If a rejection reason would apply
equally to the chosen option, it is not a reason.

Only claims you have checked go in this table. Anything unchecked is marked
`asserted, not checked` in the row itself.

**Artefact:** N option rows, N−1 rejection reasons, each naming a cost.

## 6 · Reversibility, and the claim that could be falsified

State how hard this is to undo: `reversible in a session` / `reversible with a
migration` / `one-way`. Then write the sentence that would show it was wrong, and
name where that would be observable — a metric, a file, a test, an incident shape.

**Artefact:** one reversibility class and one falsifiable sentence with its
observation point.

## 7 · Emit

Number = highest existing ADR number from step 1, plus one. `Status: Proposed`.
Write to `docs/decisions/NNNN-<slug>.md`. If the write is denied because the file
exists, your number is stale — re-run the glob rather than picking another name.

If this decision supersedes another, say which. You cannot mark the old one; name
it so a human can.

**Artefact:** the file path written, and the number of the ADR it supersedes if any.

## When this does not apply

- **The question is product scope, pricing or priority.** Not an architecture
  decision. Return it as an open question with what would settle it.
- **Step 2 or step 4 stopped you.** The artefact is the dependency, not an ADR.
  Writing one anyway records a decision resting on nothing.
- **The decision is already recorded** (step 3 found it). Cite it. A second ADR on
  a settled question creates a conflict that a later reader has to adjudicate.
- **You are checking whether an existing decision still holds.** That is
  `design-claim-audit`.
