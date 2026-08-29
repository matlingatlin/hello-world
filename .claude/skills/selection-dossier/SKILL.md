---
name: selection-dossier
description: "Use when ruled candidates have to be put in front of a human who will choose between them — assembling the dossier they decide from, on separate axes, with the conventional-pick drift and the unlisted options made visible. Produces a decision document; it never ranks, scores or selects, because that step is measured to be where the chain breaks. NOT for generating candidates (blank-slate-positions, comparable-products-sweep), NOT for ruling what a candidate already is (proposal-adjudication), NOT for judging whether an existing capability should survive (capability-retirement-audit), and NOT for recording the decision once made (design-decision-record)."
---

# The dossier a human decides from

Generation is not the bottleneck. Selection is.

Rietzschel et al. measured groups that generated more ideas and more original
ideas, and found they **did not select better ones — selection was not
significantly better than chance.** People pick the conventional: the
correlation between "picking the best" and "picking the original" was
**−0.40**. Telling them to select for both originality and feasibility
**improved selection not at all.**

That is the single most actionable finding in this literature, and it is why
this skill exists and why it is shaped the way it is. Every rule below is a
consequence of a measured failure, not a preference about document layout.

**You do not choose.** Model-versus-expert agreement on idea quality is
**22–40%** where expert-expert is 60%, and the disagreement runs in *opposite
directions* rather than being noisy. A dossier that arrives with a
recommendation has substituted the weakest judge in the room for the decision it
was assembled to support. Open
`/home/user/skills-repo/knowledge/notes/ideation-and-idea-selection.md` and
`.../llm-idea-generation.md` before any figure here goes into a document; the
numbers live there, not in your memory of this file.

## 0 · Admit only what is decidable

Input is a ruling table from `proposal-adjudication`. Take only `new` and
`partly`.

- `already-built` — the decision was taken; it is not on the table.
- `already-proposed` — it is proposal `E-7`; the decision belongs to whatever
  decides proposals, not to this dossier. Say which id.
- `too vague to rule` — goes back to the generator. A candidate that cannot be
  made concrete enough to be wrong cannot be chosen between.

A candidate set arriving with no ruling table is not admitted. Rule it first.

**Artefact:** admitted list, and the excluded list with the reason and id beside
each. The excluded list is part of the dossier, not scaffolding you discard —
step 4 depends on the reader being able to see it.

## 1 · Two axes, never one number

Originality and feasibility are **negatively correlated, r = −0.71**. A single
"quality" score therefore destroys the information the reader needs: it maps the
two things that trade off onto one line and hides which way each candidate
leans.

So: two columns, each with its evidence, and **no total column, no weighting, no
stars.** If someone asks for a single number, the answer is that the number
would be incoherent, and here is the pair.

| Column | What goes in it | What does not |
|---|---|---|
| Feasibility | what it would take, in named parts and named unknowns | a 1–5 score |
| Originality | the nearest named neighbour and the specific delta | a novelty rating |

**Novelty ratings reward vagueness** — measured: the worst system in a 2026
study scored **highest** on novelty (3.73/4) and last on quality (1.00/4),
because a topic-agnostic proposal has no precise prior art to collide with. A
named neighbour cannot be gamed that way; a rating can.

**Artefact:** the two-axis table, one row per admitted candidate.

## 2 · Mark the drift, do not correct it

For each candidate, one mark: `conventional` or `departs`, with the sentence
that makes it one or the other.

This is not a score and it does not order the table. It exists because the
measured bias runs one way — toward the conventional — and the reader cannot
see their own drift without the column. A dossier where every admitted candidate
is marked `conventional` is itself the finding, and it goes in the summary line.

Do **not** compensate by promoting original candidates. Instructing selectors to
weigh originality was measured and it changed nothing; the fix is visibility,
not a thumb on the scale.

**Artefact:** the marked column, plus one line: `n of m depart from the
conventional`.

## 3 · No forced comparison

Do not build a pairwise table, a tournament, or any structure that requires a
winner per pair. **Forcing ties to be broken moved the same model's win rate
from 27.2% to 49.1%** — the ranking was manufactured by the format, not measured
by it.

Where two candidates genuinely conflict — they cannot both be done, or one
forecloses the other — say so as a **named dependency**, not as a comparison:
*"C-4 forecloses C-9; doing C-9 first costs the intake rewrite twice."* Conflicts
are structure the reader needs. Preferences are not yours to state.

**Artefact:** the conflict list, or the explicit sentence that there are none.

## 4 · Name what is not on the list

This is the step the dossier is most likely to skip and least able to afford.

Fischhoff pruned three branches from a fault tree and asked people to allocate
probability to "all other problems." They gave it **.140 where the normative
answer was .468 — about 30% of what was missing. One subject of 55** assigned
enough. Experience did not help: **τ = .058**, uncorrelated with detection.
Directing attention explicitly at what might be missing recovered **46–57%** —
better, and still under half, and only marginally significant.

**A shortlist is a pruned fault tree.** The reader will distribute their
attention across the options you named and will not recover the rest, and
seeing more branches also made the whole area feel far more likely — pruned-tree
subjects rated the failure 5× as likely, full-tree subjects 20–60×. The
presentation moves the reader's sense of the size of the problem, not just their
choice within it.

Three entries are therefore mandatory, and each has to be substantive:

1. **What was excluded and why** — the step 0 list, in the dossier, not in a
   footnote.
2. **What was never generated** — the briefs the prospector ran under, and the
   directions no brief covered. If the framing distribution came back
   `supply over-concentrated`, that sentence goes here verbatim.
3. **Do none of these** — as a real row with its own consequence, not a
   courtesy. What happens if nothing on this list is done, and by when does that
   change.

**Artefact:** the three sections. An empty one is a defect, not a clean result.

## 5 · State what you could not settle, and hand it over

Some candidates turn on a question no `file:line` answers — who the user is,
what it may cost, whether the risk is acceptable. Do not resolve those by
inference, and do not let the inference hide inside a feasibility cell.

**Artefact:** open questions, each phrased as a question, each with a named
person or document that could answer it. Then the closing line, which is always
the same shape: **the choice is the reader's, the dossier is the input, and
nothing here is a recommendation.**

## Output

One document under `docs/`, carrying: the admitted and excluded lists with
reasons, the two-axis table, the drift column and its count, the conflict list,
the three what-is-not-here sections, and the open questions. Findings that need
work become backlog items with ids.

A dossier that ends in a ranked list is not this skill's output, whatever it is
titled.

## When this skill does not apply

- **There is one candidate.** Nothing to put beside it. Rule it and decide.
- **The candidates have not been ruled.** Run `proposal-adjudication` first —
  a dossier that mixes `new` with `already-built` invites a decision that has
  already been taken.
- **Someone wants a recommendation.** That is a different request, and it is not
  one this skill can serve: the agreement figures above say the recommendation
  would be worse than the reader's own reading of the same table.
- **The decision is already made** and needs writing down. That is
  `design-decision-record`.
