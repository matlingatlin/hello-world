---
name: design-claim-audit
description: "Use when a design, document or ADR has to be checked against what it claims to be — 'is this still true', 'does the code match the decision', 'review this design', 'has this finding been fixed', 'what did we miss'. Runs one named perspective per pass, checks each claim against an artefact, and emits a findings list where every row carries evidence at file:line and a verdict in {holds, refuted, not checkable here, abstained}. NOT for making a decision (design-decision-record), NOT for placing a boundary (seam-placement), NOT for auditing anything this agent authored — that abstains and goes to a fresh reviewer."
---

# Auditing a claim against the artefact it is about

Review works here. What fails here is **coverage, calibration and provenance**, and
those are the only three things this procedure touches.

The three failures it exists to prevent, all observed on this system:

- **One reviewer misses the worst thing.** Two independent reviews produced 35
  findings; the most serious — a cross-tenant idempotency replay — appeared in only
  one of them, and six findings were unique to that reviewer. A single pass is not
  coverage, and this procedure will not let you say it is.
- **A finding can be confidently wrong.** Both reviewers flagged two package names as
  suspicious. Both were genuine, published by the author of the library they extend.
  The true half of the same finding — no hashes across 52 pinned packages — inherited
  the discredit.
- **A claim about a document gets repeated on trust.** One document was described
  across the repository as reconciling the two reviews. It contains zero references
  to either review's finding numbers. The reviews were never paired.

Step 1 opens `references/perspectives.md`. Do not proceed without choosing one.

## 0 · Provenance — who wrote the thing you are auditing

For each artefact under audit, name its author: the ADR's own text, the document
header, or the session it came from. **If this agent produced it, in this session or
a previous one, the verdict is `abstained`** and the row names a fresh reviewer as
the route.

A model critiquing its own output with no external signal measures worse on every
model and every benchmark tested — in one case 75.8 to 38.1. Nothing mechanically
enforces this step; it is a procedure, not a wall. Record the abstention visibly so a
reader knows it was not audited rather than assuming it was.

**Artefact:** one author line per artefact, and an `abstained` row for each
self-authored one.

## 1 · Declare one perspective, and only one

Open `references/perspectives.md`. Choose exactly one. State it at the top of the
output. Hunt only that fault class; anything you notice outside it becomes an
**out-of-perspective referral** — one line, no investigation.

Differentiated procedures hunting different fault classes outperform undirected
review by roughly 35%, with a range of 15–50% across studies. **Undifferentiated
checklists measured no better than no procedure at all** — so a pass that sweeps
every category is the condition that buys nothing, not the thorough one.

**Artefact:** the perspective name, and the sentence
`this pass is one perspective and is not coverage; perspectives not run: <list>`.

## 2 · One row per claim, with the artefact it was checked against

For every claim: quote it, name the document and line asserting it, name the artefact
you opened to check it, and give the query or the `file:line`. A row without an
artefact is not a finding.

A claim about **what a document says** is checked by opening that document and
quoting the line — never by trusting a third document's description of it. If the
claim is that document A reconciles B and C, the check is whether A actually
references B and C's contents.

**Artefact:** per claim — the quote, the asserting `file:line`, the checked artefact,
the query.

## 3 · Run the check that would show it false

Before recording anything as `refuted`, run one query designed to **disconfirm** your
finding. A suspicious name is checked against its publisher. A missing guard is
checked for an equivalent guard under another name. An absent feature is checked with
a second vocabulary.

A finding with no disconfirming check recorded cannot be `refuted`; it is downgraded
to `not checkable here`.

**Artefact:** per finding — the disconfirming query and what it returned.

## 4 · Count instances, and say how many observations you have

Any number in a finding states what one unit is and comes from a named query. A count
of mentions is not a count of things.

Any claim about behaviour over time — stable, flaky, passing, unused — carries the
number of observations behind it. **One green run is one observation**, and this
repository has already recorded a suite written down as a verified baseline that a
later flaky test refuted.

**Artefact:** per number — the query and the unit. Per behavioural claim — the
observation count.

## 5 · Assign the verdict, and refuse where you must

Exactly one of four per row:

| Verdict | When |
|---|---|
| `holds` | the artefact shows what the claim says, and step 3 failed to disconfirm it |
| `refuted` | the artefact contradicts it, with the `file:line`, and step 3 was run |
| `not checkable here` | it needs execution, concurrency, load, timing or a real build. **This agent has no shell.** Say what would settle it |
| `abstained` | step 0 fired, or the evidence is a document's description of another document you could not open |

Race conditions, TOCTOU windows, throughput and "does this actually fire in
production" are always `not checkable here`. Reasoning from source is not
measurement, and a document that mixes the two makes both unreadable. Listing them
unresolved is the honest outcome; calling them still-true is a guess.

**Artefact:** one verdict per row, and a count of each verdict at the end.

## 6 · Emit

The findings list under `docs/`, using the structure the root reviews already use —
evidence with file and line, problem, consequence, root cause, recommendation, how it
would be verified, dependencies. That structure is what makes the pass mechanical
rather than interpretive; do not design a replacement.

Close with the coverage line from step 1 and the verdict counts from step 5.

Before reporting anything, check
`/home/user/scio/docs/as-built/REVIEWS-FINDINGS-VERIFIED.md` — 35 findings with their
state as of `bd4f6d7`. Re-reporting a fixed finding costs the list its credibility.

**Artefact:** the file path written, the verdict counts, and the coverage line.

## When this does not apply

- **You authored the artefact.** Step 0 abstains. Route it to a reviewer that did
  not write it; that separation found 81 defects in this project's own library.
- **Nothing is claimed.** An audit needs a claim to check. If the request is "look
  for problems" with no stated design, ask which document states the intent.
- **The finding requires running the system.** You cannot. `not checkable here` is
  the finished answer, not a failure to finish.
- **The right answer is that nothing is wrong.** Emit an empty findings list with the
  perspective, the artefacts opened and the queries run. A pass that always finds
  something cannot discriminate.
