# 0014. Component library — assemble curated parts before generating

- **Status:** Accepted
- **Date:** 2026-08-12
- **Phase:** PP4/PP5 (engine · the library)

> Recorded alongside the first build slice (B045). Earlier kickoffs referenced
> this ADR, but it had never landed in the repo; this writes down the decision as
> agreed in planning and as built.

## Context
Every app Scio builds repeats most of another app. Generating each part afresh
pays a model to rediscover a booking flow or a labelled input, takes minutes per
package, and yields whatever quality that run produced. The first two real runs
against Claude showed the cost of that concretely: ~$1.42 and 14 minutes for five
packages, with one part still needing a look.

`docs/STRATEGY.md` calls the library "the nave": build it and the cost estimate
and cheap modular building fall out of it. It is also the part no Anthropic API
primitive replaces (STRATEGY §G) — the moat, not a commodity.

The risk is the mirror image. A part offered *instead of* generating carries
authority: nobody reviews it again per project. Assembling the wrong thing ships
code that looks reviewed and is not what the user asked for.

## Decision
The engine keeps a **catalog of curated parts** and, between Layer B and Layer C,
**matches every package against it**. A match is assembled; anything else is
generated as before.

- Entries are **contracts with files attached**: what they provide (in canonical
  vocabulary), the exact files they write, their token bindings, their
  `data-scio-id`s, and their quality metadata.
- Entries are written against a **placeholder entity**, so adapting to a project
  is a deterministic substitution, not a model call.
- **Matching is strict and deterministic**: vetted entry, same canonical entity,
  every owned operation covered, and files exactly equal to the package's file
  plan. The relay is asked only to break a genuine tie between two entries that
  pass all four, and a tie it cannot break generates.
- **Assembly is verified like generation**: the instrumentation verifier and the
  app-wide manifest still run; only the relay and the repair loop are skipped.
- **Contributing back is gated and curated**, never automatic.

## Consequences
- A covered feature costs **nothing** and finishes instantly — proven in the
  first slice: the booking package assembled with no model call at all.
- Cost becomes predictable *before* the build, because the plan already says
  which parts are free. The cost estimate wires directly onto this.
- Quality stops being per-run luck for the covered parts.
- The library must be maintained: entries drift from the framework, and a stale
  entry is worse than none. The strict file-plan equality check turns drift into
  a loud failure rather than a silent one.
- Curation is human work. That is the cost of the promise; automating it would
  fill the catalog with things nobody chose.
- Consistency across apps rises — the same button, the same validation shape —
  which is a feature for quality and a constraint on variety.

## Alternatives considered
- **Generate everything, always** (today's behaviour) — rejected: it is the
  expensive, least predictable path, and it throws away everything learned from
  every previous build.
- **Fuzzy/embedding matching on descriptions** — rejected for the first slice: a
  near-match that assembles the wrong feature is the worst failure this system
  can have. Canonical-vocabulary identity is checkable and explainable.
- **Let the model pick from the catalog** — rejected as the default: it is slower,
  costs a call per package, and is unpredictable. Kept only for genuine ties.
- **Automatic contribute-back after an approved build** — rejected: it grows the
  catalog fastest and destroys the guarantee that makes an entry worth assembling.
