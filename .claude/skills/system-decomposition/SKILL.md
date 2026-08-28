---
name: system-decomposition
description: Split a system into parts and defend the seams. Places boundaries on what changes together and on team shape rather than on nouns or layer names, forces each part to declare what it hides, checks dependency direction, and names the part that will be repaired downstream. Use when carving a new system into modules, services or layers, when naming a unit whose name no longer matches its jobs, or when a boundary is being crossed and someone must decide whether to move the boundary or stop the crossing. Not for choosing between technologies (use architecture-decision).
---

# Where the seams go, and why they hold

The as-built review of this codebase reached one conclusion about its own
structure worth starting from:

> Not in the ideas, which are good. In the seams.

Five named seams, each small: granularity fixed in one layer and repaired by
chunking in a later one; a lower module defining what "producible" means and
being imported *upward* by an earlier layer's validator; a verification harness
filed under the library, which is not the library; one entry point doing four
jobs with only the first in its name; a boolean where the downstream question
was a quantity. *"Together they are the difference between a system that was
drawn and one that accreted."*

This skill is the procedure for drawing them. Each step emits an artefact,
because a boundary you agreed with and did not write down is not a boundary.

## 0 · Reject the noun list

The default decomposition is the list of nouns in the problem statement:
`User`, `Project`, `Build`, `Library`. It is wrong reliably enough to be worth
a step. Nouns describe what the system *stores*; boundaries have to describe
what the system *changes*.

**Artefact:** the noun list, written down and then set aside. You will check it
again at step 5 — not to use it, but to see what it hid.

## 1 · Group by what changes together

For each candidate part, answer: **when a requirement changes, how many parts
open?** One is the target. Three is a signal that the boundary is drawn across
the grain of change rather than along it.

Take the three or four changes most likely in the next six months — a new field
end to end, a new provider, a new output language, a new tenant rule — and for
each, list the parts that open.

**Artefact:** a change × part matrix. Every row with three or more marks is a
finding with a name.

A warning about the metric you may reach for instead. Cohesion is the intuitive
formalisation of "changes together", and the measured result does not support
using it: Radjenović et al.'s systematic review of 106 studies concluded
*"LCOM is not very successful in finding faults."* Use the change matrix, which
is about the future, not a coupling number, which is about the present.

## 2 · Draw the boundary on the team, and say what it costs

Nagappan et al. (ICSE 2008) measured eight organisational metrics against
post-release failures across 3,404 Windows Vista binaries and got 86.2%
precision and 84.0% recall — beating code churn, complexity, coverage,
dependencies and pre-release defects. Organisational structure was the best
predictor of failure they measured.

So: **count the groups that will own these parts.** If a part will be owned by
two groups, or a group will own parts either side of a boundary, that boundary
is going to be crossed and re-crossed.

**Artefact:** a part → owner mapping, one owner per part. Where you cannot
supply one, write `unowned` — an unowned part is the finding, not a gap in the
document. Where a boundary does not match an ownership boundary, one sentence
saying so and why you are keeping it anyway.

## 3 · Make each part declare what it hides

For every part: **what can change inside it without anything outside changing?**
That sentence is the part's reason to exist. A part that cannot answer it is a
folder.

Be honest about the strength of this rule. Information hiding is measured only
through a proxy: MacCormack et al.'s propagation-cost work recorded Mozilla
falling from 17.35% to 2.78% after its redesign — a real change in structure,
with no downstream defect or delivery outcome measured alongside it. So treat
the hiding sentence as a design discipline that produces a testable claim, not
as a proven predictor of quality.

**Artefact:** one hiding sentence per part, and the public surface it implies —
the functions, types and routes that outsiders may name. Anything not on that
list is internal, and step 4 will catch it when it is not.

## 4 · Check every arrow

For each dependency between parts, ask two questions:

**Direction.** Does it point from the volatile thing to the stable thing, and
from later stages to earlier ones? An upward or backward import is where this
codebase's own graph analysis found its violations: of 5,173 nodes and 12,054
links across 276 files, only six links violated layer direction — and both
places were exactly the seams the review had named independently
(`intake/extraction.py` → `layerb/vocabulary.py`; `layerc/validate.py` →
`builder/file_plan.py`). Six links out of twelve thousand were enough to make
the difference between drawn and accreted, and a mechanical check found them.

(Stable-dependencies as a *principle* — depend in the direction of stability —
is widely repeated and, as far as this skill's sources go, never measured
against outcomes. The direction check is worth running because it is cheap and
mechanical, not because the principle is proven.)

**Necessity.** Is the arrow there because the parts genuinely need each other,
or because a helper landed in the nearest file? A dependency that exists for
one utility function is a copied function waiting to happen.

**Artefact:** the list of arrows, each marked `ok`, `wrong-direction`, or
`incidental`, with the two module names. Any non-`ok` arrow gets a named
resolution: move the boundary, invert the dependency, or accept it with a
reason. Three choices; picking none is not one of them.

## 5 · Find the part that will be repaired downstream

This is the step that catches what steps 1–4 miss, and it is derived from this
system's most instructive seam: granularity was fixed in the build-plan layer
and then repaired by chunking in the build layer. Nothing was wrong at either
end. The decision was simply made where the information was not.

For each part, ask: **does it decide something that a later part will have to
undo, work around, or re-derive?** The signals:

- A part produces a shape and a later part reshapes it.
- A part answers a boolean where a later part needs a quantity — `is_buildable()`
  where the real downstream question was *how much will be invented*.
- A part fixes a size, a granularity or a limit before the thing that knows the
  limit has run.
- A later part imports an earlier part to find out what the earlier part meant.

**Artefact:** for each hit, one line: *"X decides D; Y repairs it; the
information to decide D lives in Y."* Then one of: move the decision to Y, pass
the constraint from Y to X explicitly, or record it as accepted with the reason.

Now return to the noun list from step 0. Anything on it that is not inside a
part is either dead or is the part you missed.

## 6 · Name the parts by their jobs

A name that describes fewer jobs than the unit does is the cheapest possible
lie, and this codebase has one: `run_layer_c` does four jobs and only the first
is in its name.

**Artefact:** for each part, its jobs as a numbered list. If the list has more
than one entry and the name covers one, either rename or split — and say which,
in the same line. A unit whose job list exceeds its name and is left alone
becomes a backlog item with an id, not a note.

## Output

A decomposition document under `docs/` carrying: the change matrix, the
part → owner mapping, one hiding sentence and public surface per part, the
arrow list with verdicts, the downstream-repair lines, and the job lists.
Findings that need work become backlog items with ids. The document is the
deliverable; a conversation about the boundaries is not.

## When this skill does not apply

- One part, one owner, and no second party. Not a decomposition.
- The boundaries exist and are being obeyed. Use architecture-review to check
  that, not this skill to redraw them.
- The question is which technology sits inside a part. That is
  architecture-decision.
