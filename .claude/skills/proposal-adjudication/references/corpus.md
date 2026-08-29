# The corpus, by absolute path

Every path here is absolute, and that is the whole point of the file.

`docs/as-built/` **is not in this repository.** It lives in the sibling repo at
`/home/user/scio`. Twelve files in `hello-world` cite it as though it were local
(backlog **B128**), and a `file:line` quoted from a document you could not open
is the exact failure this reference exists to prevent. Relative paths here would
resolve — silently, to nothing.

Verified present on 2026-08-29. If a path below is missing when you run, that is
a finding for step 1's second list, not a reason to proceed from memory.

## What the system already is — `already-built` rulings

| Path | Holds |
|---|---|
| `/home/user/scio/docs/as-built/00-INDEX.md` | entry point; read first |
| `/home/user/scio/docs/as-built/ARCHITECTURE-AS-BUILT.md` | the system as it stands, not as planned |
| `/home/user/scio/docs/as-built/01-DECISIONS.md` | decisions already taken |
| `/home/user/scio/docs/as-built/LAYER-A-INTAKE.md` … `LAYER-G-CROSS-CUTTING.md` | seven layer documents, A B C D E F G |
| `/home/user/scio/docs/as-built/JOURNEY-INVOLVED-PATH.md` | the end-to-end path through the layers |
| `/home/user/scio/docs/as-built/REVIEWS-FINDINGS-VERIFIED.md` | findings that survived verification |
| `/home/user/scio/docs/as-built/REVIEWS-WHAT-WE-MISSED.md` | findings about the review process itself |
| `/home/user/scio/docs/as-built/graph/graph.json` | the call graph — **this file exists**, so an arrow check against it is available and a row you mark `unverified against the graph` needs a reason other than absence |

## What has already been proposed — `already-proposed` rulings

**85 standing proposals**, in §9 `ADR proposals` of the seven layer documents
under `/home/user/scio/docs/next/`. Ids are `<layer letter>-<n>`: `A-1`, `G-2`.
They are table rows, so grep the id, do not scan for a heading.

| Path | §9 proposal ids |
|---|---|
| `/home/user/scio/docs/next/LAYER-A-INTAKE.md` | `A-*` |
| `/home/user/scio/docs/next/LAYER-B-UNDERSTANDING.md` | `B-*` |
| `/home/user/scio/docs/next/LAYER-C-BUILD-PLAN.md` | `C-*` |
| `/home/user/scio/docs/next/LAYER-D-LIBRARY.md` | `D-*` |
| `/home/user/scio/docs/next/LAYER-E-BUILD.md` | `E-*` |
| `/home/user/scio/docs/next/LAYER-F-DESIGN-WINDOW.md` | `F-*` |
| `/home/user/scio/docs/next/LAYER-G-CROSS-CUTTING.md` | `G-*` |

`/home/user/scio/docs/next/README.md` states the nine headings every layer
document carries and the standing rule the proposals exist under: *"Nothing here
is decided."* A candidate matching a proposal is `already-proposed`, never
`already-built` — §9 is a list of things that have **not** happened.

## What has been settled — `not-applicable` rulings

| Path | Holds |
|---|---|
| `/home/user/scio/docs/decisions/` | accepted ADRs. Two today: `0001-graph-is-standard.md` and the template |
| `/home/user/hello-world/docs/decisions/` | this repo's ADRs |

Two accepted ADRs is a small denominator. `not-applicable` therefore rests far
more often on a layer document or a verified review finding than on an ADR, and
the ruling must name which.

## Where the reasoning was already stress-tested

| Path | Holds |
|---|---|
| `/home/user/scio/docs/triage/LAYER-*.md` | four triage documents — proposals already argued down |
| `/home/user/scio/docs/evals/` | ablations and case catalogues, including `architecture-ablation.md`, `as-built-ablation.md`, `CASES-RESEARCH.md` |

A candidate that a triage document already rejected is not `new`. Grep the
triage set before writing that ruling.

## The searches, when you rule `new`

`new` requires the searches you ran, named. The minimum that counts:

1. `grep -rn "<term>" /home/user/scio/docs/next/` — all 85 proposals
2. `grep -rn "<term>" /home/user/scio/docs/as-built/` — what exists
3. `grep -rn "<term>" /home/user/scio/docs/triage/` — what was already argued down

Three empty greps is evidence. "I found nothing" is not.
