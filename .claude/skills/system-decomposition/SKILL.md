---
name: system-decomposition
description: Split a system into parts and defend the seams. Borrows one decomposition from a far domain before committing to its own, places boundaries on what changes together and on team shape rather than on nouns or layer names, forces each part to declare what it hides, checks dependency direction, and names the part that will be repaired downstream. Use when carving a new system into modules, services or layers, when naming a unit whose name no longer matches its jobs, or when a boundary is being crossed and someone must decide whether to move the boundary or stop the crossing. Not for choosing between technologies (use architecture-decision).
---

# Where the seams go, and why they hold

The as-built review of this codebase reached one conclusion about its own
structure worth starting from:

> Not in the ideas, which are good. In the seams.

Five named seams, each small, each a decision made where the information to make
it was not. They are listed with their provenance in
`references/decomposition-evidence.md`, which every step below draws on and which
you open before quoting any number from this file.

This skill is the procedure for drawing seams. Each step emits an artefact,
because a boundary you agreed with and did not write down is not a boundary.

## 0 · Reject the noun list

The default decomposition is the list of nouns in the problem statement: `User`,
`Project`, `Build`, `Library`. It is wrong reliably enough to be worth a step.
Nouns describe what the system *stores*; boundaries have to describe what the
system *changes*.

**Artefact:** the noun list, written down and then set aside. You check it again
at step 5 — not to use it, but to see what it hid.

### 0b · Borrow a decomposition from a far domain before you draw your own

Setting the noun list aside is not enough, because the carve you would reach for
next is also an anchor — and a **self-generated** first concept anchors *harder*
than a provided one (0.32 vs 0.24, F(1,165) = 4.4, p < 0.04). You cannot escape
that by intending to. Warnings against it are the single most thoroughly measured
non-intervention in this literature.

What is measured to work is a written far-domain mapping: fixation **52.4% →
26.9%** (p < 0.001, 73 professionals) with structured analogy, and **+90–173%**
diversity with explicit cross-domain relational mapping. The gain comes from the
mapping being written; "look at other fields" measured nothing.

Open `../architecture-decision/references/far-domain-analogy.md` — which is
`.claude/skills/architecture-decision/references/far-domain-analogy.md` from the
repo root — and run it with one substitution: instead of carrying back a
*mechanism*, carry back a **division of labour**.

1. State the system's overall function in one sentence with no software nouns.
2. Name one non-software organisation that performs that function — a kitchen, a
   newspaper, a hospital, a shipping line, a lending library.
3. Write how *it* is divided, in its own words: prep / line / pass / expedite;
   desk / copy / production; triage / ward / theatre / records.
4. Map its divisions onto your candidate parts, and find the one it has that you
   have nowhere.

**Artefact:** a two-column table, `their division → our part or nothing`. Every
`nothing` row is either a candidate part or a written reason it does not apply.
The empty rows are the point; the ones that map neatly tell you nothing.

## 1 · Group by what changes together

For each candidate part, answer: **when a requirement changes, how many parts
open?** One is the target. Three is a signal that the boundary is drawn across
the grain of change rather than along it.

Take the three or four changes most likely in the next six months — a new field
end to end, a new provider, a new output language, a new tenant rule — and for
each, list the parts that open.

**Artefact:** a change × part matrix. Every row with three or more marks is a
finding with a name.

Do not substitute a cohesion metric: a systematic review of 106 studies concluded
*"LCOM is not very successful in finding faults."* The matrix is about the
future; a coupling number is about the present.

## 2 · Draw the boundary on the team, and say what it costs

Organisational structure was the best predictor of post-release failure in the
largest study available here — 86.2% precision, 84.0% recall across 3,404
binaries, beating every code-metric family.

So: **count the groups that will own these parts.** If a part will be owned by
two groups, or a group will own parts either side of a boundary, that boundary is
going to be crossed and re-crossed.

**Artefact:** a part → owner mapping, one owner per part. Where you cannot supply
one, write `unowned` — an unowned part is the finding, not a gap in the document.
Where a boundary does not match an ownership boundary, one sentence saying so and
why you are keeping it anyway.

## 3 · Make each part declare what it hides

For every part: **what can change inside it without anything outside changing?**
That sentence is the part's reason to exist. A part that cannot answer it is a
folder.

Be honest about the strength of this rule: information hiding is measured here
only through a proxy (propagation cost 17.35% → 2.78% after Mozilla's redesign,
with no defect or delivery outcome measured alongside). It is a discipline that
produces a testable claim, not a proven predictor.

**Artefact:** one hiding sentence per part, and the public surface it implies —
the functions, types and routes outsiders may name. Anything not on that list is
internal, and step 4 catches it when it is not.

## 4 · Check every arrow

**Direction.** Does it point from the volatile thing to the stable thing, and
from later stages to earlier ones? An upward or backward import is where this
codebase's graph analysis found its violations: six links out of 12,054, and both
sites were seams an independent review had named. A mechanical check found them,
which is the reason to run it — the stability *principle* itself is unmeasured.

**Necessity.** Is the arrow there because the parts genuinely need each other, or
because a helper landed in the nearest file? A dependency that exists for one
utility function is a copied function waiting to happen.

**Artefact:** the list of arrows, each marked `ok`, `wrong-direction` or
`incidental`, with the two module names. Any non-`ok` arrow gets a named
resolution: move the boundary, invert the dependency, or accept it with a reason.
Three choices; picking none is not one of them.

If you used `docs/as-built/graph/graph.json` for this, say so. If it is absent —
it is, as of 2026-08-28 — the check is a targeted grep and the row is marked
`unverified against the graph`.

## 5 · Find the part that will be repaired downstream

This is the step that catches what steps 1–4 miss, and it comes from this
system's most instructive seam: granularity was fixed in the build-plan layer and
then repaired by chunking in the build layer. Nothing was wrong at either end.
The decision was made where the information was not.

For each part, ask: **does it decide something a later part will have to undo,
work around, or re-derive?** The signals:

- A part produces a shape and a later part reshapes it.
- A part answers a boolean where a later part needs a quantity — `is_buildable()`
  where the real downstream question was *how much will be invented*.
- A part fixes a size, a granularity or a limit before the thing that knows the
  limit has run.
- A later part imports an earlier part to find out what the earlier part meant.

**Artefact:** for each hit, one line — *"X decides D; Y repairs it; the
information to decide D lives in Y."* Then one of: move the decision to Y, pass
the constraint from Y to X explicitly, or record it as accepted with the reason.

Now return to the noun list from step 0, and to the `nothing` rows from step 0b.
Anything on either that is not inside a part is dead, or is the part you missed.

## 6 · Name the parts by their jobs

A name that describes fewer jobs than the unit does is the cheapest possible lie,
and this codebase has one: `run_layer_c` does four jobs and only the first is in
its name.

**Artefact:** for each part, its jobs as a numbered list. If the list has more
than one entry and the name covers one, either rename or split — and say which,
in the same line. A unit whose job list exceeds its name and is left alone
becomes a backlog item with an id, not a note.

## Output

A decomposition document under `docs/` carrying: the step-0b borrowed-division
table, the change matrix, the part → owner mapping, one hiding sentence and
public surface per part, the arrow list with verdicts, the downstream-repair
lines, and the job lists. Findings that need work become backlog items with ids.
The document is the deliverable; a conversation about the boundaries is not.

## When this skill does not apply

- One part, one owner, and no second party. Not a decomposition.
- The boundaries exist and are being obeyed. Use `architecture-review` to check
  that, not this skill to redraw them.
- The question is which technology sits inside a part. That is
  `architecture-decision`.
