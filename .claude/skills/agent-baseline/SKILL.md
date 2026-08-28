---
name: agent-baseline
description: "Use AFTER a spec exists and BEFORE writing an agent's skills — dispatches independent subagents to attempt the target job with no support at all, and records exactly what they get wrong. That observed failure list is the only legitimate content for the agent's procedures; anything not on it is speculation. Run this even when the failures seem obvious, because roughly 15% of tasks measurably get WORSE with a skill added, concentrated exactly where the model was already competent — and without a baseline you cannot tell which way yours pushed. NOT for designing what agents should exist (use agent-shape), NOT for writing the files (use agent-assembly), NOT for testing a finished agent (that is a separate dispatch at the end of assembly)."
---

# Watch it fail first

You cannot observe your own baseline. This procedure delegates the failure.

The reason is not ceremony. SkillsBench measured skills lifting task success from
33.9% to 50.5% overall — **and roughly 15% of tasks regressing**, concentrated
where the base model was already competent. Software engineering was its weakest
domain at +4.5%. Adding a procedure is not free and not reliably positive. The
baseline is how you find out which way yours pushed.

Three of four architecture skills measured elsewhere in this project **did not
discriminate at all**, and one made the answer worse. That is the base rate you
are working against.

## 1 · Write the task the agent will actually face

Realistic, from this repo, with a real artefact expected. Not a toy. If the agent
will review migrations, hand over a real migration. The failure modes you are
hunting only appear under real conditions.

**Artefact:** the task prompt, verbatim, saved with the spec.

## 2 · Dispatch at least two independent runs, with nothing

Two, not one — a single run cannot separate a systematic failure from a bad draw.
Independent and parallel; **they must not see each other's work.** The measured
gap between instances is where the information is, and agents that converse
collapse toward one answer (0 of 62 comparisons significant across 12
interventions).

Give them the task, the repo, and no guidance. Ask for the artefact and a short
rationale — the rationale is where the reasoning that produced the mistake shows.

**Artefact:** N transcripts and N outputs.

## 3 · Record what they got wrong — quoted, not summarised

Go through each output against the spec. For every failure write:

- **what they did**, quoted or at `file:line`
- **what the consequence is** — concretely, not "could cause issues"
- **whether both runs did it** — a failure both made is systematic; one is a draw

Watch particularly for the failures that look like competence:
- something granted by omission rather than by decision
- a boundary written as a sentence
- a step that ends in a consideration rather than an artefact
- a claim asserted rather than checked
- work that was never tested, or tested by whoever produced it

**Artefact:** the failure table. This is the deliverable.

## 4 · Separate what the agent must fix from what it need not

Not every failure is the agent's job. Sort each row:

| Verdict | Meaning |
|---|---|
| **teach** | the agent's procedure must prevent this |
| **wall** | prose will not hold it; it needs a hook or a tool that is absent |
| **out of scope** | real, but a different agent's job — record and route |
| **draw** | one run only, not reproduced; keep it, do not build on it |

**Only `teach` rows become procedure content. Only `wall` rows become mechanisms.**

## 5 · Say what the baseline did *well*

The honest half, and the one that gets skipped. Anything the runs got right
without help is somewhere your procedure can only add noise — that is exactly the
regression zone. Write it down and leave it alone.

**Artefact:** the leave-alone list.

## Handing over

`agent-assembly` builds only from the `teach` and `wall` rows. If a rule you want
to write has no row behind it, it is your opinion, and it goes in the spec's open
questions rather than in the agent.
