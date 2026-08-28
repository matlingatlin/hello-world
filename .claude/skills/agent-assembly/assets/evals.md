<!-- TEMPLATE — evals for an AGENT. Written by someone who did not author it. -->

# evals — <agent>

**Author:** <tester>  **Not** the author of the agent.
**Status:** <written | run>

## Why these cases

<What the suite is for, and the discrimination bar: a case earns its place only if
an unaided agent plausibly gets it wrong. Cases the baseline already passes cannot
measure the agent — and roughly 15% of tasks measurably regress under added
guidance, concentrated exactly where the model was already competent.>

## Cases

### <N> · <name> — <normal | negative control | containment | trigger>
**Input:** <…>
**An unaided agent typically:** <the observed baseline failure, or "succeeds" for a
negative control>
**Pass requires:** <the artefact, specifically. Discussing the right thing without
emitting the artefact is a fail.>
**Ground truth:** <where it is checkable>

<At minimum the suite carries: several NORMAL cases; one NEGATIVE CONTROL where the
right answer is to produce nothing — without it the suite cannot separate a finding
from noise; at least one CONTAINMENT case asking whether the agent can exceed its
remit, which no skill-authoring practice covers because a skill has no remit; and a
TRIGGER check that work belonging to a neighbour is routed away.>

## Results

| # | Verdict | Verified how | Note |
|---|---|---|---|

## What this suite is blind to

<Required. A green number alone says nothing about coverage. Also state how many
results were verified against the artefact versus taken on a report's word.>

## Bar

<Pass threshold, and which cases are mandatory. Below the bar the agent is CUT,
not defended.>
