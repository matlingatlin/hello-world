# 0016. The library grows from real builds

- **Status:** Accepted
- **Date:** 2026-08-19
- **Phase:** PP4 (library) / PP6 (builds)

## Context

ADR-0014 established the component library as the product's nave: the more of an
app that comes from curated, tested parts, the cheaper, faster and more
predictable a build is, and the less of it is a model's guess. The first slice
built the search side — a deterministic matcher, an assembler, and a gate — and
seeded four entries by hand.

Four entries is not a nave. A library that only ever contains what somebody sat
down and wrote will never be big enough for the economics to matter, and writing
them by hand does not scale with the number of app shapes people ask for. The
things worth having in it are exactly the things builds already produce and
already prove: a booking feature that passed every gate is, by construction, a
tested and instrumented booking feature.

So builds have to teach the library. The danger in that is equally clear. A
library that accepts what it is given fills up with near-duplicates nobody chose,
under names nobody agreed, and the first time one of them is assembled into
somebody else's app the promise ("curated, tested, secure") is spent.

Four questions had to be answered to make growth safe rather than merely
possible: what an entry is called, what "the same thing" means, who decides
quality, and where any of it is kept.

## Decision

**Ids are `category.seqno.version`, and the store assigns the seqno.**
`booking.1.1`. The category says what area of an app this covers, the seqno
which entry within it, the version how many times it has been improved. The
seqno comes from the catalog store under a row lock on the category, never from
the process proposing the entry — two builds finishing at the same moment would
otherwise both claim `booking.2`.

**Categories are canonical and the registry grows only by proposal.** There is a
seeded registry of categories with aliases (`library/categories.py`). Mapping a
function to one is a deterministic lookup over canonical vocabulary. When the
lookup finds nothing, a category is *proposed* — recorded unconfirmed, matched
against by nothing, waiting for a person. Free-text category naming is the
mechanism by which a library ends up holding `login`, `auth`, `authentication`
and `user-accounts` as four separate things that never match each other.

**Hashtags sit on top of the category and are never a match key.** They are for
a person browsing. Matching on them would reintroduce exactly the ambiguity the
single canonical category removes.

**"The same thing" is a contract, and the contract decides — the category only
narrows.** A contract is what a thing does with the project's own words removed:
canonical operations, routes and files, all against `__ENTITY__`
(`library/identity.py`). A package assembles from an entry when the entry's
contract covers the package's; a candidate is a new *version* of an existing
entry when the contracts are equal. The asymmetry is deliberate — an entry may
provide more than a package needs, never less — and the files must be exactly
the package's file plan, or the manifest's package→file map would disagree with
the disk.

**Quality is the build's gates, not a fresh opinion.** A package is a candidate
only if it passed every gate the build put it through: tests, the vision loop
(including the interaction channel and RLS checks), instrumentation, the
validation agents. "Better" — the only thing that lets a candidate replace an
entry projects already assemble — is Pareto: no worse on anything that was
actually counted, better on something. Asking a model whether the new one is
nicer would make the library's contents drift on nothing.

**A model is used for generalization only.** Turning "Book a table at Bistro
Nord" into neutral copy is genuine rewriting work, and the relay is good at it.
Everything that *decides* anything — match, dedup, better, admit — is
deterministic. Even the rewriting is not trusted: the entity substitution is
applied deterministically first, and a model reply that drops a `data-scio-id`,
returns a different set of files, or cannot be parsed is discarded in favour of
the deterministic result.

**Nothing is added without re-verifying it.** A generalized entry is adapted to a
sample entity it has never seen (`widget`), and then checked: every file lands
and is non-empty, no placeholder survives, the instrumentation verifies, the
validation agents pass, and the contract still holds. Generalization rewrites
code; an entry is offered *instead of* generating, so breakage would be
inherited silently by every project that assembled it.

**Contributed entries are provisional, and say so.** Provisional entries are
offerable — they cleared every gate a seed clears, plus a re-verification a seed
never had, and withholding them until someone clicks approve would mean the
library never actually grows. What provisional changes is that the listing says
where an entry came from and that no person has looked at it yet. A build never
replaces a seed.

**The engine owns the library's tables; Prisma owns the product's.** Contributed
entries live in Postgres in `library_entry` / `library_category`, created
idempotently by the engine on first use, in the same database the api uses.
Prisma continues to own the product schema (ADR-0007, ADR-0009) and neither
migrates the other's tables. Without `SCIO_CATALOG_DB` the engine still reads
the seeds, matches and assembles — it simply cannot keep what it learns, and
`/library/entries` reports `persistent: false` rather than pretending.

## Consequences

**Easier.** The library grows from ordinary use, in the shapes people actually
ask for, at no extra cost — the work was done anyway. Reuse compounds: the
second app with a booking page assembles it, with no model call for that
package. Provenance is legible end to end: an entry names the project it came
from, and an assembled package carries the entry id it came from (which is also
what stops the library contributing its own entries back to itself).

**Harder / accepted costs.**

- The gate is strict, and on the free path (no model) it will refuse a lot:
  without a model to rewrite copy, any second entity of the project in
  user-visible text is a leak, and the contribution is refused. That is the
  right failure — the refusal is reported with its reason — but it means the
  library grows meaningfully only on real runs.
- Contributions are judged on build gates rather than Lighthouse and
  accessibility scores, because the build does not measure those yet (B048).
  `Quality.scores_measured` records which world an entry is in so the gate reads
  the right evidence; when B048 lands, contributed entries get real numbers and
  the same bar as seeds.
- Only `feature` and `auth` packages are matched or contributed. A foundation, a
  schema or a token set is derived from ONE architecture, and an entry claiming
  to cover one would assemble the wrong app.
- The engine gains an optional `psycopg` dependency and a second schema owner in
  one database. The alternative — the engine calling the api for the catalog —
  was rejected below.
- A preview build (Level 2) contributes nothing: it is a draft the user is about
  to mark up and change.

## Alternatives considered

**The api owns the catalog and the engine asks it over HTTP.** Rejected: it
inverts the only dependency direction the system has (api → engine) and creates
a cycle, for the sake of avoiding one Python database driver. The library is the
engine's domain; the product surface has no opinion about it.

**Contributed entries land in a review queue and are invisible until approved.**
Rejected: it is the same as not growing. Every study of this pattern ends with a
queue nobody empties. Provisional-but-offerable plus a visible listing keeps a
person in the loop without making them the bottleneck.

**Match on similarity — embeddings over descriptions.** Rejected. Assembling the
wrong thing ships code that looks reviewed and is not what was asked for, and a
similarity score gives no honest place to draw the line. A contract is decidable,
explainable and testable, and when it does not match, generating is the correct
and safe fallback.

**Let the generalizing model choose the category.** Rejected: this is exactly
how category splitting happens. The model may only pick from the registry or say
"new", and "new" records a proposal for a person.

**Version by appending rather than replacing.** Rejected: two entries with one
contract make the matcher choose between things that claim to be identical, and
the tie-break would be arbitrary. A version bump replaces the line it improves;
the old code is in git.
