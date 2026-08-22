# Scio — Technical architecture

How the product (docs/PRODUCT-OVERVIEW.md) is built: the services, the agents, the model
orchestration, the shared core, and how a project flows through the three gates. Detail lives in
PRD, UX-FLOW, DATA-MODEL, INTAKE-SCHEMA, LAYER-A/B, and the ADRs; this is the system-level picture.

## 1. Topology (services)
- **apps/app** — React + TS + Vite + Tailwind; Clerk login. The UI, including the design window.
- **apps/api** — NestJS. Auth (Clerk verify), workspaces, projects, versions, uploads, metering,
  notifications; orchestrates jobs; streams engine output to the client (SSE). Owns the DB.
- **apps/engine** — Python + FastAPI. The brain: A->B->C, the matrix + multi-pass relay, the
  agents, reference RAG.
- **Sandbox** — Azure Container Apps dynamic sessions, custom container (ADR-0005). Runs each
  project's generated code (preview + final) and streams it back. Behind a swappable interface.
- **Data plane** — Postgres (+ pgvector), object storage (uploads), git (version code), Azure
  secrets (keys/tokens). Git holds code; the DB holds contracts/state/metadata.

Request shape: app -> api (authz, persistence, job) -> engine (brain) -> sandbox (run) -> stream
back up to app. The api coordinates, the engine is the intelligence, the sandbox is the muscle.

## 2. The agents (the engine is agent-based)
Each agent has one job and runs on the matrix + multi-pass relay (it declares a task type and gets
the best models). An **orchestrator** sequences agents per gate and enforces the contracts between
them. Agents hand each other **contracts**, not raw output — that is what keeps the whole coherent
and makes multi-pass review concrete.

- **Intake agent** (gate 1). Runs the conversation against the Layer A checklist: extracts each
  answer into the typed spec (metadata + provenance), picks the next question from what's still
  missing/triggered, and produces the refined "if I understood you right" confirmation.
- **Architect** (gate 2, Layer B). Deterministic derivation (rules) + LLM judgment -> the whole,
  the machine-readable architecture graph, and rule validation before anything generates.
- **Planner** (gate 3, Layer C). Decomposes the architecture graph into a dependency-ordered graph
  of small, contract-bearing build packages; validates the plan (full coverage, acyclic).
- **Design agent** (gate 2). Generates the runnable preview from the architecture; interprets
  prompt + marking changes; performs *directed* regeneration (only annotated packages), preserving
  the rest; flags conflicts with the contract.
- **Builder agent** (gate 3). Builds each package in plan order against its contract (goal +
  architecture slice + dependencies' interfaces + why + house rules + "done when").
- **Vision / critique agent** (the loop). Renders a package in the sandbox, takes screenshot +
  console, critiques against the contract, drives fixes until it passes or hits the cap.
- **Validation agents** (background, always on). Spec-completeness, contract-consistency (matches
  the whole + design), security review, code-quality/lint, test-presence. They gate progress and
  feed fixes back.

No agent calls a model directly — all LLM work goes through the relay.

## 3. Model orchestration (built, B031)
- **Matrix** — matrix.yaml maps task types (spec_extraction, architecture, codegen, review, fix,
  design, light_edit) to ranked models with strength/cost/latency/context; `top_n` selects. Data,
  not code (rankings change monthly).
- **Multi-pass relay** — pass 1 (best) -> review/rewrite/complement passes -> final pass (best),
  structured hand-off, configurable pass-count per task (hard cap 4). Hard packages get more passes,
  trivial ones fewer.
- **Providers** — Anthropic / OpenAI (via Azure OpenAI) / Google behind a ModelProvider interface,
  plus a FakeProvider for tests. Keys via Azure secrets.
- **Cost is enforced here:** pass-count + directed regeneration (never rebuild the unchanged) +
  the budget (metering -> warn -> pause).

## 4. The shared core (one implementation, all gates)
- **A -> B -> C** (A + B built; C next) — the brain every gate runs on.
- **Sandbox** — runs the runnable preview (gate 2) and the final app (gate 3): the same service.
- **Marking -> code coupling** — every element maps to its build package/code, saved with the
  project (git + DB) so it survives sessions. Powers directed regeneration in preview, build, AND
  post-delivery editing. The hardest single piece.
- **Vision loop** — build -> run -> critique -> fix, per package; shared by build and directed edits.

## 5. Gate flow, end to end
1. **Gate 1 (input).** app -> api creates/loads the project; the intake agent fills the Layer A
   spec; is_buildable opens the spec gate; approval freezes the spec contract (spec_version).
2. **Gate 2 (preview/design).** The architect builds the whole + architecture (+ validation); the
   design agent generates real code, run in the sandbox, shown in the design window; marking/prompt
   changes -> directed regeneration, conflicts flagged; approval freezes the design contract
   (design_version). Type-aware: visual surface for app/website, flow surface for automation.
3. **Gate 3 (build).** The planner decomposes into packages; the builder builds each in order; the
   vision + validation agents verify each against its contract; failures isolate to a package and
   are surfaced honestly. The full app runs, testable, in the design window (build_version + git_sha).
4. **Packaging.** Publish (Scio URL -> domain -> own infra) and/or own (clean code to GitHub +
   living docs). The code was clean and exportable throughout.
What crosses each boundary is the **contract + code**, never a picture — so the final product
matches what was approved, by construction.

## 6. Data & persistence
- **git** — the version code (real, ownable history; git_sha per build_version).
- **Postgres** — workspaces, users, projects, spec/design/build versions, deployments, usage,
  notifications, audit; the contracts + the marking->code coupling metadata.
- **pgvector** — reference embeddings (RAG), owned/queried by the engine.
- **object storage** — uploaded reference assets.
- **Azure secrets** — API keys, tokens; never in the DB or git.

## 7. Cross-cutting: security & cost
- **Security** — two different things, said separately because one sentence covering both has
  already misled one reader:
  - *In the apps we generate*: row-level security is part of the locked stack (every generated
    table gets RLS with explicit policies — it is an acceptance criterion of the schema package),
    plus secure defaults from the playbook, a posture derived from the sensitivity field, and the
    security validation agent + vision loop checking it.
  - *In our own platform*: tenant isolation is **application-layer**, not database RLS. A Prisma
    `$extends` client (`auth/workspace-scope.ts`) stamps and filters `workspace_id` on the scoped
    models and **fails closed** on any operation it does not recognise. Child rows — spec, design
    and build versions, messages — are reached only through a project the scoped client already
    resolved, so their safety is a *discipline*, enforced by a test that fails if a service touches
    them on the raw client (`test/tenant-discipline.spec.ts`). Postgres RLS on our own tables is a
    backstop we do not have yet; until we do, that test is the fence.
- **Cost** — pass-count + directed regeneration + caching (LLM); idle timeout + concurrency caps
  (sandbox); estimate at the spec gate + live counter + pause at the cap (budget).

## 8. Type-awareness
Everything is shared except **gate 2's preview surface** (and a little agent behaviour): visual +
marking->code for app/website; a flow map + step-editing + sample-run for automation. Build app
first; keep the core type-agnostic so website (a lighter app) and automation (a later, larger
effort) slot in without rebuilding the brain.

## 9. Built vs to build
- **Built:** marketing site + brand; api (auth, tenant isolation, project CRUD, versions in the
  data model); app shell (projects end-to-end); engine scaffold + Layer A + execution machinery
  (matrix + multi-pass + providers) + Layer B (architecture graph, the whole, playbook, validation).
- **To build, in order:** Layer C (planner) -> the sandbox + marking->code core (the shared hard
  part) -> the builder + vision loop -> wire the gates (engine <-> api <-> app) -> the design window
  for real -> packaging/deploy -> then website, then automation.
