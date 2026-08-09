# 0010. Intake schema (Layer A)

- **Status:** Accepted
- **Date:** 2026-08-07
- **Phase:** 4 (engine · intake)

## Context
The wizard must capture *enough*, *structured* information to drive two things downstream:
understanding the whole (Layer B) and decomposing the build (Layer C). Blank-prompt builders
fail because their input is an unstructured blob; Scio's differentiator starts in the input.
We need three things: a checklist (completeness), typed storage (editability + downstream
use), and an explicit "enough" threshold.

## Decision
Adopt the intake schema in docs/INTAKE-SCHEMA.md. Key choices:
- **Three layers:** A (intake schema, this) -> B (understanding) -> C (build plan). This ADR
  is Layer A.
- **Six core fields** (always) + **conditional follow-ups** (only when triggered) + **non-goals**.
- **Every field carries metadata:** value, source (stated | derived | default), confidence,
  and provenance (which wizard message it came from).
- **Every field is tagged with the downstream build area it feeds** (data model,
  functions/routing, auth, access rules, security/compliance, connectors, design tokens).
- **"Buildable enough" gate:** all core fields answered or explicitly defaulted-and-flagged;
  every triggered conditional branch resolved; no unresolved contradictions. Not "every
  possible field" — momentum over completeness.
- **Per-type** schema (app first); the core is **fixed but extensible**.

## Consequences
- Metadata enables the honest "assumed" tags, surgical edits (update one field), and traceability.
- Downstream tags make Layer B (architecture) and Layer C (build decomposition) possible.
- Non-goals enforce scope, keeping the build (and cost) in check.
- The completeness rule is explicit and testable (is_buildable), not a vibe.

## Alternatives considered
- A single free-text blob — rejected; that is the failure mode we exist to fix.
- Flat field values without metadata — rejected; no honest tagging, no surgical edits, no provenance.
