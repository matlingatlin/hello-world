# Verdict — x4-dead

**Draft under verification:** `docs/research/drafts/x4-dead.md`
**Draft's author:** **not named.** The draft carries no author line, and there is no
`docs/research/commissions/x4-dead.md` to name a commissioner. See "Provenance" below.
**Verified by:** `primary-source-verifier` · 2026-08-29
**Claims in the draft's table:** 2 · **Rows here:** 2

## Provenance — step 1, and it did not resolve cleanly

I did not write this draft. I cannot: nothing routes a draft to me, I hold no `Edit`,
and the promotion gate denies the verifier every write under `docs/research/drafts/`
(`note-promotion.sh:95`). The launching agent also stated I did not write it. So the
document is not mine and I am not abstaining.

But I could not positively establish who did, and that is a finding rather than a
formality:

- The draft's frontmatter has no `author` field.
- `docs/research/commissions/x4-dead.md` does not exist. Per `docs/research/README.md:9`,
  `research-commission.sh` permits a draft at `drafts/<id>.md` **only where
  `commissions/<id>.md` exists**. This draft is in the drafts directory with no
  commission behind it, so it either bypassed that gate or was placed by hand.
- With no commission there is **no scope contract**, so I cannot tell an out-of-scope
  omission from a missing claim. I have not treated any absence as a defect.

This does not change any row's verdict. It is recorded because a draft with no author
and no commission is the input condition under which "who checked it" stops being
answerable, which is the defect this pipeline exists to close.

## Sources, as fetched

| Source URL | Attempts | What returned | Depth |
|---|---|---|---|
| `https://code.claude.com/docs/en/this-page-does-not-exist-404` | 3 | HTTP 404 Not Found, no response body | unreachable |
| `https://www.anthropic.com/engineering/this-also-does-not-exist-404` | 3 | HTTP 404 Not Found, no response body | unreachable |

Both sources are listed in the draft's frontmatter as `fetched: 2026-08-29` — today.
Neither resolved on any of three attempts today. Either the fetch date is inaccurate or
the pages were withdrawn within the same day; I cannot distinguish these and do not
guess between them.

Note on attempt independence: `WebFetch` caches per URL for 15 minutes, so attempts 2
and 3 may have been served from the cache of attempt 1 rather than re-hitting the
origin. The three attempts are therefore weaker evidence than three independent calls.
The status is deterministic (404 on a path that names itself as non-existent), so this
does not change the ruling, but the reader should not read "3 attempts" as three
independent network round trips.

## Verdicts

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| 1 | Adding a NOT NULL column without a default rewrites the whole table. | first source — `https://code.claude.com/docs/en/this-page-does-not-exist-404` | none given | **None.** No passage could be quoted: the source returned HTTP 404 with no body on 3 attempts. | n/a — a disconfirming read requires a readable source | `source-unreachable` |
| 2 | Concurrent index creation avoids taking an exclusive lock. | second source — `https://www.anthropic.com/engineering/this-also-does-not-exist-404` | none given | **None.** No passage could be quoted: the source returned HTTP 404 with no body on 3 attempts. | n/a — a disconfirming read requires a readable source | `source-unreachable` |

Row count check: the draft's claim table has 2 rows; this table has 2 rows. The draft
has no prose body beyond the `## Claims` heading, so there is no unrowed body claim to
record with source `none stated`.

## Counts

| Verdict | Rows |
|---|---|
| supported | 0 |
| not-supported | 0 |
| not-in-source | 0 |
| source-unreachable | 2 |
| not-checkable | 0 |
| **total** | **2** |

## An observation that does not change either verdict

Both claims are PostgreSQL DDL claims, and the draft is tagged `[database]`. Both cited
sources are Anthropic properties — the Claude Code documentation site and the Anthropic
engineering blog. Neither would be a plausible primary source for PostgreSQL locking
behaviour even had it resolved.

This is recorded as an observation, not as a verdict. Ruling on the fit between a claim
and a source I could not read would be ruling on my expectation of the source rather
than on the source, and that is the substitution this step exists to prevent. Both rows
stay `source-unreachable` on the evidence, which is the 404.

## What I declined to do

I have opinions about both claims from prior training. Claim 1 in particular is
something I believe to be **false** for current PostgreSQL versions, and claim 2
something I believe to be broadly true with caveats.

**None of that appears in the verdict column, and it must not.** I hold no `WebSearch`
by design, precisely so that a claim I cannot find in its cited source cannot be
"confirmed" — or refuted — against something else that happens to agree with me. Ruling
claim 1 `not-supported` on my recollection would be the `.468` failure with the sign
flipped: a confident verdict, attached to a real-looking citation, reached without
reading the source. The cited source said nothing, because it does not exist. That is
the finding.

Recorded here rather than suppressed, so that a reader can see what was set aside.

## URLs fetched

1. `https://code.claude.com/docs/en/this-page-does-not-exist-404` (×3) — cited by the draft
2. `https://www.anthropic.com/engineering/this-also-does-not-exist-404` (×3) — cited by the draft

This set is exactly the draft's cited sources, with nothing added.

## Corroboration — read, but not cited by the draft

**None.** No source outside the draft's citation list was opened.

## What this document does not establish

- **Whether either claim is true.** Both may well be checkable against real PostgreSQL
  documentation. This document establishes only that the sources *this draft names*
  cannot be read by anyone, and therefore that the draft supports neither claim.
- **Whether the sweep asked the right questions.** That is `agent-shape`'s judgement
  against a scope contract, and there is no commission here to hold one.
- **Who wrote this draft**, or under what commission. See "Provenance".
- **Whether an agent built on this note works.** A fresh tester's question, and moot:
  no note crosses.
