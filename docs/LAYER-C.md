# Scio — Layer C: build plan / decomposition

Layer C of three: **A (intake) -> B (understanding/architecture) -> C (build plan)**. It takes
Layer B's architecture graph + generation playbook and decomposes them into a dependency-ordered
graph of small, contract-bearing build packages that the builder takes one at a time. This is what
makes the build professional (not spaghetti), and it underpins marking->code, directed
regeneration, cost control, and failure isolation. See ADR-0013.

## What a build package is (the contract)
The smallest unit the builder produces in one focused pass, with a tight contract:
- **goal** — what this package builds
- **architecture slice** — the nodes it owns (e.g. the booking table + its operations + its screen)
- **dependencies** — what already exists that it may lean on: prior packages' *interfaces /
  contracts*, NOT their full code (this keeps context tight)
- **why** — the relevant slice of the whole (keeps the package aligned with intent)
- **house rules + canonical vocabulary + scope guard** (non-goals)
- **acceptance criteria / "done when"** — testable; this is the vision loop's and the tests' target

## How decomposition works (deterministic-first)
Rules group the architecture nodes into packages:
- **foundation** — scaffold the locked stack (ADR-0011)
- **schema** — Supabase tables + RLS
- **auth** — sign-in / access setup
- **one package per feature** — an entity's operations + its screen
- **connectors** — integrations / payment / notifications
- **design tokens**
The LLM (via the relay) is used ONLY for judgment where grouping is genuinely tricky — grounded.

## Dependency ordering
Packages have dependencies (schema before operations before screens; auth before protected screens;
foundation first). A **topological sort** gives the build sequence. Independent features can run in
parallel; MVP runs sequentially.

## Validate the plan before building
- every architecture node is covered by some package (nothing dropped)
- the graph is acyclic (no dependency cycles)
- every package has a valid contract
Catch plan errors here, before a line of code is generated.

## Granularity
**Per feature** — an entity's operations + its screen as one package — plus foundation, schema,
auth, and tokens as their own. Not per file (too fine, loses context), not per app (too coarse,
loses the tight context that makes LLM output good).

## How it ties everything together
- Package boundaries + the architecture slice = the **marking->code mapping**: a later change lands
  in the right package, so we regenerate only it.
- The per-package **why** keeps the whole intact.
- Small packages = tight context = **cheaper**, better output, and tractable directed diff + vision
  loop; the relay can run more passes on hard packages and fewer on trivial ones.
- A build **failure isolates** to one package.

## Notes
- Consumes Layer B; feeds the builder + the vision loop.
- Per type (app first); the same decomposition idea applies to website (lighter) and automation
  (flow steps as packages) later.
