---
name: research-commission-scoping
description: "Use when a research sweep is about to start and its edges have not been fixed — turning a commissioned candidate sentence into a bounded question list, an explicit out-of-scope list, and a ruling on whether an existing knowledge note should be extended instead of a rival authored. Run it before any search, and again when a later stage sends the sweep back narrower. Produces the scope contract that the note, its verifier and the shaping stage all read. NOT for deciding what agents should exist, NOT for extracting claims from a source once the questions are fixed (claim-evidence-extraction), and NOT usable at all without a commission file: a topic is not a scope."
---

# Bounding a sweep before it starts

A sweep with no stated edges is bounded by whoever is writing. That has a recorded
cost in this pipeline: research runs before anyone knows what the agent will do, so
a sweep of "database" comes back for an agent that turns out to only review
migrations — the effort was real and most of it was outside the need
(`docs/decomposition-agent-pipeline.md` §5). The resolution recorded there is the
one this procedure implements: **the candidate sentence is the scope**, and a later
stage may commission exactly one narrower second sweep.

The two procedures nearest to this one take no scope input at all. The house method
note starts at *"Clarify the goal (1–2 questions max; skip on 'just research it')"*
— the topic is a given and its edges are not. This step is what that is missing.

Open `assets/commission.md` for the commission's shape.

## 1 · Refuse to start without a commission

A commission is a file under `docs/research/commissions/`. It carries the
**candidate sentence** — one sentence naming what the proposed agent does and the
artefact it emits — plus who asked, and, on a re-commission, what the first sweep
already covered and why it was too wide.

If you were handed a topic instead ("research database work"), the commission is
missing. Do not reconstruct one; a candidate sentence you wrote yourself is your
scope, not the caller's, and it will be wrong in exactly the direction that makes
your sweep interesting. Say what is missing and stop.

Name the identifier. The commission's filename is `<id>`, and `<id>` is the name of
the draft, the verdict document and the note that follow it. One identifier, four
files, so the promotion gate downstream is mechanically checkable.

**Artefact:** the `<id>`, the candidate sentence quoted verbatim, and the caller.

## 2 · Decompose the candidate sentence into questions the artefact needs

Read the sentence for its **artefact**, not its topic. "It reviews a migration and
produces a findings list at `file:line` with a verdict" needs: what goes wrong in
migrations, how it is detected in a static artefact, what a finding must carry to be
actionable, and what is only checkable by running something. It does not need
database performance tuning, ORM design, or query planning.

Each question is one line, and each names what a good answer would let the later
stage decide. A question that cannot say that is a topic in disguise.

**Artefact:** the question list, each row naming the decision it serves.

## 3 · Write the out-of-scope list, with reasons — this is the half that gets skipped

For every neighbouring area the topic would naturally pull in, one row: what it is,
and why the candidate sentence does not need it. This list is not padding. It is
what tells the shaping stage *what it would have to commission* if it disagrees
with your reading, and it is what stops a second sweep from re-covering ground.

If the evidence you later find suggests the sentence itself was wrong, that goes
here as a row too — you record it, you do not act on it. Widening your own
commission is the failure this procedure exists to prevent.

**Artefact:** the out-of-scope list, one reason per row.

## 4 · Rule extend-or-author against the existing base

Search `/home/user/skills-repo/knowledge/notes/` before searching the web. Read
`INDEX.md`, then grep the notes for the question list's vocabulary **and for its
symptoms**, not only its name. The standing rule of that repository is to extend a
note that already owns a topic rather than add a rival to it, because rivals drift
apart and nobody notices which one is stale.

Then rule, in one line: `extend <note>` or `author <name>`. "Nothing exists" counts
as evidence only if you can say where you looked — record the queries.

Note the cost of `extend`: an existing note cannot be rewritten by the verifier
downstream, so an extension arrives as a patch a human applies. Say so in the row,
so the caller knows what they are asking for.

**Artefact:** the queries run, and one `extend` or `author` verdict.

## 5 · Fix the search protocol, and reuse rather than reinvent it

Open `/home/user/skills-repo/.claude/skills/literature-review/SKILL.md` and run its
sections 2 to 5 — the search protocol, the search log, the four-key deduplication
order, and staged screening with recorded exclusion reasons. It is a good procedure
and it is already written; do not author a second one.

Two additions it does not carry, both from what this base has already got wrong:

- **Prefer the primary source, and record when you are not at one.** A secondary
  account that cites a study is not the study. This base has recorded three
  fabrications in one short secondary text, each attached to a real citation.
- **Cap lookup attempts at about three per source and state the uncertainty**
  rather than looping.

**Artefact:** the search log table, started, with the databases and the exact query
strings that will be run.

## 6 · Emit the scope contract

One section at the top of `docs/research/drafts/<id>.md`, before any claim:

the `<id>` and the candidate sentence · the question list · the out-of-scope list
with reasons · the extend-or-author verdict with its queries · the search log.

Your stopping condition for the whole run is this contract: the sweep ends when
every question row carries either a claim row or an explicit "not found measured"
row. It does not end at a number of sources, and you set no target — quotas act as
ceilings, measured: told "5–7" people produced 7, told "at least 20" they produced
21, told nothing they produced 29.

**Artefact:** the scope contract section, written, at the path.

## When this does not apply

- **There is no commission.** Step 1 stops. This is the common case and declining is
  the correct output, not a failure to produce one.
- **The question is about this repository rather than a domain.** Reading what a
  system does is a different job with different evidence; route it to the agents
  that hold the corpus.
- **A note already answers the question and the caller wants it repeated.** Say
  which note, quote the lines, and do not sweep. Re-researching a settled question
  produces a rival note, which is the outcome the base's own rule forbids.
- **The commission is a re-commission that is not narrower.** One narrower second
  sweep is the agreed resolution. A second sweep that is wider is a new commission
  and needs whoever owns the pipeline to say so.
