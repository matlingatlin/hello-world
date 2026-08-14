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
not what the user asked for. So a match must be an identity, not a resemblance —
all four of these, or it generates (`library/matcher.py`):

1. the entry is vetted (tested **and** security-reviewed);
2. its entity **is** the package's entity, in canonical vocabulary;
3. every operation the package owns is one the entry provides — four of five is
   not a match, the fifth would silently vanish;
4. the files it would write are **exactly** the package's file plan.

Only when two vetted entries survive all four is there anything for a model to
decide, and only then is the relay asked. If it cannot choose, the package
generates: the matcher never guesses.

## Assembling is not "skip the checks"

It is the same build with the expensive, uncertain step removed. What still
happens: the files go through the same instrumentation verifier and the same
app-wide manifest, because an entry that has drifted from its contract must fail
at the moment it is written rather than three packages later. What does not
happen: no relay call, no repair loop, no waiting on a model to remember the
instrumentation rules.

## Contributing back

When a build is approved, a *generated* part may be offered to the library — but
only through a gate (`library/gate.py`), and only with a human choosing to. A
library that fills up automatically fills up with things nobody chose.

The gate rejects a candidate that is: untested, not security-reviewed, below the
score bar, not generalized (still written against one project's concept), or
leaking anything project-specific — a customer's name, a URL, a key, an email.

**Status:** the gate is built and tested. The contribution itself (writing an
accepted entry into the catalog) is stubbed — `propose()` reviews and reports,
it does not persist.

## What is built, and what is next

Built (B045, first slice):

- catalog schema + repo-backed storage (`library/catalog/<id>/entry.json` + `files/`)
- 3 UI entries + 1 full booking blueprint
- deterministic matcher with relay-only-for-ambiguity
- assembler with adaptation, package stamping and verification
- assemble-vs-generate marked on every package and shown in the build
- the contribute-back gate

Next:

- grow the library — more entries, the remaining three layers
- wire the cost estimate from the assemble-vs-generate plan: the plan already
  says which parts are free, which is most of what a deterministic estimate needs
- fleet learning: what a build had to fix becomes a candidate for the library
