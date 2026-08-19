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
| B045 | Component library — first slice (catalog, matcher, assembler, gate) | PP4  | P0 | done |
| B046 | Cost estimate (deterministic, from plan + library hits)        | PP4      | P0 | done |
| B047 | Fleet learning (capture fixes/patterns -> playbook + library)  | post-MVP | P1 | todo |
| B048 | Quality gate at reveal (Lighthouse + security + lint scores)   | PP9      | P1 | todo |
| B049 | Model-passes control in Settings (1 = same model x2; more = best->review->best) | PP4 | P0 | todo |
| B050 | Intake agent: extraction + next-question loop (gate 1's brain) | PP4 | P0 | done |
| B051 | Gate 1 wired end-to-end (wizard <-> api <-> engine, spec freeze) | PP5 | P0 | done |
| B052 | Wire the build + reveal end-to-end (step 3)                    | PP5 | P0 | done |
| B053 | Prepare the first REAL run (model ids, 1+Claude config, real-code sandbox, runbook) | PP5 | P0 | in progress |
| B054 | Harden the first real run (fix what real code surfaces)        | PP5 | P0 | done |
| B055 | Adopt prompt caching on build-package prompt prefixes (cost)      | PP4      | P1 | todo |
| B056 | Adopt Batch API for parallelizable build packages (cost)          | PP4      | P1 | todo |
| B057 | Evaluate Advisor tool vs our multi-pass relay (spike)             | post-MVP | P2 | todo |
| B058 | Evaluate memory tool / stores vs our own persistence             | post-MVP | P2 | todo |
| B059 | Harden the second real run (server actions + validation in the file plan, third-party console noise) | PP5 | P0 | done |
| B060a | Verification data layer (env-gated pglite client, enforced RLS, per-build lifecycle) | PP7 | P0 | done |
| B060b | Vision-loop interaction channel: drive fill/submit/reload via data-scio-id, verify outcome + persistence, make 'persists' and guest-isolation observable | PP7 | P0 | done |
| B064 | Local dev run mode: whole stack in-sandbox (dev auth, local Postgres, one script) | PP5 | P0 | done |
| B065 | Wizard UX on the free path: one field per answer is slow; the stand-in cannot read a paragraph | PP5 | P1 | todo |
| B066 | Spec review: let the user edit a field the wizard filed wrongly, without restarting the wizard | PP5 | P1 | done |
| B067 | Gate 2a: design window backend — preview-mode build (bridge) + directed-change round-trip | PP6 | P0 | done |
| B068 | Gate 2b: the design window UI — embed + marking selection + prompt + batch + generate-again + approve | PP6 | P0 | done |
| B061 | Contribute-back: the library grows from real builds (ids/categories/versions) | PP4 | P0 | done |
| B062 | Wire the cost estimate from the assemble-vs-generate plan       | PP4 | P0 | done |
| B069 | Design window: routes and per-route markings (the preview has more than one page) | PP6 | P1 | todo        |
| B070 | "Build it" recreates the workspace, so the design history is lost at the delivery build | PP6 | P0 | todo        |
| B071 | The whole + estimate are recomputed on every GET /intake: ~12s and a real Layer B+C model call per page load | PP5 | P0 | done |
| B072 | The wizard shows "Nothing yet — 0 of 6" while that GET is in flight — a false statement, not a spinner | PP5 | P0 | done |
| B073 | A build's actual cost is never recorded (usage_event empty, no cost on build_version) — only the estimate exists | PP5 | P0 | done |
| B074 | Contribute gate: allow RFC 2606 reserved names (example.com, .test, localhost) so test fixtures stop reading as leaks | PP4 | P1 | done |
| B063 | Decide customer-facing pricing (markup + currency) — the estimate shows build cost, not a price | PP4 | P0 | todo |

**Gate 2b is done** (B068) — **the design window exists and has been clicked**. Approving a spec
now asks one question (build it, or shape the design first), and Level 2 is a real screen: the
preview embedded, a Use/Mark toggle that arms the in-preview bridge, a *pending list that IS the
change set* (edit the note, remove the line, "Generate again" sends all of them plus the free prompt
as one change), the isolation proof and any skipped marking shown afterwards, conflicts answered
inline with both choices, and a versions list you can actually return to. Two calls were settled
here: **conflicts are answered in the window, not back in the wizard** — dropping a non-goal removes
it from the spec, while dropping a protection asks a second time and records an **allowance** on a
new spec version rather than rewriting the security posture (ADR-0001's wedge stays intact; the
known cost is that code and posture can drift, and the UI says a deeper change belongs in the
wizard) — and **versions really restore**, via `git read-tree` forward onto a new commit, refused if
the restored tree's instrumentation no longer verifies.

**B071–B074 are fixed, and re-measured against the same project.** `GET /intake` went from
**12.7s to 0.008s** and now makes no model call at all — the whole and the estimate are stored
with the spec that produced them. The wizard says "Reading your project…" instead of claiming
"0 of 6 core answers" it does not have. A build writes a `usage_event` with its real cost, tokens
and model, and the reveal shows what it actually spent beside what it was estimated at. The
contribute gate stopped reading `guest@example.com` as a leak — the exact `pkg_auth` the first run
refused now contributes as `auth.1.1`. Two things were found while fixing them: the key-detection
rule caught only the legacy `sk-<alnum>` shape, so a real `sk-ant-api03-…` key would have sailed
through the one check meant to stop it; and the new `.env` loader made the test suite pick up an
operator's key, so `test_api.py` was making REAL model calls — 100 seconds and real money for a
unit-test run. Both fixed.

**The first full REAL run happened (2026-08-19).** The whole product was brought up against
Claude (`claude-sonnet-5`, passes=1) and walked in a browser: wizard → review → build → reveal,
6 of 6 parts passing, a running app. It surfaced four things, now B071–B074: every load of the
wizard or review screen costs a real Layer B+C model call and ~12 seconds; while that is in
flight the wizard states "Nothing yet — 0 of 6", which is false rather than merely blank; the
build's actual cost is recorded nowhere (only the pre-build estimate exists); and the contribute
gate refuses real packages because model-written test fixtures contain `guest@example.com` and
`https://app.example.com/...`, which the leakage rules cannot tell from a genuine leak.

**B061 — the library grows from real builds.** It had four hand-written entries and no way
to get a fifth. Every delivery build now offers its work back: what came FROM the library is
skipped (assembled packages carry the entry id they came from), what passed every build gate is
generalized, re-verified against an entity it has never seen, put through the contribute gate,
and either added under a store-assigned `category.seqno.version` id or discarded as no better
than what is already there. Categories are canonical with a proposal path, so `login` lands in
`auth` rather than starting a fifth spelling of it; matching narrows by category and is decided
by a **contract** (operations, routes and files with the project's words removed), which is also
what dedup and version-vs-new use. Contributed entries are provisional and reviewable
(`/library/entries`, approve/reject), and live in Postgres beside the seeds. See ADR-0016.
Proven live: one build taught `auth.1.1` and `workout.1.1`, and the next build ASSEMBLED both.

**B066 — the review screen is editable.** The wizard's misfilings were visible and unfixable:
the only remedy was restarting the wizard, so people approved specs they could see were wrong.
Every field can now be corrected in place, an answer can be MOVED to the field it belongs in
(one request: set it there, empty the wrong one), and a correction is authoritative — it is
marked `corrected-on-review` and extraction refuses to overwrite it, so the next wizard turn
cannot quietly re-file the same mistake. Corrections are re-validated through Layer A's own gate,
so one that opens new work (two roles → `role_permissions`) says so and is answered inline. The
gate is enforced at approve, not only in the UI.

**Gate 2a is done** (B067). The backend of the design window exists: a preview build
carries the marking bridge (and a delivery build provably does not), and `POST /design/change`
applies a BATCH of markings to only the packages they touch, behind the isolation and
instrumentation guardrails. A marking that argues with the approved spec comes back as a
question and is not built. Each applied change is a design version. Gate 2b (B068) built the UI
on top of it.

**Gate 2's path is de-risked** (spikes/design-marking, 2026-08-12). The design window's riskiest
mechanic — marking an element inside a cross-origin preview — works: a preview-mode bridge inside
the iframe reports the click, the engine's strict resolver turns it into a package and a source
line, and a directed change round-trips with only that package touched. Build gate 2 on the split
the spike enforces: **the preview reports, the parent decides, and resolution stays server-side.**
See `spikes/design-marking/FINDINGS.md` for what it does not settle.

**B064 — the product has now been used, not just tested.** One script brings the whole
stack up in the sandbox with dev auth and a local Postgres, and the first click-through
went new project → wizard → review → build → reveal in a browser. It found four real
bugs that every test suite had missed, because tests call the api in-process and render
components without StrictMode: no CORS, a wizard that looped forever on the free path,
a GET that faked its own gate, and a build stream aborted by StrictMode. All four are
fixed. See `docs/RUNBOOK-LOCAL.md`.

**B060 is complete.** With B060a (a build runs with data) and B060b (a build drives
the app), the two criteria B054 had to scope out as unobservable — "works end to end
and persists" and "a guest cannot read another guest's row" — are checked, and they
gate the build. Verified live: a correct booking feature passes both; the same app
with a silently failing insert fails the first; the same schema with a policy that
does not isolate fails the second.

**B053 is prep, not the run.** The engine, the config and the runbook are done and
tested here; the run itself is operator-driven — it needs an Anthropic key and an
environment we don't have in CI. See `docs/RUNBOOK-FIRST-RUN.md`. B053 closes when
the operator has done the run; whatever it surfaces becomes B054.
