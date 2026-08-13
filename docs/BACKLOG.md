# Backlog

> Task tracking now lives in docs/PROJECT-PLAN.md (authoritative). This backlog holds
> historical / cross-cutting items; "phase" refers to PROJECT-PLAN phases (PP) going forward.

| ID   | Item                                                     | Phase | Priority | Status      |
|------|----------------------------------------------------------|-------|----------|-------------|
| B001 | Scaffold repo + doc skeleton                             | 0     | P0       | done        |
| B002 | Run Phase 1: vision, scope & features                    | 1     | P0       | in progress |
| B003 | Record wedge decision as ADR-0001                        | 1     | P0       | done        |
| B004 | Feature brainstorm & prioritisation                      | 1     | P0       | in progress |
| B005 | Define MVP scope, non-goals, metrics                     | 1     | P0       | todo        |
| B006 | Spec customer journey (UX flow, steps 1-7)               | 1     | P0       | done        |
| B007 | Involvement levels (wizard only / wizard + design)       | 1     | P0       | done        |
| B008 | Behind-the-scenes engine: directed diff, marking->code   | 2     | P1       | todo        |
| B009 | Name decision: Scio (ADR-0002)                           | PP1   | P0       | done        |
| B010 | Visual identity (ADR-0003) + DESIGN.md tokens            | PP1   | P0       | done        |
| B011 | Full project plan -> docs/PROJECT-PLAN.md                | PP1   | P0       | done        |
| B012 | Documentation & checkpoint protocol                      | -     | P0       | done        |
| B013 | Stack decisions as ADRs (cloud, sandbox, be, db, auth)   | PP0.2 | P0       | done        |
| B014 | Logo (concept B, tile monogram) -> assets/logo           | PP1   | P0       | done        |
| B015 | Marketing site v1 -> apps/website                        | PP1   | P0       | done        |
| B016 | Phase 2: app shell + full visual (mocked)                | PP2   | P0       | done        |
| B017 | Implement prototype as real React app (apps/app)         | PP2   | P0       | in progress |
| B018 | Data model (ADR-0009 + DATA-MODEL.md)                    | PP3.1 | P0       | done        |
| B019 | Backend skeleton + API contract (NestJS)                 | PP3.2 | P0       | done        |
| B020 | Auth integration (Clerk)                                 | PP3.3 | P0       | done        |
| B021 | Project CRUD + persistence                               | PP3.4 | P0       | done        |
| B022 | Port remaining screens to React (step 2)                 | PP2   | P0       | todo        |
| B027 | Layer A: intake schema (doc, ADR-0010)                   | PP4   | P0       | done        |
| B028 | Build Layer A in engine (Pydantic + is_buildable)        | PP4   | P0       | done        |
| B029 | Layer B: understanding / architecture (design)           | PP4   | P0       | todo        |
| B030 | Layer C: build plan / decomposition (design)             | PP4   | P0       | todo        |
| B031 | Engine: scaffold + provider abstraction + matrix + multi-pass | PP4 | P0     | done        |
| B032 | Generated-app stack locked (ADR-0011)                    | PP4   | P0       | done        |
| B033 | Layer B: understanding/architecture (ADR-0012 + doc)     | PP4   | P0       | done        |
| B034 | Build Layer B in engine (arch graph + playbook + validate) | PP4  | P0       | done        |
| B035 | Layer C: build plan / decomposition (design)             | PP4   | P0       | done        |
| B036 | Product overview (synthesis doc)                         | PP4   | P0       | done        |
| B037 | Technical architecture (docs/ARCHITECTURE.md)            | PP4   | P0       | done        |
| B038 | Build Layer C in engine (the planner)                    | PP4   | P0       | done        |
| B039 | Sandbox + marking->code core (the shared hard part)      | PP6   | P0       | in progress |
| B040 | Build the real sandbox + marking->code core (per spike findings) | PP6 | P0   | done        |
| B041 | The builder: LLM generates each package into a working app | PP6 | P0      | done        |
| B042 | Builder: orchestrate the full plan (B041b)               | PP6   | P0       | done        |
| B043 | Wire the gates: engine <-> api <-> app + the real design window | PP6 | P0 | in progress |
| B044 | Strategy & moat doc (docs/STRATEGY.md)                         | PP4      | P0 | done |
| B045 | Component library — the growing asset (5 layers), the nave     | PP4      | P0 | todo |
| B046 | Cost estimate (deterministic, from plan + library hits)        | PP4      | P0 | todo |
| B047 | Fleet learning (capture fixes/patterns -> playbook + library)  | post-MVP | P1 | todo |
| B048 | Quality gate at reveal (Lighthouse + security + lint scores)   | PP9      | P1 | todo |
| B049 | Model-passes control in Settings (1 = same model x2; more = best->review->best) | PP4 | P0 | todo |
| B050 | Intake agent: extraction + next-question loop (gate 1's brain) | PP4 | P0 | done |
| B051 | Gate 1 wired end-to-end (wizard <-> api <-> engine, spec freeze) | PP5 | P0 | done |
| B052 | Wire the build + reveal end-to-end (step 3)                    | PP5 | P0 | todo |
