# Evidence behind the decomposition procedure

Opened when a step asks for it, and before any of these numbers goes into a
decomposition document.

## The five seams this procedure was built from

The as-built review of this codebase concluded: *"Not in the ideas, which are
good. In the seams."* Five, each small:

1. Granularity fixed in one layer and repaired by chunking in a later one.
2. A lower module defining what "producible" means, imported *upward* by an
   earlier layer's validator (`layerc/validate.py` → `builder/file_plan.py`).
3. A verification harness filed under the library, which is not the library
   (681 lines of pglite harness).
4. One entry point doing four jobs with only the first in its name (`run_layer_c`).
5. A boolean where the downstream question was a quantity (`is_buildable()`
   where the real question was *how much will be invented*).

*"Together they are the difference between a system that was drawn and one that
accreted."*

**Provenance:** these trace to `file:line` in `docs/as-built/`, which is **not
present in the working tree as of 2026-08-28** (backlog B128). Treat them as
priors to re-confirm, not as ground truth to recite. Two of the four findings
that document carries forward were themselves taken on another document's word
(B127).

## Why the boundary goes on team shape

Nagappan et al. (ICSE 2008) measured eight organisational metrics against
post-release failures across **3,404 Windows Vista binaries**: **86.2% precision,
84.0% recall**, beating code churn, complexity, coverage, dependencies and
pre-release defects. Organisational structure was the best predictor of failure
they measured.

Direction of the evidence: organisation *predicts* defects. The **inverse Conway
manoeuvre** — reshaping the org to obtain the architecture — is widely repeated
and **never measured** in these sources. Do not cite it as though it were.

## Why the change matrix instead of a coupling metric

Cohesion is the intuitive formalisation of "changes together" and the measurement
does not support using it: Radjenović et al.'s systematic review of **106
studies** concluded *"LCOM is not very successful in finding faults."*

The change matrix is about the future; a coupling number is about the present.

## How strong the information-hiding rule actually is

Information hiding is measured here only through a proxy: MacCormack et al.'s
propagation-cost work recorded Mozilla falling from **17.35% to 2.78%** after its
redesign — a real change in structure, with **no downstream defect or delivery
outcome measured alongside it**.

Treat the hiding sentence as a design discipline that produces a testable claim,
not as a proven predictor of quality.

## Why the arrow check is worth running anyway

Stable-dependencies as a *principle* is widely repeated and, as far as these
sources go, never measured against outcomes. What is measured is that the check
is cheap and finds things: of **5,173 nodes and 12,054 links across 276 files**,
**six** links violated layer direction — and both sites were exactly the seams an
independent review had named. Six links in twelve thousand were the difference
between drawn and accreted.

That count came from `docs/as-built/graph/graph.json`, which is **absent from the
working tree** (B128). Without it the check is a targeted grep for imports that
cross a layer boundary in the wrong direction, and the result is marked
`unverified against the graph`.

## Why your own first carve is not a safe starting point

Step 0 sets the noun list aside. The reason it does not simply say "think of your
own decomposition instead" is that a self-generated first concept is the
*stronger* anchor: fixation **M = 0.32** on a self-generated first concept versus
**M = 0.24** on a provided example — F(1,165) = 4.4, **p < 0.04**, n = 185
(Leahy et al. 2020). A 23-minute filled delay did not dissolve it.

Warnings do not help either: eight anchoring-warning variants, differing in
content and timing, were **all** indistinguishable from no warning, and "be as
different as possible" moved conformity .25 → .33, numerically worse.

What is measured to work is a structured far-domain mapping, which is why step 0b
exists and why it demands a written table rather than an intention. See
`.claude/skills/architecture-decision/references/far-domain-analogy.md` (path
given from the repo root, not from this file), including its limits
— one unreplicated LLM study, no true no-example control in Leahy, and no
published experiment on software architecture at all.
