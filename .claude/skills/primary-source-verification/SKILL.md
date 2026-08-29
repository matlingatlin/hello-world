---
name: primary-source-verification
description: "Use when claims in a document written by someone else must be checked against the sources that document cites, one claim at a time, before any of them is treated as evidence — verifying a draft knowledge note, checking whether a paper really carries the finding attributed to it, confirming a number is the observed value and not the normative one. Opens the cited source itself, never the author's summary of it, requires a quoted line or a stated reason there is none, and rules each claim supported, not-supported, not-in-source, source-unreachable or not-checkable. Produces the verdict document. NOT for extracting claims in the first place (claim-evidence-extraction), NOT for checking a design document against repo artefacts (design-claim-audit), and never applicable to claims you wrote yourself."
---

# Checking a claim against the source it names

One question per row, and it is narrow: **does the cited source carry this claim?**
Not whether the claim is true, not whether it is well put, not whether you agree
with it. **A true claim whose cited source does not carry it does not get
`supported`** — and saying so is the entire value of this step.

Which of the two non-supporting verdicts it gets is decided in step 6, and the
distinction is not cosmetic: `not-in-source` means the source is silent on the
claim, `not-supported` means it says otherwise. Absent and contradicted are
different findings and repair differently — the first needs a source, the second
needs the claim withdrawn. Do not use the two words as synonyms here or anywhere
below.

The failure mode is specific and this project has produced it. A figure attributed
to a real study, in a live skill and a signed decision record, stating the opposite
of what the study measured: `.468` reported as the value subjects moved to, when
`.468` is the **normative** value and they answered `.140`. Both numbers are in the
paper. The claim was still false, it flattered the argument that cited it, and it
was found only by a review from outside (`docs/CHANGELOG.md:14-20`).

You have no `WebSearch`, deliberately. You cannot go and find a source that agrees;
you can only open the one the document names. That is the difference between
verification and corroboration and it is the whole point of this step.

`assets/verdict.md` is the output shape.

## 1 · Establish that you did not write this

Name the author of the document under verification — from its header, its
commission, or the session that produced it. **If it is you, the whole document is
`abstained`** and it goes to a different reviewer.

Nothing mechanical enforces this; it is a procedure. Record the abstention visibly
so a reader knows the document was not checked, rather than assuming it was.

**Artefact:** the author line, and an `abstained` document-level row if it fires.

## 2 · Take the claims as they are written

Read the document's claim table. Do not rewrite, sharpen or improve a claim before
ruling on it — a claim you have improved is a claim you wrote, and you are then
verifying your own work.

Copy each claim verbatim into a verdict row, with its stated source and locator.
The row count of your document equals the row count of theirs, before you fetch
anything. A claim in the note body with no row in their claim table is itself a
finding: record it as a row with source `none stated`.

**Artefact:** the verdict table, populated with claims and sources and no verdicts
yet, and its row count set against theirs.

## 3 · Fetch the source, and record what you actually got

One source at a time, from the URL in the row. Three attempts, then
`source-unreachable` — do not loop, and do not substitute.

Check identity before content: is the thing that came back the thing the row names?
A DOI that resolves to a landing page is not the paper. A documentation URL that
redirects to a newer version is a different source than the one fetched on the date
in the frontmatter, and that difference is the row's finding.

Record, per source: the URL you called, what came back, and whether it is the full
text or an abstract, a landing page, or a paywall. **A claim checked against an
abstract is `not-checkable`, not `supported`** — abstracts state conclusions and
almost never carry the sample, the effect size or the limits.

**Artefact:** per source — URL called, what returned, and its depth.

## 4 · Find the line, quote it, and check the kind of number

For each claim on that source: locate the passage, quote it verbatim into the row,
and compare it against the claim word by word. Three specific comparisons, each of
which has failed here or in the writing this base has examined:

- **Is the number the same kind of number?** Observed or normative, treatment or
  control, absolute or difference, per-group or pooled. This is the Fischhoff trap
  and it is invisible unless you ask.
- **Is the population the same?** A result on 15 units is not a result on 2,577,
  and a result on students is not a result on professionals.
- **Does the source draw the conclusion, or does the claim draw it?** A source
  reporting a correlation is not a source reporting a cause. In the writing this
  base examined, one short secondary text attributed to one paper a finding absent
  from it and to another the exact reverse of its conclusion — three fabrications,
  each attached to a real citation.

If the quote does not settle the comparison, the quote is too short. Extend it.

**Artefact:** per row — the verbatim quote, or an explicit statement that no
passage carries the claim and which sections were read.

## 5 · Run the read that would show you wrong, before ruling anything not-supported

A finding that a claim is unsupported is itself a claim, and it inherits every
failure mode above. Before writing `not-supported`, run one read designed to
disconfirm you: a second vocabulary for the same concept, a different section, the
appendix, the supplementary material, an earlier or later edition.

**A row with no disconfirming read recorded cannot be `not-supported`.** It is
downgraded to `not-in-source`, which says exactly where you looked and stops there.

This is not caution for its own sake. A verifier that finds a defect in everything
cannot discriminate, and this base is not uniformly defective: three of three
documented limits in `subagents.md` were checked live against their cited source on
2026-08-29 and all three held, quoted.

**Artefact:** per `not-supported` row — the disconfirming read and what it returned.

## 6 · Rule every row, and count the verdicts

Exactly one per row:

| Verdict | When |
|---|---|
| `supported` | the quoted passage carries the claim, including the kind of number and the population |
| `not-supported` | the source contradicts the claim, with the quote, and step 5 was run |
| `not-in-source` | the source is reachable and read, the claim is not in it, and step 5 was not run or was inconclusive |
| `source-unreachable` | three attempts failed, or what returned was a landing page or paywall |
| `not-checkable` | it needs execution, a private dataset, a purchase, or a claim about the future. Say what would settle it |

`not-checkable` is a finished answer, not a failure to finish. So is a table of all
`supported`.

**Artefact:** one verdict per row, and a count of each at the foot of the document.

## 7 · Emit

`docs/research/verdicts/<id>.md`, using `assets/verdict.md`, where `<id>` is the
draft's identifier unchanged — the downstream promotion gate matches on it.

Close with: the verdict counts, the list of URLs you fetched, and a separate list of
anything you read that the draft did not cite, under **corroboration**. Corroboration
never changes a verdict; it is recorded so that a reader can see you went outside the
cited set and by how much.

**Artefact:** the file path, the counts, the fetched-URL list, the corroboration list.

## When this does not apply

- **You wrote the claims.** Step 1 abstains. This is the case the whole procedure
  exists for and declining is the correct output.
- **The document cites nothing.** There is nothing to verify against. The finding is
  that the document has no sources, and it is one line.
- **The claim is about this repository.** Repo claims are checked at `file:line`
  against the artefact, by an agent that can read the artefact.
- **The sources are all unreachable.** Emit the document with every row
  `source-unreachable` and stop. That is a real and useful result: it says the note
  cannot be checked by anyone, which is a stronger finding than any single row.
