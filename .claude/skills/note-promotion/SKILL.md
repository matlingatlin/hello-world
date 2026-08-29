---
name: note-promotion
description: "Use when a draft note has been verified claim by claim and a decision is needed about what may cross into the knowledge base — which claims survive, which are dropped or marked, what the note's status and verified_by record say, and which back-links its neighbours need. Run it only after a verdict document exists, and only for a note that does not already exist. Produces the promoted note path, the drop list and the back-link patch table. NOT for ruling on claims (primary-source-verification runs first), NOT for writing or extending a note that is already in the base, which is a patch a human applies, and never for promoting a note you drafted."
---

# What may cross into the base, and what it carries with it

Promotion is the moment an unverified draft becomes something other agents will
quote without re-checking. Everything that crosses has to carry the record of how
it got there, and everything that did not survive has to be visible rather than
quietly absent.

The rule underneath the whole step: **every line in the promoted note traces to a
draft claim with a verdict row.** You add nothing. If you noticed something true
and important while verifying, it goes in the verdict document, not in the note —
a claim introduced at promotion has no verdict behind it, and it would be the exact
defect this stage was built to remove, committed by the agent built to prevent it.

## 1 · Check the gate before writing anything

Three conditions, all of them, before a single write:

- **A verdict document exists** at `docs/research/verdicts/<id>.md`, and its row
  count equals the draft's claim count. A missing or short verdict document means
  verification did not finish.
- **The target note does not already exist** in
  `/home/user/skills-repo/knowledge/notes/`. If it does, this is an extension, and
  an extension is step 5's patch — not a write.
- **You did not draft it.** The verdict document names the draft's author. If that
  is you, stop; a promotion is a judgement and this one is not yours to make.

A hook enforces the first two mechanically — `.claude/hooks/note-promotion.sh`,
installed, its table run on 2026-08-29 and passing. It denies a note write with no
verdict document for that id, denies one whose verdict carries no ruling token, and
denies overwriting a note that already exists.

**It cannot enforce the third**, which is the one about who wrote the verdict. A
path gate sees paths. If the verifier is you, stop — there is nothing downstream
that will notice.

**Artefact:** the three checks, each with the path or count that satisfied it.

## 2 · Sort every claim by its verdict

| Verdict | What happens to the claim |
|---|---|
| `supported` | crosses, with its quote and its source |
| `not-supported` | **crosses, marked** — the claim, the verdict, and the quote that contradicts it, under a "refuted during verification" heading |
| `not-in-source` | crosses, marked, with what was read and where |
| `source-unreachable` | crosses, marked, with the URL and the attempt count |
| `not-checkable` | crosses, marked, with what would settle it |

Only `supported` claims appear as claims. Everything else appears as a record that
the question was asked and did not settle.

Retaining rather than deleting is a choice with no measurement behind it, and it is
recorded as such in `docs/agent-spec-domain-research.md` §8.4. The reasoning: a
deleted claim is silently re-researchable, the next sweep spends the same effort,
and this base has an unusually strong habit of recording what it could not
establish. If a later measurement says otherwise, change it there first.

**Artefact:** the drop-and-mark list, one row per non-`supported` claim.

## 3 · Write the note, with the record attached

Take the draft's note body, remove any sentence that rests on a claim that is not
`supported`, and set the frontmatter:

- `status: verified` — the base's existing vocabulary, unchanged.
- `verified_by: docs/research/verdicts/<id>.md` — **the one addition this pipeline
  makes to the base's frontmatter.** It is additive; every existing note stays valid
  without it. It is flagged in the spec as a change to a shared contract, and if the
  base's owner declines it, the verdict path goes in the body instead and this line
  goes away.
- `sources:` unchanged from the draft, minus any source no surviving claim rests on.

Then write it to `/home/user/skills-repo/knowledge/notes/<id>.md`. This is the point
of the standing rule in that repository — *a verified fact lands in `knowledge/notes/`
in the same turn it is verified* — and the reason the verifier holds the write rather
than the researcher: the applicant never writes their own credentials file.

**Artefact:** the note path, and the diff between the draft body and what was
written, stated as removed sentences.

## 4 · Set the links you can, and emit the ones you cannot

Carry the draft's back-link table forward. For each neighbour: confirm it exists as
a note, and confirm whether it names this note back.

You may not edit a neighbour. Emit the patch: the neighbour's path, its current
`related:` line, and the line a human should replace it with. A note that arrives
with no incoming links is reachable only by someone who already knows it exists.

**Artefact:** the back-link patch table, with an exact replacement line per row.

## 5 · If the note already exists, produce a patch instead

An extension does not go through this procedure's step 3. It goes out as a document
under `docs/research/patches/<id>.md`: the target note, the exact insertion point,
the new claim rows with their verdicts, and any `sources:` entries to add.

A human applies it. That costs a hop, and friction gets skipped — which is recorded
as an open question in the spec rather than solved here. The reason for the cost is
the same one that governs this whole repository's agent files: an agent that can
edit existing records can rewrite them, and content inspection does not close that
class. Create-only does.

**Artefact:** the patch document path, and the target note it applies to.

## 6 · Report what crossed and what did not

Never the note path alone. Say: the claim count that crossed, the count of each
non-`supported` verdict, the sources dropped, the back-links still owed, and the
one thing this whole stage cannot see — whether the sweep asked the right questions.
That judgement belongs to the stage that commissioned it, against the draft's scope
contract.

**Artefact:** the closing report, with those five numbers.

## When this does not apply

- **No verdict document.** Step 1 stops. An unverified draft does not cross, and
  saying so is the output.
- **Every claim is `source-unreachable` or `not-checkable`.** Nothing crosses as a
  claim. The honest artefact is the verdict document plus a one-line statement that
  the note could not be established by anyone, which is more useful than a note of
  hedges.
- **The note already exists.** Step 5's patch, always.
- **You are being asked to improve the note rather than promote it.** Improvement is
  authorship, and the author is a different agent. Route it back with the verdict
  document as the reason.
