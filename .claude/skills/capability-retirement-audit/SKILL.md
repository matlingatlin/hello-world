---
name: capability-retirement-audit
description: "Use when deciding what an existing system should stop doing — inventorying built capabilities and ruling keep, rewrite, retire or unverified for each, with file:line evidence and a named consequence of deletion. The subtract pass that add-and-refine planning never contains. Produces the retirement inventory that a rebuild's keep/rewrite decisions are made from. NOT for reviewing a design against its claim (architecture-review), NOT for redrawing boundaries (system-decomposition), NOT for ruling on new candidate proposals (proposal-adjudication), and it never deletes anything itself."
---

# What should stop existing

Planning documents add. This one subtracts, and it exists because the subtract
column is structurally missing from the corpus it reads. The seven `docs/next/`
layer documents carry nine headings each —
*Where the layer stands · Refining what exists · What is missing · Out of the
box · The means · Retrieval versus packing · Token economy · Data worth owning ·
ADR proposals* (`/home/user/scio/docs/next/README.md:10-18`) — and **every one
of them adds or refines.** Across all 85 proposals the only deletions are
housekeeping. A rebuild asked "what to keep" cannot answer it from a corpus with
no slot for "not this".

**The literature will not help you and you must not pretend otherwise.** The one
large measured study of refactoring outcomes (328 Microsoft engineers plus the
Windows 7 version history) is equivocal in the inconvenient direction: the top 5%
preferentially refactored modules decreased post-release defects **7% *less***
than the rest, while reducing dependencies and increasing LOC. And the numbers
in circulation are worse than useless — the "IBM Systems Sciences Institute"
1:6.5:15:60–100 chart traces to internal 1981 corporate training notes with no
data and no method, the study does not exist; "60–80% of rewrites fail" and
"312 attempts across 89 organizations" are REPEATED or traceable to a paper that
does not contain them. **Any keep-versus-rewrite argument here rests on what
breaks, at `file:line`, and on nothing else.** Do not import a percentage.

This procedure opens
`.claude/skills/proposal-adjudication/references/corpus.md` at step 1 for the
absolute paths, and `.../references/evidence.md` before any number goes into a
document.

## 1 · Build the capability inventory from the artefact, not from the plan

Open `references/corpus.md` for the absolute paths — **`docs/as-built/` is not in
this repository**, and twelve files here cite it as though it were.

List capabilities: things the system does that someone could ask for by name. A
capability is not a module and not a file. Derive them from the as-built
documents, then confirm each exists in the working tree.

**Artefact:** capability → the `file:line` you opened → `confirmed in tree` or
`claimed in docs, not found`. The second verdict is a finding on its own and
does not proceed to step 3.

## 2 · Trace every capability to a consumer

For each one, who or what reads its output. Not a return statement — a consumer.
Trace it to a UI, an API caller, a stored record someone queries, a test that
would fail, or a human who looks at it.

This system's most repeated defect is an honest computation dropped before it
reaches anyone, and it is confirmed rather than suspected — `validate_plan`
produces nine rule ids and returns them to nothing; `checks_passed` is computed,
typed, transmitted and never rendered; `/usage/allowance` has no consumer; five
curation endpoints have no UI. Confirm each against the tree; do not recite them.

A capability with no consumer is the strongest retirement candidate in the
inventory, and it is also the one most likely to be a half-finished feature
rather than a dead one. Say which, with evidence.

**Artefact:** capability → consumer at `file:line`, or `no consumer` plus
`unbuilt | abandoned | internal only` and what decides between them.

## 3 · Ask what breaks, and answer it concretely

For each capability: **if this were deleted tomorrow, what specifically fails?**

Name the input, the actor and the wrong result. "Could cause issues" is not an
answer and does not go in the table. If nothing you can name fails, that is the
finding, and it is a strong one.

Then the harder half, which is where retirement audits go wrong: what does this
capability's *existence* cost — what other decisions has it constrained, what
does every new feature have to be compatible with because it is there. Only
answer where you can point at something.

**Artefact:** capability → `what breaks: <input, actor, wrong result>` →
`what it constrains: <named decision>` or `nothing I can point at`.

## 4 · Distrust the evidence that it works

A passing suite is evidence only if the doubles are no stricter than production.
This codebase has two confirmed cases of tests passing for the wrong reason: a
fake scope object that enforced more than the real one, and an
interaction-channel test whose canonical spec contained zero interaction
criteria, so it asserted nothing.

For each capability you are about to mark `keep`, ask of the test cited:

| Ask | Finding when the answer is bad |
|---|---|
| Does the double enforce *more* than production? | the test proves the double, not the system |
| Does the fixture contain an instance of the thing asserted? | vacuous pass |
| Would this test fail if the capability were removed? | no positive control; the test is decorative |
| How many times has it been run? | one green run does not refute an intermittent failure |

**Artefact:** for each `keep`, one of `verifies`, `verifies the double`,
`vacuous`, `unrun`. A `keep` resting on a `vacuous` test is downgraded to
`unverified`, not to `retire` — you have learned nothing about the capability,
only about the test.

## 5 · Rule

| Verdict | Bar |
|---|---|
| **keep** | a named consumer, and a test that would fail if it were removed |
| **rewrite** | the capability is wanted and the current form constrains a named decision. Say which decision — a rewrite verdict with no named constraint is a preference |
| **retire** | nothing you can name breaks, and either there is no consumer or the consumer is itself retired. Name what would have to be true for this to be wrong |
| **unverified** | you could not open the file, the test is vacuous, or the consumer trace is incomplete. **Required and honest.** It is not a soft `keep` |

**No verdict carries a cost estimate.** The rewrite-versus-refactor literature is
empty; a cost number here would be manufactured, and manufacturing one is how a
normative value gets published in this repo as though it were observed.

**Artefact:** the inventory table, plus two counts: how many verdicts you
verified yourself against the tree, and how many you carried from another
document. Carrying four and verifying one is a fine outcome; reporting five
verified is not.

## 6 · Stop, and say what you did not check

One pass. Do not re-run this on the same evidence — a second pass with no new
evidence measured worse across every model and benchmark tested (GPT-4 on GSM8K
95.5% → 91.5% → 89.0%). If you are unsatisfied, the remedy is new evidence: the
file you skipped, the test someone else can run, the consumer you could not
trace.

**Artefact:** one line naming what you did not check and why. This is the line
that is most often left out, and absence of a result is not a negative result.

## When this does not apply

- Nothing is built yet. There is nothing to retire.
- You are checking whether a design does what it claims. That is
  `architecture-review`.
- The question is where the boundaries should fall. That is
  `system-decomposition`.
- You are being asked to perform the deletion. This procedure produces verdicts
  and hands them over; it does not delete, and the agent running it holds no
  tool that could.
