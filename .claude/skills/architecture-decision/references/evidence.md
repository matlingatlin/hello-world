# Evidence behind the decision procedure

Opened when you want the numbers, the sources or the limits behind a step. The
procedure works without reading this; a claim you are about to write into an ADR
does not.

## Why every step ends in an artefact — Fischhoff's pruned fault tree

Six branches for "car won't start", plus a seventh, "all other problems". Delete
three branches and see whether people notice by raising their "other" estimate.

| Condition | Observed "other" | Normative | Recovered |
|---|---|---|---|
| Pruned I | **.140** (from .078 with the full tree) | .468 | **30%** |
| Pruned II | .227 | .611 | 37% |
| Pruned I, attention explicitly directed at what is missing | .217 | .468 | 46% |
| Pruned II, same | .346 | .611 | 57% |
| Experienced mechanics | .215 | .441 | 49% |

Read the columns carefully — this is a table that has been misquoted inside this
repository. **.468 is the normative value: what subjects *should* have answered.
They answered .140.** Moving from .078 to .468 is what a correct subject would
have done and is not what happened. Both attention-direction improvements were
only **marginally significant** (p ≈ .06–.08).

**1 subject of 55** assigned enough to "other". Detection was **uncorrelated
with experience** (τ = .058); professional mechanics were no better than
laypeople.

A second effect from the same experiments: merely *seeing more branches* made the
whole failure mode feel far more likely — full-tree subjects rated starting
failure 20–60× as likely as a flat tyre, pruned-tree subjects 5×.

**The consequence for us:** a reader distributes attention across the branches a
document names. What it does not name is invisible, and pointing at the gap
recovers only about half of it. So an ADR enumerates the option it rejected and
the constraint it could not fill; it does not leave them out as obvious.

Source: Fischhoff, Slovic & Lichtenstein 1977/1978, tech report PTR-1042-77-8.
Full table and caveats: `design-fixation-and-anchoring.md` in the knowledge base.

## Why team shape is a constraint row and not a soft factor

Nagappan et al. (ICSE 2008) measured eight organisational metrics against
post-release failures on **3,404 Windows Vista binaries**: **86.2% precision,
84.0% recall** — beating code churn, complexity, coverage, dependencies and
pre-release bugs, all five code-metric families. Organisational structure was the
best predictor of failure they measured.

If the boundary you are drawing does not match the group boundary that will own
it, you are choosing to pay Conway's tax, and the ADR should say so rather than
let a future reader discover it.

**Direction matters and is routinely reversed in citation:** organisation
*predicts* defects. The **inverse Conway manoeuvre** — reshaping the org to get
the architecture — is widely repeated and, as far as these sources go, **never
measured**. Do not cite it as though it were.

## Why the option that removes the decision is mandatory

The SEI's Mission Thread Workshop technical report (CMU/SEI-2009-TR-012)
classified the risks its workshops surfaced: **57 risks of omission against 25 of
commission**, two raters, **kappa .82**. Two of three architectural risks were
things not there rather than things there wrongly.

The same report found **no relationship between the business goals stated up
front and the risks actually discovered.** A goals list will not find them, and
neither will a quality-attribute checklist.

## Why the procedure is numbered instead of taught

Borowa et al. (arXiv 2111.04362) delivered a knowledge-transfer intervention
about cognitive bias to practising architects and measured **no debiasing
effect**; practitioners were *more* biased than students, attributed to
attachment to systems they had built. The 2025 follow-up (arXiv 2502.04011)
found the same techniques worked when applied **as a procedure to the
architecture in hand**.

Knowing the step and performing the step are different interventions, and only
one of them has been measured to work. Related: a lecture telling people design
fixation exists moved fixation 92.10% → 94.29%, p = .71 — nothing. Demonstrating
a person's *own* fixation moved 92% → 72%, φ = .29.

## Why one pass, then new evidence

Huang et al. (ICLR 2024), intrinsic self-correction with no external signal:
GPT-4 on GSM8K **95.5% → 91.5% → 89.0%** across self-review rounds; GPT-3.5 on
CommonSenseQA 75.8% → 38.1%. With **oracle** labels the same loop gains 8.4
points — the external signal does the work, not the loop.

Their exposed confound is worth checking in our own reviews: a reported
self-refinement gain of 44.0 → 67.0 became, under a properly informative initial
prompt, a **baseline of 81.8 that self-refinement degraded to 75.1**. If a second
pass uses criteria the first pass lacked, put the criteria in the first pass.

## Rigour proportional to reversal cost

Nothing measured supports a fixed level of ceremony. What is measured is that
skills regress on tasks where the base model was already competent (~15% of
tasks in SkillsBench), so running a five-artefact procedure on a one-hour,
one-file decision is a way to make the answer worse. State the reversal cost and
scale to it, in writing.
