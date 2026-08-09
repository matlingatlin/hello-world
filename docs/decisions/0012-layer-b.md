# 0012. Layer B — understanding & architecture

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 4 (engine)

## Context
Layer B's real job is to manufacture the ideal **prompt substrate** so the engine builds
developer-grade in the first pass, and so multi-pass and the vision loop have something
concrete to check against. It is NOT a pretty summary. It consumes Layer A's fields +
downstream tags.

## Decision
Adopt docs/LAYER-B.md. Layer B produces three linked artifacts from Layer A, plus validation:
1. **The whole** — the human, coherent understanding shown at the spec gate (the frozen
   contract the user approves).
2. **A machine-readable architecture graph** — derived from Layer A's downstream tags.
3. **The generation playbook** — the fixed "house rules" every build prompt carries.
Method: deterministic-first (rules do what rules can guarantee); LLM only for judgment
(grounded, additions flagged "assumed"); canonical vocabulary; small contract-bearing slices;
the contracts act as shared context across the four passes. Validate the architecture with
rule checks *before* any code is generated.

## Consequences
- First-pass output is reliable and developer-grade; multi-pass review becomes concrete
  ("does this match the agreed architecture?") instead of vague.
- Design errors are caught before the expensive vision loop.
- The architecture graph is what Layer C decomposes and the vision loop checks against.

## Alternatives considered
- Prose-only architecture — rejected; not machine-consumable or decomposable.
- LLM-only understanding without deterministic rules — rejected; loses the developer-grade guarantee.
