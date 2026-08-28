---
name: architecture-review
description: Review an existing design, diff or codebase against what it claims to be, and produce findings that can be acted on or refuted. Searches for the risk of omission first, checks every claim against file and line, distinguishes a computed-and-dropped signal from a missing one, and refuses green evidence from doubles stricter than production. Use when reviewing a design document, a proposed change, a layer of an existing system, or a review someone else wrote. Not for making a decision (use architecture-decision) or for redrawing boundaries (use system-decomposition).
---

# Reviewing what is there against what is claimed

Two measured facts set the shape of this procedure.

**Most architectural risk is absence.** The SEI's Mission Thread Workshop
report (CMU/SEI-2009-TR-012) classified the risks surfaced across its workshops
and found **57 risks of omission against 25 of commission** — two independent
raters, kappa .82. Two out of three were things not there. The same report
found *no relationship* between the business goals stated at the start of a
workshop and the risks actually found, so working down a goals list will not
surface them.

**Reviewing your own work is harder, not easier.** Borowa et al. (arXiv
2111.04362) ran a knowledge-transfer intervention about cognitive bias on
practising architects and measured **no debiasing effect**; practitioners were
*more* biased than students, attributed to attachment to systems they had
built. The 2025 follow-up (arXiv 2502.04011) found the techniques did work when
applied by architects *to their own architecture as a procedure* rather than
taught as knowledge. So: run the steps, do not recall them. That is the whole
reason this is a numbered procedure and not a list of things to bear in mind.

A third fact sets the stopping rule. **Do not review the same thing twice
hoping it improves.** Huang et al. (ICLR 2024) measured intrinsic
self-correction: GPT-4 on GSM8K went 95.5% → 91.5% → 89.0% across
self-review rounds; GPT-3.5 on CommonSenseQA fell 75.8% → 38.1%. Additional
passes without new evidence make results worse. What works is an **external
verifier**. In this repo that means the file, the line, the test, the graph —
never a second opinion from yourself.

## 1 · Fix the claim before looking

Write the thing being reviewed as a claim you can be wrong about. Not "review
the build layer" — *"the build layer produces a running app from a plan, and
reports honestly what it verified."*

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
mark each `present`, `absent`, or `unreachable`. `unreachable` is its own
verdict and this codebase needs it: it has a queue state nothing can enter.

## 3 · Check the outputs for the drop

This system's most repeated defect is not a missing computation. It is an
honest computation dropped before it reaches anyone. From the as-built
analysis: `validate_plan` produces nine rule ids and returns them to nothing;
`checks_passed` is computed, typed, transmitted, never rendered;
`/usage/allowance` has no consumer; five curation endpoints have no UI.

So for every value the claim says the system produces, **trace it to a
consumer**, not to a return statement.

**Artefact:** value → consumer, or value → `no consumer`. A `no consumer` row
is a finding with a proposed destination, not an observation. The as-built
document's conclusion is worth carrying: *a rebuild that only surfaced what is
already computed would deliver most of the claimed differentiator without
inventing anything.*

## 4 · Distrust green

A passing suite is evidence only if the doubles are no stricter than
production. This codebase has two confirmed cases of tests passing for the
wrong reason: a fake scope object enforced more than the real one, and an
interaction-channel test whose canonical spec contained zero interaction
criteria, so it asserted nothing.

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
`vacuous`, or `unrun`.

## 5 · Order the checks by what has actually killed systems

Not a quality checklist. Five failure classes with measured incidence, in
order:

1. **Error handling.** Yuan et al. (OSDI 2014): 92% of catastrophic failures in
   five distributed systems came from *incorrect handling of explicitly
   signalled errors*, and 58% of those were catchable by simple testing of the
   handler. Read every catch block in scope. Log-and-continue, catch-all and
   `TODO` handlers are findings by inspection.
2. **Authorisation ordering.** Find every place where identity is checked, and
   check *what runs before it*. This repo's live breach is exactly that shape:
   `BuildService.run` replays a build by `{projectId, idempotencyKey}` **before**
   the ownership guard, and the version row has no workspace column to scope on.
   A guard that runs second is not a guard.
3. **Retry and overload.** Huang et al. (OSDI 2022): retry-induced work is the
   sustaining effect in over half of studied metastable failures. Find the
   retries, the backoff, the cap, and the signal used to shed load — WeChat's
   DAGOR measured request *queuing time* as the signal that works, ~50% better
   than CoDel, and CPU as the one that does not.
4. **Growth terms.** Anything counted per-peer, per-tenant, per-file or
   per-fleet-member. AWS Kinesis, Nov 2020: per-peer threads grew quadratically
   with the fleet, a small capacity addition crossed an OS thread limit, ~17
   hours down.
5. **Reactivated names.** Any flag, column, route or constant being reused.
   Knight Capital: a repurposed flag woke an 8-year-old dead path on 1 of 8
   servers; $460M in 45 minutes. Grep for every reader of the name and put the
   result in the finding.

**Artefact:** each class gets a row, even when the row says `none in scope`.
An absent row and a clean row are indistinguishable to the next reader, and
absence of a result is not a negative result.

## 6 · Write findings that can be refuted

A finding that cannot be checked cannot be fixed or dismissed, so it stays open
forever. Each one carries:

- **Where** — `file:line`, or the doc heading. Never "in the build layer".
- **What is true** — the observed fact, stated so it can be shown false.
- **Why it matters** — the concrete failure, with inputs and the wrong result.
  Not "could cause issues".
- **State** — `live`, `fixed`, `false positive`, or `unverified`. `unverified`
  is honest and required when you took it on another document's word.
- **Cost to fix** — so the reader can triage without re-deriving it.

**Artefact:** the findings table. And a count: how many findings you verified
yourself against code, versus carried over from another document. Carrying four
findings from a prior review and verifying one is a fine outcome; reporting
four verified is not.

## 7 · Stop

You have run the procedure once. Do not run it again on the same evidence —
step 0's third fact says that makes it worse. If you are unsatisfied, the
remedy is a new external check: run the test, read the file you skipped, query
the graph. New evidence, not another pass.

**Artefact:** one line naming what you did *not* check and why. This is the
last defence against the omission bias the SEI measured, and it is the line
reviewers most often leave out.

## Output

A review document under `docs/` with: the claim, the derived-requirements list
with verdicts, the value → consumer table, the test verdicts, the five failure
class rows, the findings table with states, and the not-checked line. Findings
that need work become backlog items with ids.

## When this skill does not apply

- Nothing exists yet. There is no claim to check; use architecture-decision.
- You are being asked to approve rather than review. Say which you did.
