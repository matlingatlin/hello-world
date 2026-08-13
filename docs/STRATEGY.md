# Scio — Strategy, moat & open ideas

Everything we've refined and proposed for making Scio a serious, higher-quality competitor to
Lovable: the user flow (with gaps), the connecting pieces still to build, and the bigger ideas
that make Scio structurally better and cheaper. Complements PRODUCT-OVERVIEW.md (the product
model) and ARCHITECTURE.md (the system). Not all of this is MVP — see "Sequencing".

## A. The user flow, start to now (status + gaps)
1. **Open app -> Projects.** Built + wired (Clerk + projects, real).
2. **New project -> type select.** Built. A light DB write (project: type, status=draft) + load the
   type's intake schema. Cheap; no engine, no cost yet.
3. **Intake agent (conversation -> filled spec).** Designed; NOT built. [gap]
4. **Review screen** (understood-right + spec + cost estimate -> adjust / not now / build).
   Prototype done. The cost calculation is unresolved. [gap]
5. **Planner (Layer B -> C).** Built — but must be extended for the library (library matching
   BEFORE the build plan).
6. **Build (package-by-package + vision loop).** Built (fake-driven). Needs explicit "generate to
   preview first, then finish fully after approval" staging.
7. **Build view (estimate + schedule, ticked off live).** Screen exists; the live tick-off + the
   time estimate aren't wired.
8. **Design window** (preview -> prompt/tools -> change/approve -> cheap directed update). Prototype
   + marking->code built. Toolset to complete.
9. **Finish -> full build -> back in the design window.** Designed.

## B. The three connecting gaps (the capabilities exist; the glue doesn't)
1. **Cost estimate** — the gate that protects our margin; computed from the deterministic plan +
   library hits (near-zero cost to compute). Method still to finalise.
2. **The component library** — the nave: it makes builds cheap, professional, and modular; it must
   exist BEFORE the build plan.
3. **Intake agent** — gate 1's brain (extraction + next-question).

## C. The bigger ideas (the moat — mostly beyond MVP)
1. **The library as a growing asset** — five layers: UI components; feature blueprints (a whole
   booking system, auth flow, admin panel); design themes; integration adapters (Stripe / email /
   calendar); full app templates. Every build enriches it, so every future app is cheaper + better.
   Well-*advertised*: each entry has a rich description + contract so the planner can find and pick
   it. A compounding moat: the more Scio builds, the stronger it gets.
2. **Build the most possible WITHOUT the LLM** — the cheapest, most reliable code is code we never
   generate. A rich library makes many apps ~80% assembly of proven parts + ~20% generation. The
   LLM becomes architect + glue more than code author. Halves cost AND raises quality.
3. **Fleet learning** — when the vision loop fixes an error, save the pattern; avoid it first-pass
   next time. Error-fixes, winning solutions, common user edits -> fed back into the playbook +
   library. The product improves from ALL users' builds — the network effect Lovable lacks.
4. **Determinism-first, everywhere** — a principle, not just for architecture: anything a rule /
   template / proven component can do, it does; the LLM only for the genuinely new. Quality
   (guaranteed) + cost (near-zero).
5. **Quality as a measurable gate, not a leap** — before the reveal, run a real quality suite
   (Lighthouse: performance / accessibility / SEO; security scan; best-practice lint) and SHOW the
   scores. Developer-grade proven, not claimed. No competitor shows this.
6. **Speed as a weapon** — library + determinism + cache -> a simple app in minutes, not an hour;
   directed changes in seconds. Speed itself reads as quality.
7. **Predictable pricing as a wedge** — because we reuse + build cheap, offer predictable pricing
   where Lovable has credit anxiety. "Know the cost up front" is sellable — and possible precisely
   because the library keeps our cost down.
8. **The compounding moat (the synthesis)** — the library + fleet learning make Scio a system that
   gets better and cheaper with every build. Lovable has a generator; Scio has a generator that
   learns and accumulates. That is the difference between a product and a moat.

## D. The design-window toolset (gate 2)
mark -> describe (structural change) · smart property controls (click -> colour / font / size
slider) · free prompt · global style (edit a token for the whole project) · reference upload
("like this" with an image) · undo / versions · test / interact (in the full build). All bound to
the same marking->code core.

## E. Additional refinements captured
- **Preview = a partial build, but the whole is already locked.** Planning is done fully up front;
  only code *generation* is staged (enough for preview -> full after approval). That's what makes
  the final build match the preview.
- **Contribute-back needs a quality gate** — a newly generated component enters the library only
  after tests + review, or it pollutes the library and lowers every future build.
- **Consistency over reuse** — canonical vocabulary + design tokens must bind library components
  and newly generated code together, or the app looks stitched together.
- **Two separate "libraries":** code components (this doc) vs prompt templates (the engine's
  step-by-step prompt playbook). Don't conflate them.
- **Model passes are a Settings control (and a test lever).** Expose the relay's configurable
  pass-count in Settings. Choosing **1** (e.g. just Claude) runs that single model **twice**
  (generate, then self-review) — never a raw single pass. Choosing **more** always runs the best
  model for the task first, then the next(s) to review/complement, and finishes with the best
  again (best -> review -> best). The engine already does this (B031, hard cap 4) — it just needs
  exposing + wiring. Set **1 + Claude** for cheap, deterministic end-to-end test runs; set up to 4
  for full quality. Available globally (Settings default) and overridable per build (fewer passes
  = cheaper — ties directly to cost control).

## F. Sequencing (honest)
- **MVP proves the core:** input -> a professional app you own. The three gaps (intake agent, cost
  estimate, a first version of the library) are what the core loop needs to live end-to-end.
- **The moat layers** (a rich multi-layer library, fleet learning, quality scores, predictable
  pricing) are what take Scio past Lovable — built right after the core stands, not all at once.
- **The library is the nave:** build it (even simply first) and the cost estimate + modular, cheap
  building fall out of it.

Recommended order: library (the nave) -> cost estimate -> intake agent -> wire the gates -> then
the moat layers.

## G. Build vs adopt — Anthropic API primitives
Several of our moat ideas (caching, multi-pass, memory, orchestration) already exist as Anthropic
API primitives. The stance: build ON the cheap primitives, evaluate the higher-level ones, and
spend our own effort on the differentiators. (Verify exact pricing, minimum lengths, and beta
status in the Anthropic console / docs before relying — they change.)

### Adopt now (clear wins, low risk)
- **Prompt caching — our single biggest cost lever.** Cache reads cost ~0.1x base input (~90%
  cheaper); a 5-minute cache write is 1.25x and a 1-hour write is 2x base input. Automatic or
  explicit breakpoints (up to 4), supported on all active models, workspace-isolated, ZDR-eligible.
  Minimum cacheable length is model-specific (~1024 tokens for Sonnet 5, ~512 for Opus 5). Use it on
  the STATIC prefix of every build-package prompt — the playbook, house rules, architecture slice,
  and canonical vocabulary. The breakpoint must sit on content identical across calls: put it at the
  end of the static prefix, NOT on the varying package-specific tail. Pre-warm the shared prefix
  (max_tokens:0) before a build to cut first-token latency. This REPLACES our own caching idea.
- **Batch API — for the async build.** The 50% batch discount stacks with the caching discount.
  Route parallelizable packages (Layer C already flags them) through Batch for the non-interactive
  build. Keep interactive changes (the design window) on standard/fast — batch adds latency and
  returns results out of order (match on custom_id, never on position).

### Evaluate (spike / compare before adopting)
- **Advisor tool (beta)** — a cheaper model consults a stronger advisor mid-task; overlaps our
  multi-pass / matrix. Compare quality + cost against our own relay on a real build before replacing
  anything. Our relay stays until proven.
- **Memory tool / memory stores (beta)** — a client-side /memories directory the agent reads before
  tasks and updates as it works, persisting across sessions (memory stores = the managed-agents
  server-side version). Could complement our DB-stored contracts for a living project. Evaluate vs
  our own persistence; not a replacement for the library or fleet learning.

### Keep our own (too custom / the differentiator)
- **Orchestration + sandbox + marking->code.** Anthropic's Managed Agents host sandboxing, state, and
  orchestration, and the Agent SDK ships the single-agent loop + sessions + checkpointing +
  telemetry (multi-agent coordination and organizational memory are left to you). But our sandbox
  needs custom instrumentation (data-scio-id) + marking->code + the vision loop, which a generic
  managed sandbox won't support. Keep ours. Borrow SDK primitives (session persistence, checkpointing,
  telemetry) only where they save work without constraining the core.
- **The component library + fleet learning.** No Anthropic primitive replaces these; they are the moat.

### The principle
Build ON the cheap primitives (caching + batch), evaluate the higher-level ones (advisor, memory),
and spend our own effort on the unique combination (gates + library + marking->code + our
instrumented sandbox). This sharpens the wedge rather than splitting it.
