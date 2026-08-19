# The component library

> **Provenance:** this document was written alongside the first build slice
> (B045), from the flow agreed in the planning chat. It had been referenced by
> earlier kickoffs but never landed in the repo — so what is below describes the
> design *as built*, and says plainly which parts are not built yet.

## Why it exists

Every app Scio builds shares most of its substance with every other app. A
booking flow is a booking flow; a labelled input is a labelled input. Generating
each one afresh means paying a model to rediscover it, waiting while it does,
and accepting whatever quality that particular run produced.

The library inverts the default. **Assembly first, generation as the fallback.**
The parts that come from the catalog are curated, tested, security-reviewed and
instrumented — so the more of an app that comes from the library, the cheaper the
build, the faster it finishes, and the less of it is a guess. This is the "nave"
in `docs/STRATEGY.md`: build it, and the cost estimate and modular, cheap
building fall out of it.

## The flow

```
Layer B (architecture)
        │
        ▼
   ┌────────────┐   match      ┌──────────────┐
   │  MATCHER   │ ───────────▶ │   CATALOG    │
   └────────────┘              └──────────────┘
        │                             │
   no match                       match: fetch
        │                             │
        ▼                             ▼
   ┌────────────┐              ┌──────────────┐
   │  GENERATE  │              │    ADAPT     │  entity name + tokens
   │ (the loop) │              └──────────────┘
   └────────────┘                     │
        │                             ▼
        │                      ┌──────────────┐
        └────────────────────▶ │   ASSEMBLE   │ ──▶ one running app
                               └──────────────┘
```

The match happens **between Layer B and Layer C** — before the plan is built, not
during the build. Knowing which parts are assembled *before* anything runs is
what makes a build's cost and quality predictable rather than discovered.

## The five layers

An entry declares which layer it belongs to. The first slice seeds two of them;
the rest exist so an entry never has to be re-homed as the library grows.

| Layer | What it holds | Seeded |
|---|---|---|
| `token` | palettes, type scales, radii | — |
| `ui` | one button, one field, one empty state | ✅ 3 entries |
| `pattern` | compositions: a form with validation, a list with filters | — |
| `feature` | whole capabilities: booking, check-in, invoicing | ✅ 1 blueprint |
| `integration` | connectors: payments, email, calendars | — |

## What an entry is

Not a snippet — a contract with files attached (`library/entry.py`):

- **provides** — the entities, operations and capabilities it covers, in
  canonical vocabulary. This is the matcher's index, and it is why a user who
  says "reservations" finds the booking blueprint: Layer B's vocabulary
  canonicalises the word before the lookup happens.
- **files** — path templates and bodies, the same deterministic decision the
  file plan makes, so the manifest's package→file map cannot disagree with disk.
- **token_bindings** — `__TOKEN_ACCENT__` → the project's `accent` token.
- **element_ids** — the `data-scio-id`s it carries. `data-scio-package` is *not*
  in the entry: that is per-project, and the builder stamps it exactly as it does
  for generated code.
- **quality** — tested, security-reviewed, accessibility and Lighthouse scores.
  An entry that has not been vetted is never offered, however good it looks.

Entries are written against a **placeholder entity** (`__ENTITY__`), never one
project's own words. Adapting is then a substitution — deterministic and
reviewable, "rename the generic thing to the project's thing" done by a regex
rather than by a model.

## Matching is deliberately strict

The two mistakes are not symmetric. Generating something the library already has
costs money. *Assembling the wrong thing* ships code that looks reviewed and is
not what the user asked for. So a match must be an identity, not a resemblance,
and it is decided in two steps that do different jobs (`library/matcher.py`,
ADR-0016):

**The category narrows.** A package about bookings only looks at entries in the
`booking` category. Categories are canonical, from a seeded registry with
aliases (`library/categories.py`) — which is what stops the library splitting
into `login`, `auth` and `user-accounts` holding three copies of one thing.

**The contract decides.** A contract is what a thing does with the project's own
words removed: canonical operations, routes and files, all written against
`__ENTITY__` (`library/identity.py`). A package assembles from an entry when the
entry's contract **covers** the package's:

- every operation the package owns is one the entry provides — four of five is
  not a match, the fifth would silently vanish;
- the files it would write are **exactly** the package's file plan;
- the entry is vetted (tested **and** security-reviewed) and not rejected.

An entry may provide *more* than a package needs; it may never provide less.
Because the contract has the entity taken out of it, a project that says
"reservations" matches what a project that said "bookings" contributed, without
anyone teaching the matcher about restaurants.

Only when two vetted entries survive is there anything for a model to decide,
and only then is the relay asked. If it cannot choose, the package generates:
the matcher never guesses.

Only `feature` and `auth` packages are matchable. A foundation, a schema or a
token set is derived from ONE architecture, and an entry claiming to cover one
would assemble the wrong app.

## Assembling is not "skip the checks"

It is the same build with the expensive, uncertain step removed. What still
happens: the files go through the same instrumentation verifier and the same
app-wide manifest, because an entry that has drifted from its contract must fail
at the moment it is written rather than three packages later. What does not
happen: no relay call, no repair loop, no waiting on a model to remember the
instrumentation rules.

An assembled package carries the entry id it came from
(`PackageBuildResult.entry_id`). That is how the contribute step knows not to
offer it back.

## Contributing back — how the library actually grows

Four hand-written entries is not a nave. The things worth having in the library
are exactly the things builds already produce and already prove, so every
delivery build offers its work back, and `library/contribute.py` is the sequence
of refusals that decides what is kept:

    skip what came from the library  →  it is already in there
    require every build gate         →  the build's own checks ARE the quality bar
    generalize                       →  one project's code becomes anybody's
    re-verify                        →  generalization can break code; prove it did not
    gate                             →  no leakage, tested, instrumented
    dedup on the contract            →  new version, new entry, or nothing
    assign an id from the store      →  category.seqno.version, seqno from the DB

**Ids.** `booking.1.1` — category, sequence number, version. The store assigns
the seqno under a lock on the category, so two builds finishing at once get 2
and 3 rather than 2 and 2.

**Quality is the build's gates**, not a fresh opinion: a package is a candidate
only if it passed every gate it was put through (tests, the vision loop
including the interaction channel and RLS, instrumentation, the validation
agents). Lighthouse and accessibility are not measured in the build yet (B048),
so `Quality.scores_measured` records which evidence an entry carries and the
gate reads the right one.

**Version vs new is decided on the contract.** A candidate whose contract
already exists is not a new entry — it is a claim to be a better version of one.
It replaces the existing entry only if it is *Pareto* better on evidence that
was counted (no worse on anything, better on something), and is otherwise
discarded. That is the difference between a library that improves and one that
accumulates. A build never replaces a seed.

**A model is used for generalization only**, and is not trusted even there: the
entity substitution runs deterministically first, and a reply that drops a
`data-scio-id`, returns a different set of files or cannot be parsed is
discarded in favour of the deterministic result. Everything that decides
anything is deterministic.

**Re-verification is not optional.** A generalized entry is adapted to a sample
entity it has never seen (`widget`) and checked: every file lands and is
non-empty, no placeholder survives into the output, the instrumentation
verifies, the validation agents pass, and the contract still holds.

**Contributed entries are provisional.** They are offerable — they cleared every
gate a seed clears plus a re-verification a seed never had — but the listing
says where they came from and that nobody has looked yet. Approving is a record
of a person having looked, not a gate on usefulness.

A preview build (Level 2) contributes nothing: it is a draft the user is about
to change.

## Where it lives

Seeds are in the repo (`library/catalog/<id>/`), reviewed like the code they
are. Contributions go to Postgres — `library_entry` and `library_category`,
created idempotently by the engine, in the same database the api uses but not in
Prisma's care (ADR-0016). Without `SCIO_CATALOG_DB` the engine still reads the
seeds, matches and assembles; it just cannot keep what it learns, and
`/library/entries` says `persistent: false` rather than pretending.

## The curation surface

```
GET  /library/entries?category=&status=      what is in there, and what is provisional
POST /library/entries/{id}/approve           a person looked at this and it stays
POST /library/entries/{id}/reject            a person looked at this and it goes
POST /library/categories                     propose a category (unconfirmed)
POST /library/categories/{name}/confirm      the only way the registry grows
```

A rejected entry is marked, not deleted: that it was offered and refused is a
fact about the library worth keeping, and a rejected entry is never offerable.

## What is built, and what is next

Built (B045, first slice):

- catalog schema + repo-backed storage (`library/catalog/<id>/entry.json` + `files/`)
- 3 UI entries + 1 full booking blueprint
- deterministic matcher with relay-only-for-ambiguity
- assembler with adaptation, package stamping and verification
- assemble-vs-generate marked on every package and shown in the build
- the contribute-back gate

Built (B061, contribute-back):

- ids, canonical categories and contracts (`identity.py`, `categories.py`)
- the catalog store — seeds on disk, contributions in Postgres, DB-assigned seqnos
- matching on category + contract, so contributed entries are found by the next build
- generalization (relay), re-verification, dedup and version-vs-new
- the contribute step in the build pipeline, and the curation endpoints

Next:

- real quality scores for contributed entries (B048): Lighthouse and
  accessibility measured in the build, so contributions are held to the same
  numeric bar as seeds
- the remaining three layers (tokens, patterns, integrations)
- fleet learning: what a build had to *fix* becomes a candidate for the library
