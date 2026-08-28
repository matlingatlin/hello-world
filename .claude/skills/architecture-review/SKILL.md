---
name: architecture-review
description: Review an existing design, diff or codebase against what it claims to be, and produce findings that can be acted on or refuted. Derives the requirements the claim implies before opening a file, crosses one far domain to catch what the claim never mentioned, checks every claim against file and line, distinguishes a computed-and-dropped signal from a missing one, and refuses green evidence from doubles stricter than production. Use when reviewing a design document, a proposed change, a layer of an existing system, or a review someone else wrote. Not for making a decision (use architecture-decision) or for redrawing boundaries (use system-decomposition).
---

# Reviewing what is there against what is claimed

Three measured facts set the shape of this procedure, and the numbers behind all
three are in `references/review-evidence.md`.

**Most architectural risk is absence** — 57 risks of omission against 25 of
commission across the SEI's mission-thread workshops, and no relationship between
the goals stated up front and the risks found. A goals list will not surface them.

**Reviewing your own work is harder, not easier.** Teaching architects about
their biases produced *no* debiasing effect; the same techniques worked only when
applied as a procedure to the architecture in hand. So run the steps. Do not
recall them.

**A second pass with no new evidence makes it worse** — GPT-4 on GSM8K
95.5% → 91.5% → 89.0% across self-review rounds. What works is an external
verifier: the file, the line, the test, the graph.

This procedure opens two files: `references/review-evidence.md` when a number or
a limit is going into the review, and, at step 2b, the analogy procedure shared
with the other two skills — `../architecture-decision/references/far-domain-analogy.md`,
which is `.claude/skills/architecture-decision/references/far-domain-analogy.md`
from the repo root.

## 1 · Fix the claim before looking

Write the thing being reviewed as a claim you can be wrong about. Not "review the
build layer" — *"the build layer produces a running app from a plan, and reports
honestly what it verified."*

**Artefact:** the claim, in one sentence, before you open a file. Everything
below is evidence for or against it.

## 2 · Enumerate the omissions first, from the shape of the claim

Do this before reading code, because after you read code the code sets your
agenda and you will only find what is there. From the claim, derive the list of
things that *would have to exist* for it to be true:

- Every input the claim implies, and its validation.
- Every error the claim implies, and its handler.
- Every state the claim implies, and its exit.
- Every output the claim implies, and its reader.
- Every actor the claim implies, and their authorisation.

**Artefact:** the derived list, written before the first file is opened. Then
mark each `present`, `absent` or `unreachable`. `unreachable` is its own verdict
and this codebase needs it: it has a queue state nothing can enter.

### The boundary on this rule — it is narrower than it sounds

"Derive before you look" is supported **for finding what is absent**, which is
what this step does. It is **not** a defence against anchoring, and it must not
be carried into any step where you are producing a design.

Measured: fixation on a **self-generated** first concept was **0.32** against
**0.24** for a *provided* example — F(1,165) = 4.4, **p < 0.04**, n = 185. Your
own first sketch anchors *harder* than someone else's, and a 23-minute delay did
not dissolve it.

| You are | Derive cold first? |
|---|---|
| enumerating what must exist, to find omissions | **yes** — this step |
| proposing a replacement, alternative or redesign | **no protection**; run the analogy pass instead, and hand the decision to `architecture-decision` |

Limits — no true no-example control, novice subjects, no study of fixation on
software architecture at all — are in `references/review-evidence.md`. Read them
before you quote the numbers.

### 2b · One far-domain pass over the derived list

The list you just wrote is bounded by the claim's own vocabulary, which is
exactly the pruning Fischhoff measured: readers distribute attention across the
branches a document names, and pointing at the gap afterwards recovers under half
of it.

Open `../architecture-decision/references/far-domain-analogy.md` and run moves
1–3 against the claim's function: strip the technology nouns, name one non-
software domain that performs the same function, fill the relational map. Then
ask the one question this step exists for: **which element that domain treats as
mandatory has no counterpart anywhere in my derived list?** A kitchen has
expediting. A hospital has handoff. A bank has reconciliation. A post office has
a dead-letter office.

Structured far-domain analogy is the largest measured lever available here
(fixation 52.4% → 26.9%, p < 0.001, 73 professionals), and the measured effect
comes from the written relational mapping — a vague "think laterally" measured
nothing.

**Artefact:** the domain, and for each mandatory element either a **new row
added to the step-2 list** or `no counterpart needed, because …`. Producing no
new rows is a legitimate outcome and is written down; skipping the table is not.

## 3 · Check the outputs for the drop

This system's most repeated defect is not a missing computation. It is an honest
computation dropped before it reaches anyone: `validate_plan` produces nine rule
ids and returns them to nothing; `checks_passed` is computed, typed, transmitted,
never rendered; `/usage/allowance` has no consumer; five curation endpoints have
no UI.

So for every value the claim says the system produces, **trace it to a consumer**,
not to a return statement.

**Artefact:** value → consumer, or value → `no consumer`. A `no consumer` row is
a finding with a proposed destination, not an observation.

## 4 · Distrust green

A passing suite is evidence only if the doubles are no stricter than production.
This codebase has two confirmed cases of tests passing for the wrong reason: a
fake scope object enforced more than the real one, and an interaction-channel
test whose canonical spec contained zero interaction criteria, so it asserted
nothing.

For each test cited as evidence:

| Ask | Finding when the answer is bad |
|---|---|
| Does the double enforce *more* than production? | The test proves the double, not the system |
| Does the fixture contain an instance of the thing asserted? | Vacuous pass — assert the count of the input first |
| Would this test fail if the behaviour were removed? | No positive control; the test is decorative |
| How many times has it been run? | One green run does not refute an intermittent failure |

That last row is not hypothetical here: a `design.test.tsx` flake failed two
different tests on two consecutive runs, then passed three times, cause never
found — while a single green run of each suite was written down as a verified
baseline. **One observation is not a baseline.** Say which it is.

**Artefact:** for each cited test, one of `verifies`, `verifies the double`,
`vacuous` or `unrun`.

## 5 · Order the checks by what has actually killed systems

Five failure classes with measured incidence, in order. The sources, the numbers
and this repo's instance of each are in `references/review-evidence.md`.

| # | Class | What to produce |
|---|---|---|
| 1 | **Error handling** — 92% of catastrophic failures came from mishandled *signalled* errors | every catch block in scope, with log-and-continue, catch-all and `TODO` named |
| 2 | **Authorisation ordering** — a guard that runs second is not a guard | for each identity check, what runs before it, at `file:line` |
| 3 | **Retry and overload** — retries sustain over half of metastable failures | the retries, the backoff, the cap, and the shed signal (queuing time, not CPU) |
| 4 | **Growth terms** — anything counted per-peer, per-tenant, per-file, per-fleet-member | the term and the limit it hits first |
| 5 | **Reactivated names** — a reused flag, column, route or constant | the grep for every reader of the name, and its result |

**Artefact:** each class gets a row, even when the row says `none in scope`. An
absent row and a clean row are indistinguishable to the next reader, and absence
of a result is not a negative result.

## 6 · Write findings that can be refuted

A finding that cannot be checked cannot be fixed or dismissed, so it stays open
forever. Each one carries:

- **Where** — `file:line`, or the doc heading. Never "in the build layer".
- **What is true** — the observed fact, stated so it can be shown false.
- **Why it matters** — the concrete failure, with inputs and the wrong result.
  Not "could cause issues".
- **State** — `live`, `fixed`, `false positive` or `unverified`. `unverified` is
  honest and required when you took it on another document's word.
- **Cost to fix** — so the reader can triage without re-deriving it.

**Artefact:** the findings table, and a count: how many findings you verified
yourself against code versus carried over from another document. Carrying four
findings from a prior review and verifying one is a fine outcome; reporting four
verified is not.

## 7 · Stop

You have run the procedure once. Do not run it again on the same evidence — the
third fact at the top of this file says that makes it worse. If you are
unsatisfied, the remedy is a new external check: run the test, read the file you
skipped, query the graph. New evidence, not another pass.

**Artefact:** one line naming what you did *not* check and why. This is the last
defence against the omission bias the SEI measured, and it is the line reviewers
most often leave out.

## Output

A review document under `docs/` with: the claim, the derived-requirements list
with verdicts, the step-2b analogy rows, the value → consumer table, the test
verdicts, the five failure class rows, the findings table with states, and the
not-checked line. Findings that need work become backlog items with ids.

## When this skill does not apply

- Nothing exists yet. There is no claim to check; use `architecture-decision`.
- You are being asked to approve rather than review. Say which you did.
- The artefact under review is one you produced in this same session. You are the
  wrong reviewer for it; say so and name what an external check would be.
