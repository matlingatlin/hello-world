---
name: knowledge-note-drafting
description: "Use when a claim table has to become a knowledge note that matches the base it is joining rather than a new format — frontmatter with per-source fetch dates, per-claim MEASURED or REPEATED verdicts, an explicit section for what could not be found measured, reciprocal links, and a status that says unverified because nobody has checked it yet. Run it as the last step of a research sweep, before anything is handed to a verifier. Produces the draft note and the back-link table its neighbours need. NOT for gathering or judging evidence (claim-evidence-extraction), NOT for promoting a note into the knowledge base (note-promotion, a different agent), and never for marking your own work verified."
---

# Writing the note the base already writes

The format here is **not yours to design**. It exists, it works, and a second
format would fork the base — which costs exactly what a rival note costs: two
places to look, one of them stale, and no way to tell which. Your job is to make
the sweep's output indistinguishable in shape from what is already there.

The exemplars are the five notes added to
`/home/user/skills-repo/knowledge/notes/` on 2026-08-28:
`ideation-and-idea-selection.md`, `design-fixation-and-anchoring.md`,
`llm-idea-generation.md`, `requirements-discovery.md`,
`architecture-evidence.md`. **Open one before you write.** Reading its gist is not
the same as opening it, and this procedure will not tell you what is in it.

`references/base-format.md` carries the contract those notes keep, with the
`file:line` behind each element. `assets/note.md` is the skeleton.

## 1 · Open an exemplar and the format reference

One of the five, read, not remembered. Then `references/base-format.md`.

The elements that are not optional, because every exemplar has them: frontmatter
with `title`, a per-source `sources:` list where each entry carries a URL, a full
citation and a `fetched:` date, `status:`, `tags:`, `related:`; a house-rule line
naming the per-claim verdict scheme; claim tables rather than prose paragraphs where
there are numbers; and a closing section for what could not be found measured.

**Artefact:** which exemplar you opened, and the element list checked against it.

## 2 · Build `sources:` from the claim rows, not from your browser history

The source list is the **union of the sources named in the claim table**, and
nothing else. Two failure directions, both observed in this base:

- A source in the frontmatter that no claim rests on. It reads as support and is not.
- A claim citing a source the frontmatter does not list — `long-text-comprehension.md:61`
  attributes a token heuristic with a stated `±15%` precision to "ECC
  token-budget-advisor", which is not among that note's three sources. The origin
  cannot be reached from the note, and the note is marked `verified`.

Every entry carries a URL, a full citation naming authors, year, title and venue
where the source is a paper, and the date you fetched it. Not the date you are
writing.

**Artefact:** the `sources:` block, and a check that the set of URLs in it equals
the set of URLs in the claim table.

## 3 · Write the body as claim tables, and keep the empty cells

Group by question, not by source — a reader arrives with a question, not with a
bibliography. Inside a group, the claim rows from the extraction step go in with
their columns intact, including the empty ones.

Do not smooth. If four rows have no sample size, four cells are empty and the
reader can see the shape of the evidence at a glance. Prose that spans the gap
reads like more evidence than there is, and it is the specific way this base's
older notes stop being checkable.

Where two sources disagree, say so in the text and keep both rows. The base does
this well; match it.

**Artefact:** the body, with every numeric claim inside a table row that carries its
verdict.

## 4 · Close with what could not be found measured

The list from the extraction step, verbatim: each unanswered question, what was
searched, and the finding that nothing measured was found. Then the out-of-scope
rows from the scope contract, so a reader can tell "we looked and found nothing"
from "we did not look, and here is why".

This is the section the next stage of the pipeline reads hardest. It is what stops
a rule with no evidence behind it from being written into an agent as though it had
some.

**Artefact:** the closing section, with both lists distinguishable.

## 5 · Make the links reciprocal, and emit the ones you cannot write

`related:` is a graph, and a graph written by one author at a time comes out
one-sided. In the base as it stands, four wikilinks resolve to no note at all —
`[[plugins]]` in two files, `[[context-budget]]`, `[[unified-memory]]` — and many
pairs point one way only: one note names three neighbours and none of the three
names it back. The repository's own standing rules already record the cause,
*"parallel authoring produces one-sided links structurally"*, and attach no
mechanism to it.

So: for each neighbour you name, check the target note exists, and check whether it
names you back. Where it does not, you cannot fix it — an existing note is edited by
a human, not by this pipeline. Emit the row instead.

**Artefact:** the back-link table: neighbour note, whether it exists, whether it
names this note, and the exact `related:` line a human would add.

## 6 · Set `status: unverified`, and say so out loud

The status of your draft is `unverified`. Not `verified` — nobody has checked it,
and you are the last agent who could honestly claim to have. In the base this feeds,
26 notes of 26 say `status: verified` and not one names who verified it; that field
currently records that an author was satisfied with their own work.

Write the draft to `docs/research/drafts/<id>.md`, with the scope contract at the
top and the claim table preserved below the note body so the verifier can rule row
by row without reconstructing it.

**Artefact:** the path written, the claim count, and the sentence naming which agent
verifies it next.

## When this does not apply

- **The claim table is empty.** Then the deliverable is the scope contract plus the
  "could not be found measured" list, and that is a complete and useful answer. Do
  not pad a note out of nothing.
- **An existing note owns the topic.** The scope contract's verdict was `extend`.
  Write the addition as a patch against that note — the lines and where they go —
  because nothing downstream may rewrite a note that already exists.
- **You are about to invent a field or a section the exemplars do not have.** Stop.
  Additions to the base's shape are a change to a shared contract and need its
  owner's assent; record the proposal in the draft rather than shipping the fork.
- **The note is about this repository rather than a domain.** Repo facts are checked
  at `file:line` against the artefact and live in this repo's documents, not in the
  knowledge base.
