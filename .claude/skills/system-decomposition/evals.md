# evals — system-decomposition

**Status: written, not run.** Authored by the session that wrote the skill.
An independent tester must run these and fill the results table.

Ground truth for every case is `docs/as-built/`, where each claim traces to
`file:line` or a test name. The five seams named there were found by an
analysis that did not have this skill, so they are honest labels — but for the
same reason a tester must confirm the skill *finds* them rather than *recites*
them. **A case is a fail if the output names the seam without producing the
step's artefact**, because reciting a known answer is what this eval set is
most at risk of measuring.

---

## S1 · The decision made where the information is not

**Input:** the Layer C and Layer E summaries in `docs/as-built/`, with the
question "are these two layers correctly separated?"

**Required artefact:** the step-5 line — *"Layer C decides granularity; Layer E
repairs it by chunking; the information to decide granularity lives in E"* —
plus one of the three named resolutions. Ground truth confirmed.

**Baseline failure:** concludes the layers are separated because each has a
clear job. That is true and misses it.

## S2 · The upward import

**Input:** "`layerc/validate.py` needs to know which files the builder can
produce."

**Baseline failure:** imports `builder/file_plan.py` — which is what the
codebase actually did.

**Required artefact:** the arrow, marked `wrong-direction`, with both module
names, and a named resolution. Ground truth: this is one of only 6
layer-direction violations in 12,054 links, confirmed mechanically against
`docs/as-built/graph/graph.json`.

## S3 · The unit whose name is smaller than its job

**Input:** `run_layer_c` and what it does.

**Required artefact:** the numbered job list (four entries), and an explicit
`rename` or `split` verdict with a backlog id. Ground truth: four jobs, one in
the name.

**Baseline failure:** describes the function accurately and stops. Accurate
description without the verdict is a fail — this is the case that separates
documentation from decomposition.

## S4 · The part filed under the wrong parent

**Input:** the contents of `library/`, with the question "is the library one
part?"

**Required artefact:** `library/verification/` named, its hiding sentence shown
to be unwritable in library terms, and a move proposed. Ground truth: 681 lines
of pglite harness under the library, which the as-built analysis lists as safe
to move.

## S5 · Negative control — a boundary that is already right

**Input:** the sandbox provider interface and its conformance suite.

**Required artefact:** `ok` on the arrows and a hiding sentence that holds —
*a provider's implementation can change without callers changing* — and **no
proposed change.** Ground truth: the provider conformance suite exists and
names the original bug it fences
(`test_every_provider_passes_the_callers_env_to_the_app`).

A skill that finds a finding here is producing noise. **A pass is silence with
a reason.** Without this case the eval set cannot distinguish a skill that
finds real seams from one that finds seams everywhere.

## S6 · The change matrix earns its place

**Input:** "we want to support a second output language."

**Required artefact:** the change × part matrix, with every row of three or
more marks named as a finding. This case exists to check that the matrix is
*produced*, not that its conclusion is novel — the skill's claim is that the
matrix surfaces the parts, and an output that reasons to the same answer
without the matrix has not tested the claim.

---

## Results

| Case | Tester | Date | Verdict | Note |
|---|---|---|---|---|
| S1 | — | — | unrun | |
| S2 | — | — | unrun | |
| S3 | — | — | unrun | |
| S4 | — | — | unrun | |
| S5 | — | — | unrun | |
| S6 | — | — | unrun | |

**Shipping bar:** ≥4 of 6 **and S5 must pass.** A false-positive rate that the
set cannot measure is worse than a lower score.
