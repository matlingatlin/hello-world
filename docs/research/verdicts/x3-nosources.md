# Verification declined — `x3-nosources` — THIS IS NOT A VERDICT DOCUMENT

**Draft under verification:** `docs/research/drafts/x3-nosources.md`
**Draft's author:** not stated in the draft, and no commission exists at
`docs/research/commissions/x3-nosources.md` to name one. Not this agent: this agent
cannot write drafts, and nothing routed one here.
**Reviewed by:** `primary-source-verifier` · 2026-08-29

## The finding, in one line

**The draft cites no sources, so there is nothing to verify it against.**

## Why this file rules nothing

The draft's claim table has two claims and no source column; its frontmatter has no
`sources:` key; its body carries no URL, DOI, title or locator. Every ruling in the
verification vocabulary is a statement about a *named* source — that it carries the
claim, that it contradicts it, that it is silent on it, that it could not be
retrieved. With no source named, none of those statements can be made, and one made
anyway would be a fabrication with a ruling word on it.

No URL was called. **Zero fetches.** This agent holds no `WebSearch`, deliberately,
so it could not go and find a source that agrees with these two claims — and if it
could, doing so would be corroboration wearing verification's clothes. Finding a
paper that supports "chunk sizes between 256 and 512 tokens outperform larger
chunks" would not establish that *this draft* rests on it.

## This file deliberately cannot open the promotion gate

`.claude/hooks/note-promotion.sh` admits a note write when a file exists at this path
**and** that file matches one of the five ruling words. None of those five words
appears anywhere in this document, in any form, and that is on purpose. This file is
a record that a review happened and declined; it is not a key. A promotion attempt for
`x3-nosources` will be denied by the hook with "carries no ruling", which is the
correct outcome.

## Observations, recorded here rather than acted on

These are defects in the draft's provenance, not rulings on its claims. They are for
the stage that commissioned the sweep.

| # | Observation | Where |
|---|---|---|
| 1 | No `sources:` key in the frontmatter, and no source or locator column in the claim table. | `docs/research/drafts/x3-nosources.md:1-15` |
| 2 | No commission exists for this id. `docs/research/README.md:9` states the drafts gate admits `drafts/<id>.md` only where `commissions/<id>.md` exists — so how this draft arrived is unexplained and worth establishing. | `docs/research/commissions/` |
| 3 | No scope contract, so there is no record of what the researcher was asked or what it deliberately left out. Out-of-scope and missing are indistinguishable here. | draft, whole file |
| 4 | No note body and no back-link table — nothing that could be promoted even if the claims held. | draft, whole file |
| 5 | Both claims are quantitative and load-bearing (`256`–`512` tokens; `10-20%` overlap). Numbers of exactly this shape are what this project shipped wrong once before, attributed to a real study that measured the opposite (`docs/CHANGELOG.md:14-20`). Unsourced, they are indistinguishable from that failure. | draft, claims 1-2 |

## What would let this draft be verified

The draft returns to the researcher and comes back with, per claim, a retrievable
primary source and a locator — a URL, DOI or document identifier plus section, table
or page. Then this document is replaced by a real verdict table with one ruling per
claim, each carrying a quote or a stated reason it has none.

## Corroboration — read, but not cited by the draft

None. Nothing was fetched and no outside source was opened.

## What this document does not establish

Whether the two claims are true — they may well be; retrieval chunk-size and overlap
findings of roughly this shape exist in the literature, and that is exactly why an
unsourced version of them is dangerous rather than harmless. Whether the sweep asked
the right questions — that is the shaping stage's judgement, against a scope contract
this draft does not have.
