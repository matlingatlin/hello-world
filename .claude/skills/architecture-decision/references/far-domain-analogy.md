# The far-domain analogy pass

Opened by `architecture-decision` step 2a, `system-decomposition` step 0b, and
`architecture-review` step 2b. One file so the three cannot drift apart.

## Why this step exists, and why it is not "think outside the box"

This is the largest measured lever available to any of the three procedures.

| Measurement | Result |
|---|---|
| Far-domain **structured** analogy (WordTree), 73 practising professionals | design fixation **52.4% → 26.9%**, p < 0.001 |
| Cross-domain structural analogy, LLM idea generation | diversity **+90–173%**; novel-solution rate **1.6% → 50.4%**; 78% human preference; compute-matched |
| Structured second pass with an external prompt system (Design Heuristics) | similarity **0.43 → 0.28**, p < 0.001, at a cost of ~35% of fluency |

Two adjacent findings say *why the structure is load-bearing*:

- **A vague instruction to "look elsewhere" is not the intervention.** The
  measured gain came from an **explicit relational mapping** — roles named on
  both sides. Without the mapping there is no measured effect to claim.
- **Near-domain examples anchor; far-domain examples feed.** A 43-study
  meta-analysis finds examples *increase* novelty and quality while narrowing
  category variety, and that a single **uncommon** example helps most. So one
  distant domain worked properly beats four neighbouring ones.

And the finding that removes the obvious alternative: **generating your own idea
first is not a defence.** Leahy et al. 2020 (n = 185) measured fixation on a
self-generated first concept at **M = 0.32** against **M = 0.24** for a provided
example, F(1,165) = 4.4, **p < 0.04**. Your own first carve anchors *harder*
than someone else's. A 23-minute filled delay did not dissolve it either.

## Limits — do not overstate these numbers

- The LLM analogy result is **one paper, one domain, not replicated**, and it is
  the strongest positive finding in that literature. Treat direction as measured
  and magnitude as provisional.
- Leahy has **no true no-example control**: it compares two kinds of anchor, not
  anchor against none, and its subjects were 17–18-year-old novices.
- Jansson & Smith 1991, the origin of the fixation numbers, reports **no
  inferential statistics at all** — cells of 6–18. It is a demonstration that
  has since replicated, not a significance result.
- Lab-to-field deflation: Jørgensen & Grimstad measured lab effect sizes
  consistently **larger** than field ones for the same manipulation (30% vs 11%).
  Halve a lab-derived magnitude before you plan around it.
- **No published experiment measures design fixation on software architecture or
  code.** Applying it here is a reasonable extrapolation. Calling it measured on
  our own task is not.

Sources, with per-claim MEASURED/REPEATED marks, live in the knowledge base at
`/home/user/skills-repo/knowledge/notes/design-fixation-and-anchoring.md` and
`llm-idea-generation.md`. Read them there rather than copying numbers forward.

## The four moves

**1 · Strip the technology nouns out of the function.** One sentence saying what
must happen, containing no product, protocol, layer or vendor name.

> Not "should the build queue use Redis or RabbitMQ" but *"work arrives faster
> than it can be served, must not be lost, and someone is waiting on each item."*

**2 · Name a domain that performs that function and is not software.** Two is
enough; one worked properly beats four listed. The test for "far enough" is that
the domain has no engineers in it.

Starting set, for a system that accepts work, transforms it and hands it back —
use them as a prompt, not as an answer, and prefer one you can actually reason
about over one that sounds impressive:

| Domain | It solves | Mechanisms it has that software often omits |
|---|---|---|
| Hospital emergency triage | more arrivals than capacity, unequal urgency | explicit triage category, re-triage on wait, a named person owning each patient, handoff protocol |
| Restaurant kitchen pass | bursty arrivals, hard latency, no losses | expediting as a separate role, the ticket rail as visible queue depth, "86" (declare unavailable and stop accepting) |
| Postal sorting | high volume, addressing errors, delivery guarantee | dead-letter office, return to sender, tracking number as the item's identity, sort-then-batch |
| Air traffic control | overload with catastrophic failure cost | holding stacks, ground stop *upstream* of the constraint, strip handoff, mandated readback |
| Blood banking | perishability, matching, absolute traceability | expiry as a first-class field, cross-match before release, cold-chain break = discard, lot recall |
| Newspaper production | daily hard deadline, quality gate, correction path | copy desk separate from writing, spike (kill without deleting), printed correction as a first-class artefact |
| Container shipping | heterogeneous items, many operators | standard box + manifest, bill of lading, demurrage (a *price* on holding), transhipment |
| Library circulation | shared scarce items, long tail, retrieval | catalogue separate from stock, hold queue, recall, reference vs lending copy |

**3 · Write the relational map.** This is the step that carries the evidence.
For the domain you chose, fill both columns — the mapping is what makes it an
analogy rather than a metaphor:

| Role | In that domain | Here |
|---|---|---|
| The item | | |
| The queue | | |
| The server / operator | | |
| The failure they fear most | | |
| The signal that says "overloaded" | | |
| What they do first when overloaded | | |
| What they refuse to do at all | | |

A row you cannot fill on our side is the finding. That empty cell is usually the
mechanism the domain has and this design does not.

**4 · Carry back exactly one mechanism, and say what happened to it.** Not a
theme — a mechanism, named in that domain's own words, then translated. Each one
ends as an option, a derived requirement, a candidate boundary, or an explicit
`does not transfer, because …`.

## What this step emits

Two or three rows:

| Domain | Mechanism carried back | Became |
|---|---|---|
| kitchen pass | "86 the dish" — declare unavailable upstream and stop accepting | option 4: shed at intake, not at the worker |
| air traffic | ground stop upstream of the constraint | already covered by option 2's backpressure |
| blood bank | expiry as a first-class field | does not transfer: build artefacts have no perishability |

**An empty result is a result, and it is written down.** "Both domains produced
nothing that is not already in the option set" is a legitimate row. A missing
step is not — and in the CoT-diversity study, **~15% of runs silently skipped
the differentiation step and declared the ideas already varied**, so the absence
of this table is the specific thing a reviewer should look for.

## When to skip it

- Reversal cost is one file and one hour. Ceremony proportional to consequence.
- The decision is already recorded and unchanged. Cite the ADR.
- You are checking a claim, not producing an alternative — with one exception:
  `architecture-review` step 2b uses the mapping to hunt for *omissions*, which
  is the one review job it fits.
