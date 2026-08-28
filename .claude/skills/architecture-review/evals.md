# evals — architecture-review

> **Revision note, 2026-08-28.** The skill was repaired after these cases were
> written (step 2 now carries its boundary — derive-cold is for omissions, not
> for generating alternatives; new step **2b**, the far-domain omission pass;
> evidence moved to `references/review-evidence.md`). **Step numbers 1–7 and
> every artefact named below are unchanged**, so R1–R7 still run as written —
> R2 in particular still tests the derive-then-look ordering, which is the half
> of the rule the evidence supports. Step 2b and the boundary itself have **no
> case in this set** — the tester writes them, and the boundary needs a case
> where deriving cold is the *wrong* move. R2 and R5 name inputs in
> `docs/as-built/`, absent from the working tree (B128): reconstruct from code
> or record `unrunnable`, not fail. See `docs/architect-repair-tester-brief.md`.

**Status: written, not run.** Authored by the session that wrote the skill.
An independent tester must run these and fill the results table.

This set has an unusual hazard. The ground truth lives in `docs/as-built/` and
in the six review documents, which the agent can read. A case therefore
measures the skill only if passing requires **the procedure's artefact**, not
the answer. Every required artefact below is a table, a count, or a verdict
that cannot be produced by quoting a document.

---

## R1 · The guard that runs second

**Input:** `BuildService.run`, with the claim *"a build can only be replayed by
its owner."*

**Required artefact:** step 5 row 2 filled — the ordering finding, at
`file:line`, with the inputs that produce the wrong result, and the note that
`BuildVersion` has **no `workspace_id` column to scope on**. Ground truth:
review finding F-03, verified live three ways as of 2026-08-26.

**Baseline failure:** confirms an ownership guard exists. It does exist. It
runs second.

## R2 · Omissions before code

**Input:** `docs/UX-FLOW.md`'s claim that Level 1 *"moves shaping to AFTER the
build… so Level 1 does not read as the lesser path."*

**Required artefact:** the step-2 derived list, written from the claim, with
`/live` marked **absent**. Ground truth: `App.tsx` lists five placeholder
routes, and `/live` — "Refine" — is Level 1's entire landing surface.

**Baseline failure:** reads `App.tsx`, sees five placeholders, reports five
placeholders, and never connects `/live` to the claim. The as-built review
itself made a weaker version of this error, concluding the gap sat "at the two
ends of the user's path" when the whole post-reveal half is unbuilt. **This is
the highest-value case in the set**: the procedure's order — derive, then look
— is the only thing that produces it.

## R3 · The vacuous test

**Input:** `test_interaction_channel` and the canonical spec it runs against.

**Required artefact:** the verdict `vacuous`, and the fix — assert the count of
interaction criteria in the fixture before asserting on them. Ground truth: the
canonical spec contains **zero** interaction criteria, so the test asserts over
an empty set and passes.

## R4 · The double stricter than production

**Input:** `FakeScope` and the workspace-scoping tests.

**Required artefact:** the verdict `verifies the double`, with the specific
behaviour the fake enforces and production does not. Ground truth: confirmed
case in `docs/as-built/`.

## R5 · One green run is not a baseline

**Input:** `00-INDEX.md`'s recorded verified baseline, plus consultant finding
B105.

**Required artefact:** the `unrun`/observation verdict — the baseline restated
as *one observation* — and the note that B105 records `design.test.tsx` failing
two different tests on two consecutive runs with the cause never found. A pass
does not require re-running anything; it requires the claim to be downgraded in
writing.

## R6 · Negative control — a finding that is not one

**Input:** review finding F-16, *"suspicious package names `httpx2` and
`httpcore2`."*

**Required artefact:** state `false positive`, with the reason — genuine
Pydantic-org packages by httpx's own author — **and** the half that survives:
no hashes in the lockfile. Ground truth confirmed.

A review skill that confirms every finding handed to it is a rubber stamp.
**A pass here refutes and salvages in the same finding**, which is the harder
of the two.

## R7 · The line most often left out

**Input:** any of the above, run to completion.

**Required artefact:** the step-7 line naming what was *not* checked and why,
and the step-6 count separating findings verified against code from findings
carried from another document. Ground truth for the count: of the 35 findings
in the two root reviews, four have been checked and **two of those four were
taken on another document's word.** An output reporting four verified is a
fail.

---

## Results

| Case | Tester | Date | Verdict | Note |
|---|---|---|---|---|
| R1 | — | — | unrun | |
| R2 | — | — | unrun | |
| R3 | — | — | unrun | |
| R4 | — | — | unrun | |
| R5 | — | — | unrun | |
| R6 | — | — | unrun | |
| R7 | — | — | unrun | |

**Shipping bar:** ≥5 of 7, **R2 and R6 among them.** R2 tests the ordering that
is the skill's central claim; R6 tests that it can say no.
