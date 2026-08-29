---
name: claim-evidence-extraction
description: "Use when sources have been found and their content has to become claims someone else can check — one row per claim carrying the source, the locator, the quoted line, what was measured, the effect size, the sample and population, the limits, and a verdict of MEASURED or REPEATED. Use it whenever a number, a study or a documented behaviour is about to be written down as evidence. Produces the claim table a draft note is built from and a verifier rules on. NOT for bounding what to research (research-commission-scoping), NOT for assembling the finished note (knowledge-note-drafting), NOT for ruling whether a source supports a claim (primary-source-verification, a different agent), and not applicable where nothing was read."
---

# Turning a source into rows somebody else can check

The unit of work here is the **claim**, not the source and not the section. A claim
that cannot be checked without re-reading everything you read is a claim nobody will
check. In the base this feeds, one note cites a single URL and asserts on the order
of forty separate facts; another lists three sources and makes about a dozen claims
across sections titled "Verified claims", "Outdated claims" and "Overstated claims",
with no claim naming which source it came from. Both are marked `status: verified`.

The rule that makes the difference is small and absolute: **a row carries the quoted
line.** A number you can recall but not quote is a number you are reconstructing.
This project has already shipped one — a figure attributed to a real study, stating
the opposite of what the study measured, in a live skill and a signed decision
record, drifting in the direction that flattered the argument
(`docs/CHANGELOG.md:14-20`).

Open `references/verdict-rules.md` at step 4. Do not rule MEASURED from memory of
what the words mean.

## 1 · Reach the primary source, and record it when you have not

Work one question from the scope contract at a time. For each source, before
reading: is this the thing itself, or an account of it? A blog post describing a
study is not the study. A vendor changelog is primary for the vendor's behaviour;
a summary of that changelog is not.

If you can only reach a secondary account, that is allowed and it is **recorded** —
the row's source is the secondary account, and the primary is named as unreached.
Do not silently promote the secondary's citation into your row as though you had
opened it. That is the precise mechanism behind the misattributions this base warns
readers about: three fabrications in one short text, each attached to a real
citation.

For a long source, run
`/home/user/skills-repo/.claude/skills/deep-reading/SKILL.md` sections 1 to 5.
**Not its sections 6 and 7** — those are a self-test against the source and a
self-assigned `status: verified`, and both belong to a different agent here.

**Artefact:** per source — what it is, whether it is primary, and the locator
scheme you will cite by (page, section, line, timestamp).

## 2 · Split what you read into single claims

One assertion per row. If a sentence in your notes contains an "and" joining two
things that could be independently true or false, it is two rows.

A claim is written so that a reader who has only the source can say yes or no to it.
"Groups underperform" cannot be checked. "Individuals working alone and pooled
produced more ideas than the same number interacting, d = 1.395" can.

**Artefact:** the claim list, before any evidence is attached to it.

## 3 · Fill the row, and leave the gaps visible

| Field | What goes in it | When you cannot fill it |
|---|---|---|
| claim | one assertion, checkable against one source | — |
| source | the exact URL or citation the row rests on | the row cannot exist |
| locator | page, section, line, or heading inside that source | say "whole document" and expect the verifier to say so too |
| **quote** | the line from the source that carries the claim, verbatim | **the row is not MEASURED; see step 4** |
| what was measured | the actual dependent variable, in the source's own terms | leave empty and say so |
| effect size | the number, with its statistic named | empty |
| sample and population | n, k, who or what they were | empty — and an empty population is a limit, record it |
| limits | what the source itself says it does not establish | write "none stated by the source", which is itself a finding |
| verdict | MEASURED or REPEATED, per `references/verdict-rules.md` | — |

**Empty cells are the output, not a failure of it.** A row with a quote and four
empty cells tells a reader exactly how much is behind the claim. A row where the
gaps have been smoothed over tells them nothing and reads like more.

**Artefact:** the claim table, one row per claim, every row with a source and either
a quote or an explicit note of why it has none.

## 4 · Rule MEASURED or REPEATED, from the file and not from memory

Open `references/verdict-rules.md` and apply it row by row. The two verdicts are not
"strong" and "weak"; they are "a study with numbers exists and I read it" and
"widely asserted, no measurement found". A widely repeated claim is not upgraded by
being widely repeated, and a measured claim is not downgraded by being unpopular.

Where two primary sources disagree, both rows stay and the disagreement is a row of
its own. The base does this well already and it is the most valuable thing in it:
the two most-cited sources on one topic contradict each other on mechanism, and
almost no secondary account says so.

**Artefact:** one verdict per row, and a count of each at the end of the table.

## 5 · Collect what the search could not establish

Every question in the scope contract that produced no claim gets a row here: the
question, what was searched, and the finding that nothing measured was found.

This is not an admission. It is the highest-value output of the whole sweep for the
stage that consumes it, because it tells the shaping stage which of its intended
rules would have no evidence behind them. A rule with nothing behind it is an
opinion, and it belongs in a spec's open questions rather than in an agent.

**Artefact:** the "what could not be found measured" list, one row per unanswered
question, each naming the queries that failed.

## When this does not apply

- **Nothing was read.** There is no row without a source. If the sweep found no
  reachable sources, that is step 5's list and the whole of the output.
- **The claim is about this repository.** A claim about code or documents here is
  checked at `file:line` against the artefact, which is a different procedure and a
  different agent's job.
- **You are ruling on someone else's claims.** Extraction produces rows; ruling on
  whether a source supports a row belongs to `primary-source-verification`, run by
  an agent that did not write them. Doing both in one context is the failure this
  stage of the pipeline exists to remove.
- **The value moves on its own** — a model limit, a documented cap, a price. Record
  it as a pointer to its live source with a fetch date, never as a number in a
  procedure, and mark the row so the verifier re-fetches rather than trusting it.
