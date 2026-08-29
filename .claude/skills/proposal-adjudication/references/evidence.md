# Where each number comes from — open the note, do not quote from memory

This file holds **no numbers**. It holds the address of each one.

That is deliberate, and it is this repo's standing rule: *knowledge is queried
from `/home/user/skills-repo/knowledge/notes/`, not copied. Copies drift; the
base does not.* A reference file that restated the effect sizes would be a second
place for them to rot, and the failure this whole pipeline is shaped around —
B130, nothing verifies a note against its own sources — starts with a copy
nobody re-checked.

## The rule

Before a number, an effect size or a sample size goes into any document you
write: **open the note, read the row, and carry across the verdict with it.**
Every note marks each claim `MEASURED` or `REPEATED`. A `REPEATED` claim may be
cited only as "widely repeated, traced to no study" — never as a finding.

We have measured what happens without this. In outside writing: a finding
attributed to Diehl & Stroebe that is absent from their paper, and Mullen's
conclusion reversed. Both survived because the writer quoted a summary rather
than the source.

## The map

| Claim as it appears in these skills | Note | Grep anchor |
|---|---|---|
| Novelty scored with and without retrieval, and the inflation ratio | `llm-idea-generation.md` | `6.14` |
| Vague proposals score highest on novelty, last on quality | `llm-idea-generation.md` | `3.73` |
| Framing distribution — bridge and synthesise, human versus LLM rates | `llm-idea-generation.md` | `11,683` |
| Normalised entropy, human versus LLM | `llm-idea-generation.md` | `0.926` |
| Model-versus-expert agreement on idea quality, and expert-expert baseline | `llm-idea-generation.md` | `22–40` |
| Similarity does not detect restatement — human questions more similar, less narrow | `llm-idea-generation.md` | `similar` |
| Runs that silently skip the differentiation step | `design-fixation-and-anchoring.md` | `skipped` |
| Selection is the broken step; correlation between "best" and "original" | `ideation-and-idea-selection.md` | `−0.40` |
| Originality and feasibility are negatively correlated — one score is incoherent | `ideation-and-idea-selection.md` | `0.71` |
| Refactoring and post-release defects, Windows 7 version history | `requirements-discovery.md` | `7%` |
| The 1:6.5:15:60–100 cost-of-defect chart — the study does not exist | `requirements-discovery.md` | `Systems Sciences` |
| "60–80% of rewrites fail" and the "312 attempts" figure | `requirements-discovery.md` | `312 attempts` |
| Information hiding measured only through propagation cost | `architecture-evidence.md` | `propagation cost` |
| Organisational structure as the best predictor of post-release failure | `architecture-evidence.md` | `86.2%` |

`/home/user/skills-repo/knowledge/notes/INDEX.md` lists every note. If a claim
you need is not in the table above, it is not licensed by this pipeline: find the
source, land the note in the same turn you verify it, then add the row.

## What a missing note means

If the notes directory is unreachable, the numbers are unavailable — not
approximate. Write the argument without them and say in the artefact which claim
you had to drop. An effect size recalled from context is exactly the failure mode
above, one step earlier.
