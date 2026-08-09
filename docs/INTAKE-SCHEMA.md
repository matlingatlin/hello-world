# Scio — Intake schema (Layer A, app type)

Layer A of three: **A (intake schema) -> B (understanding) -> C (build plan)**. This is the
checklist the wizard fills for the **app** type (website/automation get their own later).
Every field is a typed slot in the spec object with metadata and a downstream tag. This is
the contract the engine's extraction (4.3) fills; the gate is `is_buildable()`. See ADR-0010.

## Per-field metadata
Every field stores, not just a value:
- **value**
- **source** — stated | derived | default
- **confidence** — low | medium | high
- **provenance** — the wizard message(s) it came from

This is what powers the spec gate's "assumed" tags, surgical single-field edits, and traceability.

## Core fields (always required, unless defaulted-and-flagged)
1. **purpose** — "What does the app do?" (one sentence). _Ex: "Guests book a table and get a
   confirmation."_ → whole + scope
2. **users_and_roles** — "Who uses it? More than one kind of user?" _Ex: "Guests" / "guests +
   staff."_ → access rules, routing
3. **entities** — "The core things the app manages." _Ex: "bookings, tables, guests."_ → data model / schema
4. **key_actions** — "The MVP flows: what can users do?" _Ex: "book/cancel; staff see today's
   list."_ → functions + screens / routing
5. **sign_in** — "Do users sign in, and how?" _Ex: "No account — name + phone" / "email link"
   / "Google."_ → auth
6. **data_ownership_sensitivity** — "Who owns the data; anything sensitive (payment, personal,
   health)?" _Ex: "I own it; no payment data."_ → security defaults + compliance

## Conditional follow-ups (asked only when a trigger fires)
- multiple roles -> **role_permissions** (what each role sees/does) → access rules
- charges money / payment -> **payment** (provider + what's charged) → connectors + security
- notifications mentioned -> **notifications** (channel + trigger) → functions / connectors
- external integrations -> **integrations** (service + data) → connectors
- uploads / media -> **media** (file types, who sees them) → storage + access
- sensitive data -> **compliance** (consent, extra care) → security / compliance
- public content -> **visibility_seo** (public vs private, SEO) → functions / design
- multi-language / region -> **localization** (which) → functions
- time / scheduling logic -> **scheduling** (timezones, availability rules) → functions / data model

## Non-goals (always asked)
- **non_goals** — "Anything you deliberately want to skip, for now?" → scope guard (caps every
  area, so the build doesn't sprawl)

## Defaulted-and-flagged (assumed unless stated; shown as "assumed")
- **platform** → responsive web app
- **data_owner** → you
- **look** → Scio default (unless brand/colours are uploaded via reference RAG)
- **publishing** → a Scio URL first (custom domain later)
- **security_and_a11y** → secure defaults + accessible by default
- **scale** → small-to-moderate initially

## Downstream tag -> build area (how B and C consume the input)
- entities → data model / schema
- key_actions → functions + screens / routing
- sign_in → auth
- users_and_roles, role_permissions → access rules
- data_ownership_sensitivity, compliance → security defaults + compliance
- integrations, payment, notifications, media → connectors (+ storage)
- look, brand → design tokens (+ reference RAG, colour picker)
- non_goals → scope guard (all areas)

## "Buildable enough" rule (when the spec gate opens)
Buildable when ALL of:
- every core field is answered, or explicitly defaulted-and-flagged;
- every conditional branch triggered by the answers is resolved;
- there are no unresolved contradictions.
Not "every possible field" — momentum over completeness; the rest defaults and is refined
later, or on the running app.

## Notes
- Schema is **per type** (app now; website/automation later, each its own).
- The core is **fixed but extensible**: the six core fields are always present; conditional
  fields can be added over time without breaking existing specs.
- This is Layer A only. Layer B (understanding/architecture) and Layer C (build plan /
  decomposition) are defined next and consume this via the downstream tags.
