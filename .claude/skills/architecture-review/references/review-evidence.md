# Evidence behind the review procedure

Opened when a step asks for it, and before you write any of these numbers into a
review document.

## Why omissions come first

The SEI's Mission Thread Workshop report (CMU/SEI-2009-TR-012) classified the
risks surfaced across its workshops: **57 risks of omission against 25 of
commission**, two independent raters, **kappa .82**. Two of three were things not
there.

The same report found **no relationship between the business goals stated at the
start of a workshop and the risks actually found.** Working down a goals list, a
quality-attribute list or a generic checklist does not surface them. What does
beat undirected review is *differentiated* perspectives — roughly 20–35% more
found, with the gain sitting **between** reviewers rather than inside one.

Fischhoff's pruned fault tree measures the same thing on the reader's side: given
a tree with branches deleted, subjects put **.140** on "everything else" where
the normative answer was **.468**; with attention explicitly directed at what was
missing, .217 — under half the gap, and only marginally significant (p ≈ .06–.08).
**1 of 55** assigned enough. Detection was uncorrelated with experience
(τ = .058). Pointing at a gap recovers about half of it, so a review that says
"consider whether anything is missing" has already failed; step 2's list is the
intervention.

(Note for anyone citing this: **.468 is the normative value, not an observed
one.** The earlier version of `architecture-decision` and ADR-0021 both reported
subjects moving "from .078 to .468", which is the correction they *should* have
made and did not.)

## The boundary on "derive before you look"

Step 2 tells you to derive requirements from the claim before opening a file.
That rule is supported **for finding what is absent** and refuted **as an
anti-anchoring device**. The two halves come from different literatures and get
conflated constantly.

**Supported half.** Once you have read the code, the code sets the agenda — the
SEI ratio above, and Fischhoff's pruned-tree result, both say the enumeration
has to come from the claim's own shape rather than from what is in front of you.

**Refuted half.** Leahy et al. 2020 (JMD 142(10) 101402), n = 185, tested
exactly the belief that thinking of it yourself first protects you:

| Anchor | Fixation |
|---|---|
| A **provided** example | M = 0.24 |
| Your own **self-generated** first concept | **M = 0.32** |

F(1,165) = 4.4, **p < 0.04.** A self-generated first idea anchors *harder*. And
delay does not dissolve it: a 23-minute filled interval did not significantly
reduce conformity (Smith, Ward & Schumacher 1993, Exp 2).

**So the rule splits cleanly:**

| You are | Derive cold first? | Because |
|---|---|---|
| enumerating what must exist, to find omissions | **yes** | the code sets the agenda otherwise |
| producing a design, a replacement or an alternative | **no protection** | your own first sketch is the stronger anchor |

For the second row the countermeasure is the far-domain analogy pass, at
`.claude/skills/architecture-decision/references/far-domain-analogy.md` from the
repo root, which is measured; "be careful not to anchor" is not — see the next
section.

**Limits.** Leahy has **no true no-example control** — it compares two kinds of
anchor, not anchor against none — and its subjects were 17–18-year-old novices.
No published experiment measures design fixation on software architecture at all.
Direction is measured; magnitude on our task is extrapolation.

## Why warnings are not a control

| Intervention | Result |
|---|---|
| "Try not to restrict your ideas; be as different as possible" | conformity .25 → **.33** — numerically worse |
| Warning about the specific bad feature | the warned group was the **most** fixated of three |
| Eight anchoring-warning variants (before/after, generic/specific) | every anchored condition differed from control; **no** warned condition differed from any other |
| Monetary incentive for accuracy | anchor p = .001; anchor × incentive F < 1 |
| A lecture explaining that fixation exists | 94.29% fixated vs 92.10% control, p = .71 |

One counter-example that works: a **specific** "avoid these named elements"
instruction under forced articulation. The difference is specific prohibition
plus written output — which is what a step-2 derived list and a step-2b mapping
table are, and what a caution in prose is not.

## Why one pass, and what to do instead of a second

Borowa et al. (arXiv 2111.04362) taught practising architects about their own
cognitive biases and measured **no debiasing effect**; practitioners were *more*
biased than students, attributed to attachment to systems they had built. The
2025 follow-up (arXiv 2502.04011) found the same techniques worked when applied
**as a procedure to the architecture in hand**. Run the steps; do not recall them.

Huang et al. (ICLR 2024), self-review with no external signal: GPT-4 on GSM8K
**95.5% → 91.5% → 89.0%**; GPT-3.5 on CommonSenseQA 75.8% → **38.1%**. With
oracle labels the same loop *gains* 8.4 points — the signal does the work, not
the loop. There is no measured case of an unaided second pass improving a review.

The external verifier here is the file, the line, the test, the graph. Never a
second opinion from yourself.

## The five failure classes, with their sources

1. **Error handling.** Yuan et al. (OSDI 2014), 198 sampled failures in five
   distributed systems: **92% of catastrophic failures** came from incorrect
   handling of *explicitly signalled* errors, and **58% of those** were catchable
   by simple testing of the handler. Log-and-continue, catch-all and `TODO`
   handlers are findings by inspection.
2. **Authorisation ordering.** Find every place identity is checked and read what
   runs *before* it. This repo's live instance has that exact shape:
   `BuildService.run` replays a build by `{projectId, idempotencyKey}` **before**
   the ownership guard, and the version row has no workspace column to scope on.
   A guard that runs second is not a guard. (Review finding F-03.)
3. **Retry and overload.** Huang et al. (OSDI 2022): retry-induced work sustains
   **over half** of studied metastable failures. WeChat's DAGOR measured request
   **queuing time** as the overload signal that works, ~50% better than CoDel,
   and CPU as the one that does not.
4. **Growth terms.** AWS Kinesis, Nov 2020: per-peer threads grew quadratically
   with the fleet; a small capacity addition crossed an OS thread limit; ~17
   hours down.
5. **Reactivated names.** Knight Capital: a repurposed flag woke an 8-year-old
   dead path on 1 of 8 servers; **$460M in 45 minutes**. Grep for every reader of
   the name and put the result in the finding.

## This repo's own instances — and their provenance

The step-3 drop instances (`validate_plan`'s nine unread rule ids, `checks_passed`
computed and never rendered, `/usage/allowance` with no consumer, five curation
endpoints with no UI), the step-4 test cases (`FakeScope` stricter than
production; the interaction-channel test whose canonical spec has zero
interaction criteria), and F-03 above are all traced to `file:line` in
`docs/as-built/`.

**`docs/as-built/` is not present in the working tree as of 2026-08-28**
(backlog B128), and two of the four findings it carries forward were themselves
taken on another document's word (F-17, F-04, backlog B127). Cite any of them as
`unverified` unless you have just confirmed it against the code, and say so in
the step-6 count.
