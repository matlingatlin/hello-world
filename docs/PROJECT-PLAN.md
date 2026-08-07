# Scio — Total Project Plan

**Scio** (Latin: "I know") is an AI app builder for founders and small teams building
software they intend to run and grow. Differentiator: developer-grade output — clean,
tested, secure-by-default, git-native code the user owns. MVP targets the **app** path.

This is the complete plan from scratch to launch, broken into phases -> steps -> tasks.
It is progressively elaborated: each task explodes into its own micro-tasks when we open
that step, so we don't over-specify the far future now.

---

## How we work (the rhythm)
- **Plan here** (this chat = PM/architect: decisions, specs, doc content) -> **build in
  Claude Code** (the hands: writes code, runs git) -> **test** -> **checkpoint** to the
  repo. One phase/step at a time.
- **Doc-driven:** decisions land in `docs/` + ADRs before code. Nothing lives only in chat.
- **Build -> test -> loop:** nothing is "done" until it's tested and works. If a test
  fails, loop and fix until green. This is a rule for us AND a built-in product behavior.

## Cross-cutting principles (true in every phase)
1. **Never lose the whole.** The project's whole is a persistent anchor; every step and
   change is checked against it, down to the code (directed edits, preserve the rest).
2. **Refine, don't parrot.** Confirmations restate intent better than the user did;
   assumptions are marked and correctable.
3. **The engine is a matrix + multi-pass relay** (see Phase 4) — Scio's signature way of
   prompting.
4. **Security and cost are first-class from day one**, not bolted on at the end.
5. **Honest status everywhere** — known remainders are shown, never hidden.

## Legend
Each phase lists: **Goal**, **Deliverable**, **Done when** (the test), **Track** (can it
run in parallel). Status: [ ] todo · [~] in progress · [x] done.

---

## Phase 0 — Foundations & setup
**Goal:** a repo and toolchain we can build in, and the big technical choices made.
**Deliverable:** working monorepo + tooling + stack ADRs. **Done when:** `hello` app
builds, lints, tests, and CI runs green on a push. **Track:** must go first.

**0.1 Repo & tooling**
- [ ] Monorepo layout (`apps/`, `packages/`, `docs/`, `infra/`), package manager (pnpm).
- [ ] TypeScript config, ESLint + Prettier, test runner (Vitest), Git hooks.
- [ ] CI skeleton (lint + test on PR), branch strategy, PR-per-phase.
- [ ] Env & secrets convention (`.env`, secret manager placeholder), `.gitignore`.

**0.2 Stack decisions (ADRs — decide, don't build)**
- [ ] Frontend: React + TS + Vite + Tailwind (confirm). Desktop wrapper deferred.
- [ ] Backend language/framework (e.g. Node/TS + Fastify or similar).
- [ ] Database (e.g. Postgres) + ORM; object storage; secrets manager.
- [ ] Sandbox provider for running generated apps (E2B / Modal / Firecracker) — spike.
- [ ] Cloud (Azure vs AWS) — decide, with cost/sandbox fit as the deciding factors.
- [ ] Auth provider (managed, e.g. Clerk/Auth0/Supabase Auth) — don't hand-roll.
- [ ] LLM providers + access (Anthropic / OpenAI / Google) and the Agent SDK for the engine.

**0.3 Existing groundwork**
- [ ] Fold in what's already in the repo (CLAUDE.md, ROADMAP, PRD, UX-FLOW, ADR-0001).

---

## Phase 1 — Brand & website
**Goal:** Scio has a face and a place on the web. **Deliverable:** logo + design tokens +
live marketing site. **Done when:** site is deployed, responsive, passes Lighthouse basics.
**Track:** parallel with Phase 2 once tokens are set.

**1.1 Logo & brand kit**
- [ ] Concept from meaning: "I know" / understanding / a mark that reads as clarity or a
      keel/structure. 3 directions.
- [ ] Produce logomark + wordmark (Space Grotesk lockup), light/dark, favicon, spacing rules.
- [ ] Trademark/domain screen for "Scio" before locking (name currently a working choice).

**1.2 Design tokens (from the drafting-table profile)**
- [ ] Encode palette, type, radius, spacing as CSS variables + a shared tokens package.
- [ ] Tailwind config consuming the tokens (single source of truth for app + site).

**1.3 Marketing website**
- [ ] Research competitor sites (Lovable, v0, Bolt, Replit, Cursor): map common sections
      — hero, "what it is", how-it-works, proof/examples, pricing, docs, CTA, social proof.
- [ ] Information architecture + copy (write from the user's side; sell the differentiator).
- [ ] Build (static/SSR), wire waitlist/sign-up CTA, analytics, SEO/meta.
- [ ] Deploy (CDN/static host). Placeholder pricing until Phase 12.

---

## Phase 2 — App shell & full visual (clickable, mocked)
**Goal:** the entire app, every screen, clickable with fake data — no engine yet.
**Deliverable:** a click-through prototype of the whole product. **Done when:** you can
walk the full journey + all support screens end-to-end; a usability pass is done; MVP
screen-scope is locked by seeing it. **Track:** core; needs 1.2 tokens.

**2.1 Scaffold & design system**
- [ ] Scaffold `apps/app` (React+TS+Vite+Tailwind) with tokens wired.
- [ ] Component library: buttons, inputs, panels, cards, chips (honest-status), modals,
      toasts/notifications, tooltips, tabs, empty states, skeletons/loaders, the number
      annotation tiles, the wholeness panel, the drafting/construction-line motif, the asset
      upload + tagging control.

**2.2 Main-flow screens (mocked)**
- [ ] Home / project list (project-first).
- [ ] Create -> type select (hybrid: prompt line + type cards; app active, rest greyed).
- [ ] Wizard: guided conversation + live wholeness panel.
- [ ] Spec gate: refined confirmation, assumptions marked, yes/no + clarify loop.
- [ ] Involvement choice (wizard-only vs wizard+design).
- [ ] Design preview + numbered annotation + "changes" list + Update (Level 2).
- [ ] Build view: calm graphic, non-blocking, background + notification states.
- [ ] Reveal: running-app placeholder, "what you built", trust receipt, honest status.
- [ ] Live feedback: running app inside Scio + numbered annotation on it.
- [ ] Versions: timeline, preview a version, safe rollback.
- [ ] Ownership/export: get-your-code, GitHub, handoff package, living doc.
- [ ] Publish: one-click URL + own-infra option.

**2.3 Everything around the main flow (you asked for these)**
- [ ] Auth screens: sign up / in / out, reset, verify.
- [ ] Account & billing (mocked plans/usage).
- [ ] Settings: profile, appearance (light/dark), model/engine preferences, connections.
- [ ] **Error screens & states:** generation failed, build failed, sandbox timeout,
      network/offline, model unavailable, quota exceeded, not-found, permission denied,
      empty project, first-run.
- [ ] **System messages/notifications:** build done, needs-a-look, rate-limit warning,
      cost warning, update available.
- [ ] Help/onboarding tips, keyboard shortcuts, command palette (optional).

**2.4 Wire it**
- [ ] Navigation + app state with a fake data layer (swappable for the real API later).
- [ ] Quality floor: responsive, keyboard focus, reduced-motion, a11y pass.

---

## Phase 3 — Backend foundations & auth
**Goal:** real accounts and persistent projects. **Deliverable:** API + DB + auth.
**Done when:** sign up, create a project, reload — it persists; authz blocks other users.
**Track:** after 0.2.

- [ ] Backend service skeleton + API contract (typed, shared with frontend).
- [ ] DB schema: users, projects, specs, versions, files, usage/metering, audit.
- [ ] Object storage + secrets manager wiring.
- [ ] Auth via the chosen provider; sessions; per-user authorization.
- [ ] Project CRUD; streaming channel (SSE/websocket) for later engine output.
- [ ] Replace the frontend's auth + project mocks with the real API.

---

## Phase 4 — The AI engine: matrix + multi-pass relay  (the heart)
**Goal:** Scio's signature prompting engine, callable in isolation. **Deliverable:** an
engine package with a test harness. **Done when:** sample tasks run the full matrix +
multi-pass + validation, with cost/latency within set caps. **Track:** core; after 3.

**4.1 Capability matrix**
- [ ] A registry mapping task types (spec-extraction, design, codegen, review, fix, ...)
      to ranked models, with metadata (strength, cost, latency, context limit).
- [ ] Selector: given a task, return the top 3 models.
- [ ] The transparency narration generator (user-facing): "I'll run this prompt N times —
      first in X; then take that result into Y to review, rewrite and complement; then
      into Z; then a final pass back in X."
- [ ] Matrix is data-driven and updatable (rankings change monthly).

**4.2 Multi-pass relay pipeline**
- [ ] Pass 1: run in the best model.
- [ ] Pass 2: feed prompt + result into 2nd model; instruct: review, rewrite if needed,
      complement.
- [ ] Pass 3: same into 3rd model.
- [ ] Pass 4: final pass back in the best model.
- [ ] Streamed to the UI; each pass visible; **pass-count configurable per task** (cost).
- [ ] Structured I/O between passes (so results are diffable, not free text where it matters).

**4.3 Requirements extraction**
- [ ] Wizard answers -> typed spec object + wholeness object (per-type schema).
- [ ] Validation: gaps, contradictions -> drives the next question.
- [ ] Refined-confirmation generation (assumptions marked vs stated).
- [ ] Freeze approved spec/whole as a versioned contract.

**4.4 Validation agents (background)**
- [ ] Agent set: spec-completeness, contract-consistency (matches the whole + design),
      security review, code-quality/lint, test-presence.
- [ ] Orchestration: run agents on outputs, aggregate a verdict, feed fixes back into 4.2.

**4.5 Cost & latency controls**
- [ ] Per-task budgets, iteration caps, prompt caching, cheap-model routing for light steps.
- [ ] Usage metering hooks (per user/project) for Phase 8/12 billing.

**4.6 Reference RAG (multimodal, tagged)**
- [ ] Upload documents, images, etc. — in the wizard (Phase 5) and the design tool (6.3).
- [ ] On upload, tag each asset with what it represents (colour, font, layout/style reference,
      content/requirements doc, brand asset, ...).
- [ ] Extraction per tag: pull the hex palette from a "colour" image; identify/approximate the
      font from a "font" sample; extract text/structure from a doc; capture cues from a screenshot.
- [ ] Index into a per-project reference store (object storage + vector index); tenant-isolated.
- [ ] Retrieval: the engine pulls relevant references during spec-building, design, and codegen —
      so users can *show* intent (a colour, a font, an example) instead of describing it.
- [ ] Extracted attributes feed the shared brand-token layer and the wholeness/contracts.
- [ ] MVP-lite: images tagged colour/font with extraction feeding tokens/design; full document
      RAG is a later expansion (scope-cut decides the line).

---

## Phase 5 — Intake vertical slice (real)
**Goal:** a real, approved spec from a real conversation. **Deliverable:** wizard wired to
4.3. **Done when:** a full guided conversation yields a valid frozen spec contract, with
the live wholeness panel and refined confirmation working. **Track:** after 4.

- [ ] Connect wizard UI -> extraction engine; live wholeness panel from real data.
- [ ] Spec-gate contract freeze + clarify loop (surgical edits).
- [ ] Involvement choice persisted.

---

## Phase 6 — Sandbox, code generation & preview
**Goal:** spec -> a real running app you can see and steer. **Deliverable:** sandbox +
codegen + previews. **Done when:** a simple app generates, runs in preview, and a numbered
annotation regenerates only the marked part while the rest stays intact. **Track:** after 5.

**6.1 Sandbox**
- [ ] Per-project isolated sandbox on the chosen cloud/provider; run a dev server; stream preview.
**6.2 Code generation**
- [ ] Codegen from approved spec using fixed-stack templates + the engine.
- [ ] Directed/incremental diff + marking->code coupling (stable IDs / AST mapping).
**6.3 Design stage (Level 2)**
- [ ] Design generation + preview surface; numbered annotation -> directed regeneration (batch).
- [ ] **Smart property controls:** click an element -> engine resolves the governing code
      attribute(s) -> surfaces an inline control (colour picker, font selector, size/spacing
      slider, toggle) bound live to that attribute. Extends marking->code coupling. Whole-aware:
      offers "just here vs everywhere this is used" (edit the design token). MVP-lite for common
      attributes (colour/font/size/spacing); full/any-attribute is a fast-follow.
- [ ] Attach + tag reference assets here too (see 4.6) — feeds the token layer and property controls.
- [ ] Feasibility check before preview; design-gate contract freeze.
**6.4 Live preview**
- [ ] Running app inside Scio; numbered annotation on the running app -> directed regen.

---

## Phase 7 — Self-testing vision loop + build/reveal
**Goal:** builds that test and correct themselves, revealed honestly. **Deliverable:** the
loop + build view + reveal. **Done when:** builds run the loop, catch and fix real issues,
and the reveal's status matches reality. **Track:** after 6.

- [ ] Vision loop: generate -> render -> screenshot + console -> critique against the two
      contracts -> fix -> repeat (capped by 4.5).
- [ ] Build view UX (calm graphic, background run, notification on done).
- [ ] Reveal + trust receipt + honest status (surfaces validation + loop results).

---

## Phase 8 — Versions, ownership/export, publish
**Goal:** the full lifecycle after first build. **Deliverable:** versions + export + publish.
**Done when:** version, rollback, export to GitHub, and publish-to-URL all work end-to-end.
**Track:** after 7.

- [ ] Version timeline (git under the hood), plain-language entries, safe rollback.
- [ ] Ownership: clean repo, get-your-code (GitHub push + zip), handoff package, living
      spec/architecture doc that travels with the code.
- [ ] Publish: one-click URL + publish-to-own-infra/domain.

---

## Phase 9 — Security hardening
**Goal:** safe for real users and untrusted generated code. **Deliverable:** security review
passed. **Done when:** threat-model controls implemented; scans clean; isolation tests pass.
**Track:** hardens Phases 3–8; some tasks run alongside them.

- [ ] Threat model -> controls doc (update `docs/SECURITY.md`).
- [ ] Tenant isolation (data + sandbox); sandbox escape hardening.
- [ ] Prompt-injection defenses in the engine; secret handling.
- [ ] Uploaded-reference handling: file-type/size validation, malware/content scanning,
      tenant-isolated RAG retrieval.
- [ ] Secure-by-default in generated apps (authz, input handling, RLS-equivalent).
- [ ] Rate limiting / abuse / cost-exhaustion protection.
- [ ] Dependency & SAST scanning in CI (use established tools/packages); pen-test pass.

---

## Phase 10 — Cloud infra, observability, cost, CI/CD
**Goal:** a deployable, observable, cost-governed platform on Azure/AWS. **Deliverable:**
IaC + pipelines + dashboards. **Done when:** staging + prod deploy from CI; logs/metrics/
traces and cost dashboards live with budget alerts; sandboxes scale. **Track:** after 0.2;
built out through 6–8.

- [ ] Infrastructure-as-code (Terraform/Bicep): DB, storage, secrets, queues, CDN, sandbox infra.
- [ ] Environments: dev / staging / prod; CI/CD deploy pipelines.
- [ ] Observability: structured logs, metrics, tracing, error tracking.
- [ ] Cost: usage + spend dashboards, budgets, alerts, autoscaling with caps.

---

## Phase 11 — Integration test & closed alpha
**Goal:** the whole thing works together, with real users. **Deliverable:** green E2E +
alpha feedback. **Done when:** full-journey E2E passes, load test holds, bug bash cleared,
alpha users can build real apps. **Track:** after 8 (+ 9/10 in place).

- [ ] End-to-end tests across the full journey (the build->test->loop discipline as automated E2E).
- [ ] Load / stress testing; failure-mode testing (sandbox, model outages).
- [ ] Onboarding polish; bug bash; closed alpha; structured feedback loop.

---

## Phase 12 — Launch prep
**Goal:** public launch. **Deliverable:** billing + legal + go-to-market live. **Done when:**
paid sign-up works end-to-end and rollout is gated/monitored. **Track:** last.

- [ ] Billing & live metering; pricing; quotas.
- [ ] Legal: ToS, GDPR, IP/ownership of generated code, EU VAT.
- [ ] Website final (real pricing), docs, support, status page.
- [ ] Gradual rollout with monitoring.

---

## Post-MVP / future capabilities
Captured now so they're not lost; built after the app MVP.

- **Full brand-system generation.** Once the website type exists, offer a "full branding +
  app" mode: generate a cohesive identity — palette, logo, website, and app — that all share
  one brand. Value is cohesion (the "whole" applied to identity). Depends on: the
  website-building type, logo/palette generation, and a shared brand-token layer feeding every
  artifact. (This is Scio doing for users what Phase 1 does for Scio by hand.)
- **Shared brand/design-token layer (bridge).** Both the smart property controls (6.3) and
  full brand-system generation rest on one token layer: property controls edit a token; brand
  generation produces the whole token set. Build the token layer well and both come cheaper.
- Other future ideas land here.

## Sequencing & reality notes
- **Parallel tracks:** Brand/website (Phase 1) runs alongside the app shell (Phase 2) once
  tokens exist. Security (9) and infra (10) are partly continuous, not just late phases.
- **The heart is Phase 4 + 6–7.** The matrix/multi-pass engine, the sandbox, and the
  vision loop are where this product is won or lost — budget the most time there.
- **The 4-pass relay is powerful but expensive and slow:** it roughly multiplies token
  cost and latency per generation. Keep it configurable — use the full relay for
  high-stakes generations, fewer passes for small edits — or cost/UX will suffer.
- **Marking->code coupling on a running, stateful app** (6.4) is the hardest single piece;
  de-risk it with a spike early.
- **This is a multi-month build**, not a weekend. The plan is designed so each phase is a
  usable, testable checkpoint — you always have something that works.

## Immediate next 3 actions
1. Phase 0.2 stack decisions (I draft ADRs: cloud, sandbox, backend, DB, auth) — these
   unblock almost everything.
2. Phase 1.1/1.2 in parallel: lock the logo direction + finalize design tokens.
3. Then Phase 2: scaffold the shell and start building screens (your "app visual").
