# The candidate-to-shipped-agent pipeline — where the seams go

Produced by running `system-decomposition` on the pipeline itself, 2026-08-29.
The deliverable is this document; the conversation was not it.

## 0 · The noun list, set aside

Candidate · Research · Baseline · Spec · Agent · Skill · Validator · Test ·
Registry. Nouns describe what the pipeline *stores*. Kept for step 5.

## 0b · A division of labour borrowed from a far domain

Function, no software nouns: *turn a suspicion that a specialist is needed into a
working specialist whose competence has been demonstrated by someone other than
the one who trained them.*

Organisation that performs it: **hospital credentialing and privileging.**

| Their division | Our part |
|---|---|
| Needs assessment | step 1, triage — **have** |
| **Primary source verification** — credentials checked with the issuing body, never the applicant's word | **NOTHING** |
| Delineation of privileges — an enumerated list of permitted procedures | `tools:` + hook — partial; we grant, we do not enumerate |
| **Proctoring (FPPE)** — a defined period of observed real cases before independent practice | **NOTHING** |
| Peer review, same specialty, not the supervisor | step 7, independent tester — **have** |
| **Ongoing evaluation (OPPE)** — periodic re-review while active | **NOTHING** |
| **Suspension / withdrawal of privileges** | **NOTHING** |
| The credentials file | spec + evals — **have** |

Four empty rows. They are the point of the step; the rows that mapped neatly
taught nothing.

**The first is the most serious.** A hospital never verifies against the
applicant's own account. Our `domain-researcher` will write a knowledge note and
**nothing checks that note against its cited sources.** We have already measured
this exact failure in other people's writing — an article that attributed to
Diehl & Stroebe a finding absent from their paper, and reversed Mullen's
conclusion. Nothing in this pipeline catches it in *our* notes. → **B130.**

The second and third are the same shape: we go from "evals passed" to "live" with
no observed period, and nothing re-reviews an agent once it is running — although
we have a measured case of a harness assumption going stale (Sonnet 4.5's
"context anxiety" mitigation, unnecessary by Opus 4.5). → **B131, B132.**

The fourth is the governance gap already recorded against
`agent-skill-creator`. → **B133.**

## 1 · Change matrix — the row that decided the build

| Likely change | Parts that open |
|---|---|
| A new domain gets an agent | shape · baseline · assembly |
| **The construction rules change** (Anthropic updates the spec) | **the validator alone — IF the rules live only there. Four-plus parts if each skill restates them** |
| A new component type appears (`memory:`, say) | shape · assembly · validator |
| We learn a new failure mode | the knowledge note alone |

Row two is the seam. **The validator is therefore the single home of the
construction rules, and the skills describe the procedure and point at it rather
than restating the numbers.** Prose that repeats a rule is a second place for it
to rot.

## 3 · What each part hides

| Part | What can change inside it without anything outside changing |
|---|---|
| `domain-researcher` | which sources, which search strategy, how the sweep is split |
| `agent-shape` | how the roster is decided, provided the spec's shape holds |
| `agent-baseline` | whether failures come from dispatched runs or recorded real ones |
| `agent-assembly` | file layout and authoring order |
| **validator** | **every rule, threshold and limit** — that is its whole reason to exist |
| tester | scenario design, provided the suite still carries a negative control and a containment case |

## 4 · Arrows

All forward: research → shape → baseline → assembly → validate → test. No part
imports a later one. **Marked `unverified against the graph`** — `docs/as-built/graph/`
is not present in this repo (B128); this is a reading of the call sites, not a
mechanical check.

One arrow is deliberate and worth naming: **assembly points at the validator, not
the reverse.** If the validator ever needed to know what assembly intended, the
rules would have leaked back out of their home.

## 5 · The part repaired downstream

**`domain-researcher` decides what is worth knowing before anyone knows what the
agent will do.** It sweeps "database"; `agent-shape` then finds the agent only
reviews migrations. The sweep was too wide, and the information that would have
scoped it lives in a step that runs later.

Resolution, chosen: the research is scoped by the **candidate sentence** from step
0, and `agent-shape` may commission one narrower second sweep. Recorded rather
than designed away, because the alternative — running shape first — would have
shape deciding a roster with no domain evidence in hand.

Returning to the noun list: **Registry** appears nowhere in any part. That is
B133, and it is the same hole the borrowed division found from the other side.

## 6 · Job lists

| Part | Jobs | Verdict |
|---|---|---|
| `domain-researcher` | 1 sweep · 2 sort · 3 write the note with per-claim verdicts | name covers it |
| `agent-shape` | 1 triage · 2 diet · 3 split · 4 tool surface · 5 boundary · 6 **component manifest** | **six jobs, name covers one.** Not split: they are one decision taken together, and splitting would put the manifest where the diet is unknown. Accepted, recorded here |
| `agent-baseline` | 1 obtain failures · 2 classify teach/wall/scope/draw | name covers it |
| `agent-assembly` | 1 place · 2 author · 3 propose the wall · 4 delegate verification · 5 delegate the test | five jobs, one name — **B134** |
| validator | 1 check | exact |

## Backlog raised

- **B130** — nothing verifies a knowledge note against its own cited sources
- **B131** — no observed period between "evals passed" and "live"
- **B132** — nothing re-reviews a live agent, though assumptions are measured to go stale
- **B133** — no registry: no owner, no version, no withdrawal mechanism
- **B134** — `agent-assembly` does five jobs and its name covers one
