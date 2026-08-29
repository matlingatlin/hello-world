<!-- TEMPLATE — a research commission. Written by whoever wants the research
     (step 0 triage, agent-shape, or a human). NOT written by the researcher:
     an agent that writes its own commission has no scope. Save as
     docs/research/commissions/<id>.md — the filename IS the id, and the draft,
     the verdict document and the note all take the same id. -->

# Commission — <id>

**Commissioned by:** <who, and on what date>
**Sweep:** <first | second, narrower — see the re-commission section below>

## The candidate sentence

> <ONE sentence. What the proposed agent does, and the artefact it produces.
>  "It reviews a database migration and produces a findings list at file:line
>  with a verdict." If you cannot name the artefact, the job is not defined yet
>  and the research will be scoped to a guess.>

## What the later stage will have to decide from this

<A few lines. Not the questions — those are the researcher's step 2 — but what
 the evidence is FOR. The researcher reads this to tell a question that serves a
 decision from a question that is merely interesting.>

## Known out of scope

<Anything the commissioner already knows is not wanted. Optional, and the
 researcher will produce its own fuller list; a row here saves a round trip.>

## Re-commission only — fill this in on a second, narrower sweep

- **First sweep:** <id of the draft it produced>
- **What it already covered:** <so the second sweep does not re-cover it>
- **Why it was too wide:** <the specific finding from the later stage>
- **The narrower question:** <one line>

A second sweep is narrower than the first. One is the agreed number
(docs/decomposition-agent-pipeline.md, section 5). A wider sweep is a new
commission and needs whoever owns the pipeline to say so.

## What is NOT here, deliberately

No target number of sources, claims or pages. Quotas act as ceilings: told
"5-7", people produced 7; told "at least 20", 21; told nothing, 29. The
researcher's stopping condition is its question list, not a count.
