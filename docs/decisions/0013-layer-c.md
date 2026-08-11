# 0013. Layer C — build plan / decomposition

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 4 (engine)

## Context
Layer B produces the architecture graph + generation playbook. To build professionally (not
spaghetti), the LLM must build from small, well-bounded, well-defined packages — not "build the
whole app." Layer C is that decomposition. It is also what makes marking->code mapping, directed
regeneration, cost control, and failure isolation work.

## Decision
Adopt docs/LAYER-C.md. Layer C decomposes Layer B's architecture graph into a **dependency-ordered
graph of small, contract-bearing build packages** the builder takes one at a time. Each package
carries: goal; the architecture slice it owns; dependencies (prior packages' interfaces/contracts,
not their full code); the relevant "why" slice of the whole; house rules + canonical vocabulary +
scope guard; and acceptance criteria ("done when" = the vision loop's + tests' target).
Decomposition is deterministic-first (rules group nodes: foundation -> schema -> auth ->
one-package-per-feature -> connectors -> tokens), a topological sort gives the build sequence, and
the plan is validated (full coverage, acyclic, valid contracts) before building. Granularity: per
feature.

## Consequences
- Package boundaries + the architecture slice ARE the marking->code mapping — a later change lands
  in the right package, so regeneration is directed.
- The per-package "why" keeps the whole intact across the build.
- Small packages = tight context = cheaper, better LLM output, and tractable directed diff +
  vision loop.
- A failure isolates to one package (not the whole app).

## Alternatives considered
- Per-file granularity — rejected; too fine, loses coherence and context.
- Per-app ("build it all at once") — rejected; too coarse, loses tight context (the failure mode
  we exist to fix).
- No plan validation — rejected; design errors would slip into code generation.
