---
name: seam-placement
description: "Use when the system has to be carved into parts and someone must say where a boundary belongs, what crosses it, and whether the current code respects it — 'where does this split', 'should this be one service or two', 'what is the contract between these', 'is this layer leaking'. Emits a seam table with the violations found at file:line and the exact query behind every count. NOT for describing an existing layer (the as-built LAYER-*.md documents already do that), NOT for deciding a technology (design-decision-record), NOT for auditing whether a document's claims hold (design-claim-audit)."
---

# Placing a seam, and counting honestly while you do it

The as-built layer documents already carry a working format — purpose, public
surface, in and out, invariants from test names, dependencies from the graph, state,
open questions. **This procedure does not replace it.** It exists for the two places
that pass measurably failed.

**One: it named a set from memory instead of from the artefact.** The analysis said
Settings was the placeholder route; the source lists five, and the one it missed was
the one that mattered — the whole post-reveal half of the product turned out to be
unbuilt. **Two: it counted mentions instead of instances.** A "14" that was a count
of the word, not of the thing, hid that the unimplemented surface spanned six modules
rather than three.

So every set is enumerated from a query, every count is reconciled against a second
query, and both queries are written down next to the number.

Step 3 requires the call graph at
`/home/user/scio/docs/as-built/graph/graph.json` — 5,173 nodes, 12,054 edges.

## 1 · Enumerate the set from the artefact

Name the set the seam divides — routes, endpoints, modules, tables, migrations,
packages. Get it with `Glob` or `Grep`. Never from a document that describes it, and
never from recall; a document is a claim about the set, not the set.

**Artefact:** the exact query string, the count it returned, and the enumerated list.

## 2 · Reconcile the count with a differently-shaped query

Say what **one unit** is — one throwing endpoint, one route entry, one table. Then
run a second query shaped differently from the first (match the construct, not the
word; or match the word, not the construct). If the two disagree, neither number is
the answer until you have opened the difference and explained it.

**Artefact:** two query strings, two counts, and one line reconciling them — or, if
they cannot be reconciled without running something, the count marked
`not checkable here` and the command handed to the caller.

## 3 · Check direction across the seam

A dependency-direction check is cheap and deterministic. On this codebase it found
**6 violations in 12,054 links across 276 files, in exactly the two places an
independent human review had named** — which is a reason to run it, not evidence that
the underlying principle is proven. Treat the output as a fact and the principle as
unproven.

Grep `graph.json` for the nodes on each side of the seam and inspect their links.
Where the check needs the whole graph traversed, you cannot run it: this agent has no
shell. Emit the exact command for the caller and mark the result pending.

**Artefact:** violations as `file:line → file:line`, or the command handed back plus
`direction check: not checkable here`.

## 4 · Name what the seam hides and what crosses it

Two questions, both answered with artefacts:

- **What changes on one side without the other noticing?** Name the specific change —
  a vendor swap, a schema migration, a protocol version, a model provider. If you
  cannot name a concrete change the seam absorbs, the seam is decorative.
- **What crosses it?** Every type, contract, event and table that traverses the
  boundary, each with the file that defines it.

**Artefact:** one named change per seam, and a list of crossing artefacts with
defining files.

## 5 · State each seam using the vocabulary that already exists

Use the as-built states, unchanged: `solid` · `wrong-shaped` · `missing` ·
`obsolete`. Do not invent a scale. Each state is justified by a step 1–3 artefact,
cited.

**Artefact:** one state per seam with the artefact that justifies it.

## 6 · Emit the seam table

One row per seam: name · the change it hides · what crosses it · state · violations
at `file:line` · the queries behind every count.

If a seam's placement is itself a decision worth arguing over later, it is also an
ADR — hand it to `design-decision-record` rather than burying it in a table row.

**Artefact:** the seam table, written under `docs/`.

## When this does not apply

- **The layer is already documented and nobody disputes it.** Read the
  `LAYER-*.md` document. Re-deriving it adds noise where the base is competent.
- **The question is which technology sits behind the boundary.** That is
  `design-decision-record`.
- **The claim under question is "does the code match what we said".** That is
  `design-claim-audit`.
- **The seam's correctness depends on runtime behaviour** — a race, a load shape, a
  timeout. You cannot execute. Emit it as `not checkable here` with what would settle
  it, and stop.
