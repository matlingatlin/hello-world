# Scio — Layer B: understanding & architecture

Layer B of three: **A (intake) -> B (understanding/architecture) -> C (build plan)**.
Its job is to manufacture the ideal **prompt substrate**: everything in B is chosen to
(1) shrink what the LLM must invent, (2) make what it does invent controllable, and
(3) keep the context per build-package small and exact. It consumes Layer A (fields +
downstream tags) and produces three linked outputs plus validation. See ADR-0012; the
generated-app stack it targets is ADR-0011.

## Output 1 — The whole (human understanding)
The coherent, human narrative shown at the spec gate: the user's vision retold, organised,
gaps reasonably filled (flagged "assumed"), the unspoken made explicit. Grounded in Layer A's
fields; the LLM organises and articulates, it does not invent. This is the frozen contract the
user approves.

## Output 2 — Architecture (a machine-readable graph)
Not prose. A typed graph, each node derived from Layer A's downstream tags and each node
sliceable (this is what Layer C decomposes and the vision loop checks against):
- **data model** — entities -> tables / fields / relations
- **auth + access** — sign_in -> auth; roles -> RBAC / access rules
- **screens / routing** — actions -> UI + navigation
- **operations** — actions -> typed operations with inputs/outputs
- **connectors** — integrations / payment / notifications
- **security posture** — sensitivity -> secure defaults / row-level security
- **design tokens** — look / brand (+ reference RAG)

## Output 3 — The generation playbook (house rules)
The fixed rules every build prompt carries — the single biggest "prompt the AI best" lever,
because it turns "build X" into "build X the Scio way" (consistent, developer-grade across
every app AND every pass):
- the locked stack (ADR-0011: Next.js + TS + Tailwind + Supabase)
- folder structure, file/naming conventions
- secure-by-default patterns (RLS, input handling, authz)
- tests expected, accessibility expected

## Validate the architecture before generating
Rule checks that catch design errors far more cheaply than the vision loop would:
- every action hits a valid entity
- every permission maps to a valid action
- no "no-login" + "user-specific data / roles" conflict
- foreign keys / relations resolve
Unresolved -> back to the wizard, surgically.

## Method (how best results are secured)
- **Deterministic-first; LLM only for judgment.** Rules do what they can guarantee (entities
  -> schema; no sign-in -> no auth tables, name/phone instead; roles -> RBAC skeleton). The
  LLM weaves the whole into prose, structures flows/components, and catches subtle
  contradictions — always grounded; anything it adds is flagged "assumed".
- **Fixed target stack** (ADR-0011) — the largest reliability multiplier.
- **Canonical vocabulary** — normalise the user's terms into one consistent name set, used in
  every prompt and all generated code (fewer bugs, more shared context).
- **Small, contract-bearing slices** — the architecture is a graph, so each build package gets
  only its slice + the relevant "why": tight context, exactly where LLMs are strongest. This
  is also what makes directed diff and multi-pass review tractable.
- **Contracts as shared context across the four passes** — pass 1 builds against architecture +
  contracts + playbook; passes 2–4 review against the *same* contracts, so "review and improve"
  becomes "does this match the agreed architecture?".

## Notes
- Consumes Layer A; feeds Layer C.
- The whole (Output 1) is the frozen spec contract the user approves at the gate.
- Hybrid rule/LLM throughout; the LLM never invents unflagged.
