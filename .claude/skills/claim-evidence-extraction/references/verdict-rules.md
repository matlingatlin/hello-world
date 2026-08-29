# MEASURED or REPEATED — the decision, and its edges

Opened at step 4 of `claim-evidence-extraction`. Rule row by row against this file,
not against your sense of what the words mean. The two verdicts are the house
vocabulary of `/home/user/skills-repo/knowledge/notes/`; they are not new here and
they must not be redefined here.

## The definitions, as the base uses them

> "Every row carries **MEASURED** (a study with numbers exists and was read) or
> **REPEATED** (widely asserted, no measurement found). The distinction is the
> content; the summary is not."
> — `ideation-and-idea-selection.md:29-31`

Two things follow that are easy to get wrong:

- **MEASURED is about provenance, not about strength.** A study with numbers that
  you read is MEASURED even when its sample is 15 and its authors disown its rigour.
  The weakness goes in the limits column, where a reader can see it. It does not
  change the verdict.
- **REPEATED is not "false".** It is "asserted, and no measurement was found by
  this search". The row still exists, because knowing that a widely believed claim
  has no measurement behind it is one of the more useful things this base contains.

## The decision

| Situation | Verdict |
|---|---|
| You opened a study, report or documentation page and quoted a line containing the result | **MEASURED** |
| A number exists in the source, you quoted it, and it is a normative or theoretical value rather than an observation | **MEASURED**, and the row must say which it is — see the trap below |
| The source is documentation stating a system's behaviour or limit, quoted | **MEASURED** (documented behaviour), and the row names the doc version or fetch date |
| Widely asserted across many secondary sources; no primary measurement reached | **REPEATED** |
| Asserted by a primary source as its own opinion or design rationale, with no measurement | **REPEATED**, source named |
| A number appears in a secondary account that cites a study you could not open | **REPEATED**, and the row names the unreached primary |
| You believe it is measured and cannot quote the line | **REPEATED.** Not "MEASURED, quote to follow" |
| Two primary sources disagree | both rows MEASURED, plus a third row recording the disagreement |
| The value moves on its own — a model limit, a cap, a price | **MEASURED** if quoted, and the row carries a pointer to the live source plus the fetch date, never a number to be trusted later |

## The trap this project has already fallen into

The most expensive error in this repository's own writing was not a fabricated
citation. It was a **real number from a real study, in the wrong column.**

`architecture-decision` and ADR-0021 both stated that Fischhoff's subjects *"moved
the probability they assigned to 'everything else' from .078 to .468"*. They did
not. `.468` is the **normative** value — what subjects should have answered. They
answered `.140`. The error described subjects as nearly self-correcting when they
had barely corrected at all, and it survived into a shipped skill and a signed
decision record until an independent review found it (`docs/CHANGELOG.md:14-20`).

Both numbers are in the paper. Both are correct numbers. The claim was still false.

So: **a row carrying a number says what kind of number it is** — observed value,
normative value, baseline, control, or the difference between two of them. If the
quote does not make that clear on its own, the quote is too short.

## Two failure shapes to watch for while extracting

- **Drift toward the argument.** The Fischhoff error made the intervention look
  better. Errors are not randomly distributed; they land where you wanted them.
  When a row is unusually convenient, re-read the quote before writing the cell.
- **A count is not a count of things.** "Nineteen skills" and "eighteen skills" for
  the same set appear seven lines apart in one note in this base, with no query
  behind either. Any number that came from counting names the query that produced
  it and what one unit is.

## What this file does not decide

Whether the source actually supports the claim. That is a different agent's job —
`primary-source-verification`, run by an agent that did not write the row, which
fetches the source itself rather than reading your account of it. Nothing in this
file is a substitute for that, and a row marked MEASURED here is still unverified
until it has a verdict there.
