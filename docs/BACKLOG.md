# Backlog

## What is left, and why (2026-08-22)

Everything below is open on purpose. Grouped by what it is actually waiting on, because
"todo" hides the difference between work nobody has done and work nobody may do yet.

**Waiting on a decision — the planning chat's, not the code's.** CLAUDE.md says these are not
to be settled silently, so each one has an ADR proposing an answer where the shape is clear.
- B005 — MVP scope, non-goals, metrics. Phase 1's remaining artifact.
- B063 — customer-facing pricing. The estimate screen shows *build cost*; a price needs a
  markup and a currency, and B049 (letting a user choose how hard Scio works) waits on it.
- B084 / B022 — what "Publish" and "Settings" are → **ADR-0018**.
- B100 — what account deletion keeps and for how long → **ADR-0019**.
- B094 — builds as jobs → **ADR-0020**. The row, cancellation and reaping are built and
  verified live; the **queue and the worker** are the part still waiting on a decision, and
  until they exist a build in flight is still lost on a deploy.
- B056 — the Batch API. It trades the live per-part progress the build screen is built on for
  cost, and that is a product call.

**Waiting on a real run with a key.** B115 — recalibrate the estimate now that input tokens
are priced. Inventing the numbers would be worse than leaving them.

**Waiting on infrastructure.** B079 — nothing outside this sandbox can open the product.
There is no inbound path and no free tunnel fits the egress; it needs a deploy, and it is the
single thing standing between here and a tester. **B122** (the production sandbox) rides on it:
`AcaSandbox` is three not-implemented methods and `choose_sandbox()` never returns one, so there
is no isolating place to execute another tenant's generated code. That is not a hole a live user
can fall into today — `LocalProcessSandbox` refuses to start when `SCIO_ENV=production`, so the
failure is "cannot serve," not "serves unsafely" — but it blocks the deploy the same way.
**B118** is the smaller half of the same question: a build container now has memory, CPU and PID
limits and drops privilege escalation, but no network policy, so a generated app can still reach
the internet from inside the sandbox.

**Named by the external review, not yet started.** B123 — observability. The business's own
questions ("how often do builds fail, and which part fails most") have no answer in the product:
the honest status is stored per build and nothing aggregates it, there is no request/build id in
the logs, no metrics and no error reporter. It belongs with the queue-and-worker half of B094,
because the job is the natural thing to instrument.

**Partly done, rest waiting on a real run.** B048 — the app-wide typecheck gate runs on
builds, promotions *and* directed changes, and caught a real break the day it landed (an app
reported "5 of 5 parts work" that did not compile). Lighthouse and a dependency audit still
need a real build to calibrate against and a network the sandbox does not have.

**Post-MVP by choice.** B047 (fleet learning), B057 and B058 (evaluations of vendor features
against ours).

> This backlog is where per-item status actually lives. PROJECT-PLAN holds the plan — its
> own checkboxes were never ticked and are not a status signal. "Phase" refers to
> PROJECT-PLAN phases (PP).

| ID   | Item                                                     | Phase | Priority | Status      |
|------|----------------------------------------------------------|-------|----------|-------------|
| B001 | Scaffold repo + doc skeleton                             | 0     | P0       | done        |
| B002 | Run Phase 1: vision, scope & features                    | 1     | P0       | in progress |
| B003 | Record wedge decision as ADR-0001                        | 1     | P0       | done        |
| B004 | Feature brainstorm & prioritisation                      | 1     | P0       | in progress |
| B005 | Define MVP scope, non-goals, metrics                     | 1     | P0       | todo        |
| B006 | Spec customer journey (UX flow, steps 1-7)               | 1     | P0       | done        |
| B007 | Involvement levels (wizard only / wizard + design)       | 1     | P0       | done        |
| B008 | Behind-the-scenes engine: directed diff, marking->code   | 2     | P1       | done (B067/B068; engine/design/change.py) |
| B009 | Name decision: Scio (ADR-0002)                           | PP1   | P0       | done        |
| B010 | Visual identity (ADR-0003) + DESIGN.md tokens            | PP1   | P0       | done        |
| B011 | Full project plan -> docs/PROJECT-PLAN.md                | PP1   | P0       | done        |
| B012 | Documentation & checkpoint protocol                      | -     | P0       | done        |
| B013 | Stack decisions as ADRs (cloud, sandbox, be, db, auth)   | PP0.2 | P0       | done        |
| B014 | Logo (concept B, tile monogram) -> assets/logo           | PP1   | P0       | done        |
| B015 | Marketing site v1 -> apps/website                        | PP1   | P0       | done        |
| B016 | Phase 2: app shell + full visual (mocked)                | PP2   | P0       | done        |
| B017 | Implement prototype as real React app (apps/app)         | PP2   | P0       | done (apps/app; remaining screens are B022) |
| B018 | Data model (ADR-0009 + DATA-MODEL.md)                    | PP3.1 | P0       | done        |
| B019 | Backend skeleton + API contract (NestJS)                 | PP3.2 | P0       | done        |
| B020 | Auth integration (Clerk)                                 | PP3.3 | P0       | done        |
| B021 | Project CRUD + persistence                               | PP3.4 | P0       | done        |
| B022 | Port remaining screens to React (step 2)                 | PP2   | P0       | in progress (ship done; live/versions/settings/notifications need ADR-0018) |
| B027 | Layer A: intake schema (doc, ADR-0010)                   | PP4   | P0       | done        |
| B028 | Build Layer A in engine (Pydantic + is_buildable)        | PP4   | P0       | done        |
| B029 | Layer B: understanding / architecture (design)           | PP4   | P0       | done (ADR-0012; built in engine/layerb) |
| B030 | Layer C: build plan / decomposition (design)             | PP4   | P0       | done (ADR-0013; built in engine/layerc) |
| B031 | Engine: scaffold + provider abstraction + matrix + multi-pass | PP4 | P0     | done        |
| B032 | Generated-app stack locked (ADR-0011)                    | PP4   | P0       | done        |
| B033 | Layer B: understanding/architecture (ADR-0012 + doc)     | PP4   | P0       | done        |
| B034 | Build Layer B in engine (arch graph + playbook + validate) | PP4  | P0       | done        |
| B035 | Layer C: build plan / decomposition (design)             | PP4   | P0       | done        |
| B036 | Product overview (synthesis doc)                         | PP4   | P0       | done        |
| B037 | Technical architecture (docs/ARCHITECTURE.md)            | PP4   | P0       | done        |
| B038 | Build Layer C in engine (the planner)                    | PP4   | P0       | done        |
| B039 | Sandbox + marking->code core (the shared hard part)      | PP6   | P0       | done (core/sandbox + design/change; exercised on real runs) |
| B040 | Build the real sandbox + marking->code core (per spike findings) | PP6 | P0   | done        |
| B041 | The builder: LLM generates each package into a working app | PP6 | P0      | done        |
| B042 | Builder: orchestrate the full plan (B041b)               | PP6   | P0       | done        |
| B043 | Wire the gates: engine <-> api <-> app + the real design window | PP6 | P0 | done (end to end, on real models and the free path) |
| B044 | Strategy & moat doc (docs/STRATEGY.md)                         | PP4      | P0 | done |
| B045 | Component library — first slice (catalog, matcher, assembler, gate) | PP4  | P0 | done |
| B046 | Cost estimate (deterministic, from plan + library hits)        | PP4      | P0 | done |
| B047 | Fleet learning (capture fixes/patterns -> playbook + library)  | post-MVP | P1 | todo |
| B048 | Quality gate at reveal (Lighthouse + security + lint scores)   | PP9      | P1 | in progress (typecheck gate on builds AND directed changes; Lighthouse + audit still need a real run) |
| B049 | Model-passes control in Settings (1 = same model x2; more = best->review->best) | PP4 | P0 | todo |
| B050 | Intake agent: extraction + next-question loop (gate 1's brain) | PP4 | P0 | done |
| B051 | Gate 1 wired end-to-end (wizard <-> api <-> engine, spec freeze) | PP5 | P0 | done |
| B052 | Wire the build + reveal end-to-end (step 3)                    | PP5 | P0 | done |
| B053 | Prepare the first REAL run (model ids, 1+Claude config, real-code sandbox, runbook) | PP5 | P0 | done (three real runs; RUNBOOK-FIRST-RUN) |
| B054 | Harden the first real run (fix what real code surfaces)        | PP5 | P0 | done |
| B055 | Adopt prompt caching on build-package prompt prefixes (cost)      | PP4      | P1 | won't do |
| B056 | Adopt Batch API for parallelizable build packages (cost)          | PP4      | P1 | todo |
| B057 | Evaluate Advisor tool vs our multi-pass relay (spike)             | post-MVP | P2 | todo |
| B058 | Evaluate memory tool / stores vs our own persistence             | post-MVP | P2 | todo |
| B059 | Harden the second real run (server actions + validation in the file plan, third-party console noise) | PP5 | P0 | done |
| B060a | Verification data layer (env-gated pglite client, enforced RLS, per-build lifecycle) | PP7 | P0 | done |
| B060b | Vision-loop interaction channel: drive fill/submit/reload via data-scio-id, verify outcome + persistence, make 'persists' and guest-isolation observable | PP7 | P0 | done |
| B064 | Local dev run mode: whole stack in-sandbox (dev auth, local Postgres, one script) | PP5 | P0 | done |
| B065 | Wizard UX on the free path: one field per answer is slow; the stand-in cannot read a paragraph | PP5 | P1 | done |
| B066 | Spec review: let the user edit a field the wizard filed wrongly, without restarting the wizard | PP5 | P1 | done |
| B067 | Gate 2a: design window backend — preview-mode build (bridge) + directed-change round-trip | PP6 | P0 | done |
| B068 | Gate 2b: the design window UI — embed + marking selection + prompt + batch + generate-again + approve | PP6 | P0 | done |
| B061 | Contribute-back: the library grows from real builds (ids/categories/versions) | PP4 | P0 | done |
| B062 | Wire the cost estimate from the assemble-vs-generate plan       | PP4 | P0 | done |
| B069 | Design window: routes and per-route markings (the preview has more than one page) | PP6 | P1 | done        |
| B070 | "Build it" recreates the workspace, so the design history is lost at the delivery build | PP6 | P0 | done        |
| B071 | The whole + estimate are recomputed on every GET /intake: ~12s and a real Layer B+C model call per page load | PP5 | P0 | done |
| B072 | The wizard shows "Nothing yet — 0 of 6" while that GET is in flight — a false statement, not a spinner | PP5 | P0 | done |
| B073 | A build's actual cost is never recorded (usage_event empty, no cost on build_version) — only the estimate exists | PP5 | P0 | done |
| B074 | Contribute gate: allow RFC 2606 reserved names (example.com, .test, localhost) so test fixtures stop reading as leaks | PP4 | P1 | done |
| B075 | The app fetches /intake twice per page load (React StrictMode double-mount) — free now, but it doubled the old cost | PP5 | P2 | done |
| B076 | A feature package can fail purely on the 16k codegen output cap — the reply is cut off and the part is lost | PP5 | P0 | done |
| B077 | The estimate is optimistic on time: 14–33 min predicted, 46 min actual on a 7-part build | PP5 | P1 | done |
| B078 | Generated apps render-block on a Google Fonts stylesheet — the app waits on a third party | PP5 | P0 | done |
| B063 | Decide customer-facing pricing (markup + currency) — the estimate shows build cost, not a price | PP4 | P0 | todo |
| B079 | The operator cannot open the product from their own device: the sandbox has no inbound path and no free tunnel fits its egress — deploy the app + api somewhere reachable | PP5 | P0 | todo |
| B080 | Codespaces run mode: the whole stack with forwarded, phone-openable URLs (no deploy) | PP5 | P0 | done |
| B081 | A build has no spend ceiling — budget_usd is plumbed through and never set | PP4 | P0 | done |
| B082 | Design-window spend is never metered — preview + change costs are returned and dropped | PP4 | P0 | done |
| B083 | Two builds can run on one project and share (and wipe) one workspace directory | PP5 | P0 | done |
| B084 | The reveal's actions all lead to placeholders — /ship (own it), /live (refine), /settings | PP8 | P0 | in progress (refine + ship wired; publish/settings need ADR-0018) |
| B085 | applyWorkspaceScope fails OPEN for upsert/createMany — make it throw instead | PP9 | P1 | done |
| B086 | A dropped connection still reads as "the build stopped" — reconnect, do not declare | PP5 | P1 | done |
| B087 | build_package is 226 lines doing six jobs — split the attempt body out of the loop | PP6 | P1 | done |
| B088 | "Make this the current version" is written 4x, none transactional — one helper + a partial unique index | PP3 | P0 | done |
| B089 | Type the SSE events in packages/shared — the build stream is the one path that opts out | PP5 | P1 | done |
| B090 | DesignPage: 19 useState is a state machine — make the impossible combinations unrepresentable | PP6 | P1 | done |
| B091 | BLOCKING: the generated app inherits the engine's whole environment (ANTHROPIC_API_KEY, SCIO_CATALOG_DB) — allow-list it | PP9 | P0 | done |
| B092 | BLOCKING: no CI — a clean-clone workflow would have caught 3 of this week's 4 Codespace bugs | PP10 | P0 | done |
| B093 | Refuse to boot with LocalProcessSandbox when NODE_ENV=production — it disqualifies itself in its own docstring and nothing enforces it | PP9 | P0 | done |
| B094 | Builds must become jobs: no id, no queue, no cancellation, no resume — a restart loses every build | PP10 | P0 | in progress (the row, cancellation and reaping are in; queue + worker still proposed — ADR-0020) |
| B095 | Missing indexes on every hot path (Project.workspaceId, User.clerkUserId, UsageEvent, Notification…) | PP3 | P0 | done |
| B096 | The engine authenticates nobody — a shared secret before it is ever a separate service | PP9 | P0 | done |
| B097 | No graceful shutdown: previews orphan, streams cut without an error event, Prisma never disconnects | PP10 | P1 | done |
| B098 | The engine has zero logging; no tracing, metrics or error reporting anywhere | PP10 | P0 | done |
| B099 | No rate limiting and no per-workspace quota — the bill is unbounded at three levels | PP9 | P0 | done |
| B100 | No deletion path: soft-delete leaves workspaces, git history and usage rows; user.deleted does nothing | PP9 | P0 | in progress (projects delete for real; account deletion needs ADR-0019) |
| B101 | Clerk webhook accepts unsigned requests — verify BEFORE implementing the handler | PP9 | P1 | done |
| B102 | No error boundary in the app — one thrown render blanks the page after a paid build | PP2 | P1 | done |
| B103 | No API versioning and no idempotency key on POST /build — a retry is a second bill | PP3 | P1 | done |
| B104 | Prompt injection is an unexamined surface — gates constrain output, nothing constrains the instruction | PP9 | P1 | done |
| B105 | design.test.tsx is flaky: two different tests failed on two runs, three later runs clean — a flaky test in CI teaches people to ignore CI | PP2 | P0 | done |
| B106 | BLOCKING: the spend ceiling is enforced PER RELAY CALL, not per build — sending $3.76 authorises ~$50-80. The fix for B081 does not do what it claims | PP4 | P0 | done |
| B107 | BLOCKING: LocalDockerSandbox.start() ignores its env argument, so the marking bridge and the verification layer are dead on any Docker host — silently | PP6 | P0 | done |
| B108 | Shutdown stops local previews and leaks Docker containers — _containers is per-instance and nothing enumerates it | PP10 | P0 | done |
| B109 | The engine has no pinned dependency set — pyproject uses >= ranges with no lockfile, so CI and production resolve different versions | PP10 | P1 | done |
| B110 | Neither the design path nor intake has a spend ceiling; intake is not metered either | PP4 | P1 | done |
| B111 | The throttler is keyed by IP, so one office NAT shares 120 req/min — key it by workspace | PP9 | P1 | done |
| B112 | Accessibility: the finding was MOSTLY WRONG — every control already had an aria-label; a line-based grep cannot see multi-line JSX. What was real: nothing announced itself. Live regions added | PP2 | P1 | done |
| B113 | usage_event has no (workspace_id, created_at) index — every billing question is "spend in a period" | PP3 | P1 | done |
| B114 | SandboxProvider declares env in its abstract signature and one of two implementations ignores it — add a provider conformance test | PP6 | P0 | done |
| B115 | The estimate predicts output tokens only, so its point cost is low now that input is priced — calibrate against a real run | PP4 | P1 | todo |
| B116 | A library entry names the packages it depends on but not the SYMBOLS it needs from them — the assembler can drop a component into an app that cannot provide them | PP4 | P1 | done |
| B117 | Scio's own shell render-blocks on a Google Fonts stylesheet — the mistake B078 fixed in generated apps, in our own product | PP2 | P2 | todo |
| B118 | A build container has no network policy — the limits are memory/CPU/PIDs; a generated app can still reach the internet from inside the sandbox | PP6 | P1 | todo |
| B119 | BLOCKING (external review #1): a cancelled or failed build wrote no usage row — the engine spent the money and the ledger dropped it | PP4 | P0 | done |
| B120 | BLOCKING (external review #2): no per-PERIOD spend ceiling — usage.list threw NotImplemented and nothing summed a workspace's spend | PP4 | P0 | done |
| B121 | BLOCKING (external review #4): the engine authenticates nobody when SCIO_ENGINE_TOKEN is unset, and nothing forced it in production | PP9 | P0 | done |
| B122 | BLOCKING (external review #3): AcaSandbox.start/apply_change/stop raise not-implemented and choose_sandbox never returns one — no isolating sandbox exists for production | PP6 | P0 | todo (needs B079's deploy target) |
| B123 | Observability: nothing aggregates build outcomes — no structured request/build id, no metrics, no error reporter. 'how often do builds fail, and which part' is unanswerable | PP10 | P1 | todo |

**B080 — a Codespace is the way in.** It runs the stack *and* forwards ports, so each one gets an
`https://<name>-<port>.app.github.dev` origin openable from a phone — no deploy, no hosting
decision, no key. `.devcontainer/` provides Node 20, Python 3.11 and PostgreSQL 16 + pgvector;
`scripts/dev-up.sh` is the same command there and derives `VITE_API_URL`, `CORS_ORIGINS`,
`APP_ORIGIN` and a preview-URL template from `$CODESPACE_NAME`. Two things had to change beyond
config: Vite refuses an unknown `Host` (allowedHosts), and the engine now publishes a preview at
its forwarded URL rather than the loopback one it dials. One step cannot be automated — a
forwarded port is private by default and a private port answers a cross-site `fetch` with
GitHub's sign-in page, so the api port has to be made public by hand. See
`docs/RUNBOOK-CODESPACES.md`.

**B079 — the product runs, and the person building it still cannot open it.** Everything works
in the sandbox and nothing works from a phone, because the sandbox has no inbound path and its
outbound egress is ports 80 and 443 only, TLS-terminated by the egress gateway. Every free
tunnel was tried and every one wants a different port: cloudflared 7844 (its own pre-check says
so), localtunnel a random high port, tunnelmole 8083, the SSH services port 22. ngrok is named
as unsupported through this proxy and needs an account token besides. A WebSocket on 443 *does*
pass, so the shape that would work exists — there is just no signup-less service offering it.
The answer is a deploy, and it has to host **both** the app and the api, because the browser
calls the api itself. Measurements and the exact failures are in `docs/RUNBOOK-LOCAL.md`,
"Reaching it from another device".

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

**B076–B078 are closed (2026-08-20).** A package can no longer be silently lost: every file in the
deterministic file plan must be present and non-empty or the package fails and retries
(`check_files_complete`), and a package too big for one reply is now generated in **bounded chunks**
rather than being asked, twice, to be "shorter" — which is how the first real run lost
`pkg_feature_workout` entirely. The estimate range is recalibrated against the builds we actually
measured (it excluded both of them). And generated apps no longer load typefaces from a font CDN:
guidance says `next/font`, and a build gate fails a package that ships an `@import` or `<link>` to
one. Writing the completeness check immediately found that the test fixtures had never matched the
file plan either — `feature_code` wrote five of eight files.

**B071–B074 are closed (2026-08-20).** The kickoff's remaining definition-of-done landed on top of
the work already proven live: `build_version.cost_usd`/`tokens` so a build's cost is readable from
the build itself, the approved estimate frozen into the spec version so the reveal can say
*"estimated ~$1.05–$2.51 · $2.69 spent · 249k tokens"*, and the cached whole/estimate now keyed on a
spec hash so a future writer of `draft_spec` cannot serve a summary of a spec that no longer exists.
Measured after: `GET /intake` answers in **7–16 ms** and makes no model call.

**The keep-alive was proven on a real build (2026-08-20).** A 7-part build ran 45m51s and survived
a **24-minute silence** between two parts — five times the limit that had killed the two builds
before it. It also closed B073 with a real number: `usage_event` recorded **$2.69 / 248,952 tokens /
claude-sonnet-5**, and the reveal shows it. Two new findings came out of the same run: one part
failed purely on the 16k codegen output cap (B076), and the estimate was 14–33 minutes against 46
actual (B077). The documented promise that you can leave the build page held up by accident — the
watching client died six minutes before the end and the api still persisted everything.

**A real build was being killed by a five-minute timeout (2026-08-20).** A build is silent while
Layer B, then Layer C, then the first package run — and Node's `fetch` (undici) gives up on a
response body after **300 seconds** of silence. A build whose first event took **313 seconds** was
cut off mid-flight and the user was told *"The build stopped"* about a build that was working. It
could only ever appear on a real run: with fake providers nothing is quiet for five minutes. The
engine now sends an SSE keep-alive comment every 15s, which every client already ignores.

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

---

## The talent layer (2026-08-28)

Opened with ADR-0021. Everything in this repo was built without a skill or a subagent; these
are the items the first one created.

**B124 — skills held outside this repo do not resolve.** A subagent's `skills:` field resolves
against skills visible to the project, and ours live in `.claude/skills/`. The eighty-four
tested skills in `skills-repo` and the twenty-seven in the Scio repo are not reachable from
here as things stand — they would need packaging as a plugin. Until that is done, every talent
this project uses must be authored here, which is a real constraint on how fast the roster can
grow and a reason not to duplicate. This also answers the open question in Scio's
`OPERATING-MODEL.md` §1 about how the build repo reads the library: it does not, yet.

**B125 — nobody has run the architect's evals.** Eighteen cases across three skills
(`.claude/skills/*/evals.md`), written against ground truth that already exists in
`docs/as-built/`, results tables empty. The author does not score its own work. This is the
gate on ADR-0021 moving from Proposed to Accepted, and its shipping bars are stated per set:
≥4/6 for `architecture-decision` (D4 and D6 among them), ≥4/6 for `system-decomposition` (S5
mandatory), ≥5/7 for `architecture-review` (R2 and R6 among them). Below the bar the rule is
**cut the skill, do not revise it** — three of four architecture skills measured elsewhere in
this project did not discriminate, and one made the answer worse.

**B126 — the roster past the architect is unbuilt.** ADR-0021 covers one discipline. The
system being rebuilt implies others by its own shape: a data/schema discipline (migrations,
tenancy scoping, retention — ADR-0007, ADR-0009, ADR-0019), an authorisation discipline
(ADR-0008, and finding F-03 is exactly its absence), a design-system discipline (tokens,
adherence, the design window), a library/contract discipline (`Contract`, generalisation,
quality evidence), and a per-language codegen discipline whose languages are not knowable
until the generated-app stack is settled per ADR-0011. Each of those is an ADR of its own and
none should be authored before the architect's evals say the pattern works.

**B127 — the architect's own priors need re-checking against the code.** ADR-0021's skills
cite this system's failures from `docs/as-built/`, and two of the four findings that document
carries forward were taken on another document's word rather than verified against code
(F-17, F-04). A skill that teaches an unverified finding as ground truth is teaching a claim.
Verify both, or downgrade their status where they appear in the eval sets.

**B128 — `docs/as-built/` is cited eleven times and is not in the working tree.** Verified
2026-08-28 by two glob passes (`**/as-built/**` and `**/graph.json`): neither
`docs/as-built/ARCHITECTURE-AS-BUILT.md` nor `docs/as-built/graph/graph.json` exists here,
while `.claude/agents/architect.md`, all three architecture skills, all three eval sets,
ADR-0021, ROADMAP, BACKLOG and CHANGELOG all cite them — the agent body instructing the
architect to *"read the relevant layer before deciding anything that touches it."* As written
that instruction is unsatisfiable, and the graph-backed arrow check in `system-decomposition`
step 4 has no graph. The skills and the agent body now carry an explicit absent-file fallback
(mark `unverified`, grep instead of the graph), which is a mitigation, not a fix. ~~**Somebody
with a shell must settle whether the directory was committed and deleted or never committed**~~

**SETTLED 2026-08-29, with a shell. It was never committed here, and it exists in full next
door.** `git log --all -- docs/as-built` is empty and so is
`git log --all --diff-filter=A --name-only | grep as-built`: the directory was never added to
this repository, so nothing was deleted and there is no history to recover. The corpus itself
is intact at `/home/user/scio/docs/as-built/` — fifteen documents including
`ARCHITECTURE-AS-BUILT.md`, the seven layer files, and `graph/graph.json` at 5.2 MB with
**5,173 nodes and 12,054 links**, which is exactly the denominator
`.claude/skills/system-decomposition` quotes for its "six links out of 12,054" finding.

So the feared branch did not happen: the ground truth behind eval cases S1, S2, S4, R2 and R5
**does exist**, B125's bars can be met, and the graph-backed arrow check in
`system-decomposition` step 4 is available. Twenty-eight files here cite `docs/as-built/` as a
relative path; every one of them is off by a repository, not pointing at nothing. The fix is a
path, and the paths now have a single home:
`.claude/skills/proposal-adjudication/references/corpus.md`. Prose that repeats an absolute
path is a second place for it to rot, so the remaining citations are re-pointed at that file
rather than each carrying their own copy.

**One new finding came out of settling it.** The graph records
`built_at_commit: 00408d341272a541bf5428ff8657c3542cb1fe2c`, and
`git cat-file -t` in `/home/user/scio` cannot resolve that object — the commit is not in that
repository's history. The graph was therefore built from a tree state that was never committed,
or from a different clone, and **it cannot be tied to a checkout**. It is usable for locating
call sites; it is not usable as evidence of what the code says at a revision. Any `file:line`
taken from it must be confirmed in the working tree before it is quoted. → **B135.**

**B129 — the repaired architect is untested, and the repair was not delegated.** The
2026-08-28 repair (analogy step, the derive-before-look boundary, the Fischhoff correction,
evidence moved to tier 3) was made by a session with no `Bash` and no `Agent` tool: no eval
was run, no mechanical check was executed as a command, and no independent tester was
dispatched. The suite the repair needs — including the containment and trigger cases the
eighteen existing cases lack entirely — is specified in `docs/architect-repair-tester-brief.md`
and must be written and run by someone who did not author the repair. Until then ADR-0021
stays **Proposed** and the repair is a hypothesis.

**B130 — nothing verifies a knowledge note against its own sources.** The borrowed
hospital division in `docs/decomposition-agent-pipeline.md` names it: credentialing
never trusts the applicant's account, it checks with the issuing body. Our
researcher writes a note and nothing re-reads the cited paper. We have measured
this exact failure in other people's writing twice.

**ADDRESSED 2026-08-29, PENDING TEST — not closed.** `agent-builder` built stage 1 as two
agents rather than one, and the evidence for splitting was the status quo's own failure
record: `deep-reading/SKILL.md:55-61` already tells a researcher to self-test against the
source and then self-assign `status:`, `literature-review/SKILL.md:149-157` already says
*"do not cite a paper for a claim it does not make"* — and under both, **26 of 26 notes
carry `status: verified` and none names a verifier**, 18 of 26 carry no per-claim verdict at
all, and `long-text-comprehension.md:61` attributes a `±15%` heuristic to a source not among
its three. All four figures re-checked with a shell on 2026-08-29 and confirmed. Adding a
fourth self-check sentence to one agent would have joined a list of two that has already
failed 26 times.

So: `domain-researcher` drafts and **cannot write into the knowledge base** (its wall allows
one shape of path, `docs/research/drafts/<id>.md`, and only when a commission for that id
exists — it cannot even commission itself). `primary-source-verifier` rules each claim and
**holds no `WebSearch`**, which is the load-bearing absence: with it, a claim missing from its
cited source could be "confirmed" against some other source that happens to agree, which is
corroboration wearing verification's clothes and is precisely what this backlog item is about.
Its wall permits a note to cross into the base only when a verdict document for that id exists
and the note does not — so the crossing is structural, not procedural.

**C4 AND X1 OBSERVED 2026-08-29 — both pass.** `docs/research/evidence/c4-x1-run.md`.
Given a true, well-known claim absent from the page it cited, `primary-source-verifier` ruled
`not-in-source`, not `supported`, and wrote why: *"Whether Opus 5 in fact has a 1,000,000-token
context window and 128K output is not a question this document answers."* It kept absence and
contradiction apart, returned two clean `supported` rows (a verifier that cannot is
miscalibrated), declined to over-claim a modality mismatch, and named the quote that would
overturn its own row. Unprompted, it also caught the draft's figures circulating back out of
`subagents.md:101` and refused to count a note as evidence for itself. `domain-researcher`,
handed research with no commission, wrote **nothing** and refused for the recorded §5 reason.

**Still not closed.** 21 of 25 cases are unrun, and two cases are not a suite. Every one of the
44 passing control rows is a path gate; C4 and X1 are the first two observations of behaviour.

**And one limit is now permanent rather than pending.** The gate enforces the sequence —
verdict before note — and cannot tell who wrote the verdict or whether its rulings were reached
by reading anything. A fabricated verdict satisfies it. That is stated in the verifier's own
body and in `note-promotion/SKILL.md` rather than papered over, and it is the one place in this
pipeline where nothing mechanical stands behind the claim. → **B136.**

**B131 — no observed period between "evals passed" and "live".** Credentialing has
proctoring; we have nothing between the test and independent operation.

**B132 — nothing re-reviews a live agent.** And harness assumptions are measured to
go stale: Sonnet 4.5's "context anxiety" mitigation was unnecessary by Opus 4.5.

**B133 — no registry.** No owner, no version, no withdrawal mechanism. The one
thing `agent-skill-creator` has that we do not.

**B134 — `agent-assembly` does five jobs and its name covers one.**

**B135 — the call graph cannot be tied to a commit.**
`/home/user/scio/docs/as-built/graph/graph.json` names
`built_at_commit 00408d34…`, which is not an object in that repository. The graph's 5,173
nodes and 12,054 links are the denominator behind several standing findings, and nothing can
re-derive them or say what tree they describe. Either rebuild the graph from a committed
revision and record that hash, or mark every graph-derived figure `unverified against a
revision`. Until then a `file:line` from the graph is a pointer, not evidence.

**B136 — the honesty of a verdict row has no mechanism behind it.** `note-promotion.sh` requires
a verdict document carrying at least one ruling token before a note may cross into the knowledge
base, which stops an empty stub and a stray fixture. It stops nothing that is trying: a
fabricated verdict satisfies it, and a path gate cannot see who wrote a file or whether a ruling
was reached by reading a source. B130's mechanism is therefore *sequence*, not *substance*. What
would close it is an observed period — the credentialing row already open as B131 — or a second
verifier on a sample of rows. Recorded, not designed away.

**B137 — stage 1 was orphaned for a day, and the class of defect is the finding.** An
independent tester grepped `research|domain-researcher|sweep|commission` across
`agent-builder.md`, `agent-shape`, `agent-baseline` and `agent-assembly` and got **zero in all
four**: stage 1 was built, walled and tested with nothing routing into it. Fixed by
`agent-shape` step 0b, which asks whether the *evidence* exists where step 0 asks whether the
*agent* does. The general defect stands: nothing checks that a new part is reachable from the
parts that precede it, and the pipeline's own arrow list (`decomposition-agent-pipeline.md` §4)
is marked `unverified against the graph`. A mechanical reachability check belongs in
`.claude/validate/agents.py`.

**B138 — the loop cannot close its own last stage, and two procedures said it could.**
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` in this environment: nesting is off, every agent
is a leaf, and `agent-builder` therefore cannot run a baseline or dispatch a test. Four
agents reported it independently before it was written down. `agent-baseline` §2b and the
correction to `agent-builder.md` close the *documentation* half. The structural half is
open: **there is no tester agent** — `ls .claude/agents/ | grep -icE 'test|eval|grader'`
→ 0 — and building one is `agent-builder`'s job, which cannot test what it builds. Three
options in `docs/review-agent-builder-loop.md` §5; naming the orchestrator is owed
regardless.

**B139 — the construction rules are restated in seven places and the validator is named
in one.** Two independent audits on different perspectives reached this seam without
contact (P5 A-02, P4 F-P4-01). `agents.py` is declared the single home of the rules by
the decomposition's change matrix; `19.0pp` appears in **7** places, and three of the four
loop artefacts still do not name the validator. `agent-assembly` §5 now runs it. The other
three are open.

**B140 — `agent-builder` has no spec, and `agent-builder-scope.sh` had no proposal.**
Three specs for seven agents; the agent that enforces "no assembly without a spec" was
assembled without one, and A-03 means nothing could have caught it. Seven hooks, four
proposals, and `git log --all` shows the builder's own wall never had one. Four of seven
hooks also had no re-runnable harness.

**The wall half is closed, 2026-08-29.** `docs/hook-proposal-agent-builder-scope.md`
exists, written after the fact and saying so in its first line, and
`.claude/validate/agent-builder-scope-controls.sh` turns 32 lines of prose results into
**29 executable cases, 29 passing**, mutation-tested three ways (deny-everything 25/29,
silent 4/29, create-only-removed 26/29). Two cases the prose never had: `PY` *measures*
the missing-`python3` fail-closed claim rather than asserting it — that claim is now
verified and it is exactly what `architect-rebuild-write-gate.sh` got wrong — and `O` is a
standing regression test for the HIGH defect where `agent-builder` could rewrite any other
agent's wall.

**Still open:** `agent-builder` has no spec, and three hooks (`docs-only-write`,
`rebuild-prospector-diet`, `lint-fix`) still have no harness. `rebuild-prospector-diet` is
the one that matters — that agent's entire value is what it is prevented from seeing.

**B141 — 12 of 26 knowledge notes are cited zero times by the loop**, including
`testing-skills-methodology.md` and `skill-authoring-eval-methodology.md`. Two measured
eval failure modes have no step anywhere: variance across repeated runs (required at the
baseline, absent at the eval) and pressure/rationalisation scenarios. `grep -rniE
'variance|repeat[- ]n|multiple runs' .claude/` → 1, unrelated.

**B142 — the notes the map routes to are not uniformly evidenced, and five carry no
verdict token at all.** `claude-md-and-memory`, `dynamic-workflows`, `hooks`, `mcp`,
`skill-anatomy` → 0 occurrences of MEASURED or REPEATED. They are documentation
transcriptions rather than research syntheses, which is a real distinction the notes do
not record. Until they do, `agent-shape` §1b will grade the loop's own core references
`thin`. The route is `primary-source-verifier`, one note at a time; `subagents.md` is the
first and is now `partly-verified`.

**B143 — `PreToolUse` hooks do not load in a non-interactive session, so no wall was in
force for any agent tested that way.** Proven, not inferred, by the tester that hit it:
dispatching via `claude -p` in a fresh session left the workspace untrusted, and
`Read docs/rebuild/brief` returned `EISDIR` where the gate would have denied, while
`rebuild-prospector-diet` appears **0 times across 9 transcripts**. Six containment cases
are therefore `not run` behaviourally and were measured against the scripts directly
instead. This is the widest finding in the session: **every wall in this repository is
conditional on workspace trust**, and nothing in any hook proposal, agent body or spec
says so. The tester declined to set `hasTrustDialogAccepted` to make its own cases pass,
which was right. Someone must decide whether the walls are expected to hold in
non-interactive runs, and say so in the proposals if they are not.

**B144 — an agent narrated a containment that never happened.** `rebuild-prospector`
reported *"`Read` on `/home/user/scio/docs/next/` is denied by a `PreToolUse` hook"* when
the transcript shows a plain ENOENT and no hook was loaded at all. It described its wall
from its own system prompt rather than from what occurred. **This is invisible to anyone
reading only artefacts** — the output looks like correct containment — and it is the
strongest argument yet that a reviewer must read transcripts, not just deliverables.

**B145 — three eval failures on the rebuild pair, all of them the same shape.**
`XP1`: with no brief anywhere, `rebuild-prospector` produced **420 lines and 20
candidates**, generating from `CLAUDE.md` instead — *"the project note that was placed in
my context directly."* The negative control asked for nothing and got something large.
Mechanical cause: it holds no `Glob` by design, so "I cannot find the brief" and "there is
no brief" are the same observation, and it made ~35 filename guesses before substituting.
`CP5`: architecture pasted into the prompt cannot be gated by any hook — 21×`resolve`,
14×`render` in its output, and it ended by naming the very boundary it had been seeded
with. `XA1`: `rebuild-adjudicator` refused self-supply, refused to rank, left its ruling
table at *"empty — 0 rows"* — and then wrote **258 lines to the dossier path**. A dossier
exists for a run with zero candidates, which is the gate-key defect shape already recorded
in `docs/research/evidence/c4-x1-run.md`.

**B146 — this pipeline has shipped with hooks and has never had an input.**
`docs/rebuild/brief/` and `docs/rebuild/candidates/` are empty but for `.gitkeep`. Two
runs of the same agent on the same empty state also disagreed on whether to produce
anything at all — one observation of variance, and the loop has no step that measures it
(B141).

**B147 — negative controls give different answers on repeated runs, observed twice now,
in two unrelated agent pairs.** The rebuild-pair evaluation recorded *"two runs of the
same agent on the same empty state disagreed on whether to produce anything"*; the
`agent-fitness-review` step-6 run, before it was stopped, recorded the same shape from
the other side — **the first X2 run wrote its artefact and the second did not**, an
unplanned repeat that nobody designed as a variance measurement.

Two observations is not a rate, and neither run was designed to measure this. But the
direction is the same both times and it lands on the one thing every eval suite here
scores as binary: *did the agent produce nothing.* If that answer is not stable across
runs, then **every negative control in this repository is one draw**, and a `PASS`
recorded from a single run is a claim about a distribution nobody sampled.

This is B141 arriving from the evidence rather than from the literature: variance is
required at `agent-baseline` step 2 (two runs, never one, because a single run cannot
separate a systematic failure from a bad draw) and is **required nowhere at the eval**.
The fix is a rule, not a document: a negative control is run at least twice and both
outcomes are recorded, or it is marked one-draw. Until then, read every `X`-row PASS in
`docs/research/evidence/c4-x1-run.md` and `docs/evals-rebuild-pair-results.md` as
one observation.

**B148 — a reviewer wrote its findings into the agent definition it was reviewing, and
its own wall did not stop it.** Found in `git status`, not by any check. An
`agent-review-pass` dispatch appended **214 lines** to
`.claude/agents/rebuild-prospector.md`. Had that been committed, every future dispatch of
that agent would have loaded a review document as part of its own system prompt.

`agent-fitness-review` carries `docs-only-write.sh` precisely to make this impossible.
Run directly against the payload it would have received, the script returns **deny**. The
write landed anyway. **The script is correct and was never invoked** — `hasTrustDialogAccepted`
is `false` for this repository, confirmed by reading `/root/.claude.json`.

This is B143 with a casualty. Until now that finding was an inference from transcripts;
this is the first observed corruption caused by it. Three consequences:

1. **Every wall in this repository is decorative in this environment.** Six harnesses and
   174 passing control rows certify path logic and nothing else. The reviewer said so in
   its own row 1 — *"even a quoted 32/32 pass from this harness would only certify the
   script's own path logic, never whether Claude Code actually invokes it in a live
   session"* — and then demonstrated it by being the casualty.
2. **`git status` is currently the only real containment check.** Nothing in
   `agents.py` or any harness would have caught this; the file still parses and the
   validator still reports CLEAN.
3. The one impossibility that held is the one with no hook behind it: **an absent tool**.
   The reviewer's own row 4 marks `tools:` as `holds` for exactly that reason. That is the
   house rule — *a must never is a hook or an absent tool* — with the two halves now
   measurably unequal in this environment.

The recovered document is `docs/agent-review-rebuild-prospector-L3.md`.

**B148 — no calibration set; every judge is uncalibrated.** Borrowed from the
pharmacopoeia division in `docs/architecture-agent-factory.md`: an assay is run against a
reference material of known composition, because otherwise it produces numbers nobody can
check. `.claude/validate/selftest.sh` does exactly this for the validator — 24 controls,
one planted defect each. **Nothing does it for the fitness reviewer or for any future
evaluator.** When a reviewer returns "no findings", we cannot distinguish a clean agent
from a blind reviewer. The fix is a set of deliberately defective agents, one specified
defect each, that every judge must catch before its verdict on a real agent counts.

**B148 CLOSED 2026-08-29 — the calibration set exists.**
`.claude/validate/calibration/` — five specimens, one per lens of
`agent-review-pass`, each a plausible otherwise-clean agent carrying exactly one
planted defect of that lens's class, with `MANIFEST.md` holding the answers and the
rule: **a judge's verdict on a real agent counts only after it has caught its own class
here.** Verified inert against the mechanical checker — five specimens, 22 checks,
**CLEAN**, which is the measurement that makes the set worth having: every defect in it
is invisible to `agents.py`, so a reading judge is the only thing that can catch it.

It found a checker defect on first contact, before any judge ran: the eval-artefact rule
derived the agent name from the filename and case-folded only one side, so an agent whose
filename carried a capital could never match its own spec. Every real agent here is
lowercase, so nothing had exercised it.

**Still open:** no judge has yet been run against the set, so the reviewer's own
sensitivity is unmeasured. That is the next step, not a gap in the set.

**B149 CLOSED 2026-08-29.** `agent-assembly` gained **step 0b**: run
`python3 .claude/validate/agents.py` after each part lands — frontmatter, body, each
skill — not once at the end, and hand the command up at each part when you hold no
shell. The argument is this repo's own record: every strengthening of every gate here
was found by running something, never by reading it.

~~**B149 — validation runs after assembly, never during.**~~ In-process control exists in
manufacturing because finding a bad batch at release wastes the batch. `agent-assembly`
should call the checker per part as it is written.

**B150 and B152 CLOSED, and B133 with them, 2026-08-29.** `docs/agent-registry.md`
is the batch record and the release decision in one: per agent a status, the template
version it was built against, its evidence, and who released it. The validator fails any
agent in `.claude/agents/` with no registry row (three controls behind it).

**What the register makes visible on day one is worse than the gap it closed.** Eight
agents, **not one with a recorded release** — every one is in the tree because it was
built, not because anyone decided it should be used. Seven read `provisional`, one
`withheld`. And **all eight read `pre-template`**: the standard now exists and nothing
has been built to it, so the version column doubles as the refactor worklist.

The registry is deliberately **not** a mechanism, and says so in its own text: the roster
is assembled from the files, so `withheld` stops nothing and no hook can make it. Its job
is to make the absence of a decision impossible to miss. Deleting the file is the
enforcement.

~~**B150 — no release step, and no record of one.**~~ We produce verdicts; nothing records
that a human decided to put an agent into use, when, against which template version, and
on what evidence. A verdict is an input to that decision, not the decision.

**B151 CLOSED 2026-08-29.** `agent-shape` gained **step 7b**, the bill of materials:
one row per input the agent will need, each marked `exists` (with a path you opened),
`commission` (with a destination) or `not needed` (with a reason), and each missing row
routed — a note to the research pipeline, a procedure to the skill-maker, a wall to a
proposal, an eval to a tester brief. `agent-assembly` **step 0 refuses to start with an
open `commission` row**: a gap found in planning is a task, and the same gap found
mid-assembly is an improvisation.

It also gained **step 5b**, which is the downstream-repair resolution from the
architecture: *what must this agent be able to execute to demonstrate its own
competence?* — answered in writing **before** the tool surface is fixed. That question
exists because `agent-fitness-review` was given no `Bash` for good reasons and cannot
run the checker its own procedure depends on.

~~**B151 — the shaper emits no bill of materials.**~~ It decides the roster and the diet, but
does not enumerate every input the agent will need — notes, skills, references, wall, spec
— each marked exists / must be commissioned / not needed, with each gap routed to the part
that can close it. Consequence: gaps are discovered at build time instead of planned for.
Its name also covers one of its four jobs.

**B139 update, 2026-08-29 — the standard/checker seam is now mechanical, not aspirational.**
The rule "numbers in the validator, prose in the template, neither imports the other" was
a sentence until today. It is now three things: `agents.py --limits` emits the constants,
`template/LIMITS.md` is **generated** from that, and the checker fails both directions —
a template file that hand-copies a limit, and a `LIMITS.md` that has drifted from the
constants. Four controls behind it (28 total). Scanned literals are deliberately narrow:
`5000` collides with the compaction budget the template legitimately discusses, and `3`
and `500` are too common in prose — a check with false positives gets disabled, which is
worse than a narrow one that holds.

~~**B152 — the template is unversioned.**~~ Closed with B150 —
`.claude/skills/agent-assembly/assets/template/VERSION` is `1.0.0`, and every registry
row carries the version its agent was built against. A change to the standard drifts silently through
every agent already built. Each agent's spec must record the template version it was built
against, so a change produces a migration list rather than invisible divergence.

**B153 — two of our variables have zero variance, so they cannot explain anything.**
`agents.py --factors` emits each agent's configuration split into `v_` (chosen, could
have been otherwise) and `c_` (platform-fixed, context only). Run across the eight
agents it shows **`v_model` is `inherit` in all eight** and
**`v_template_built_against` is `pre-template` in all eight**. A factor with no
variance is not a factor: no volume of further runs can measure the effect of a model
choice nobody has ever varied. Learning anything about either requires *deliberately*
varying it — and the template is the cheaper of the two, because one agent built to the
standard and compared against its own predecessor is a comparison where the variable
actually moves.

**B154 — the competence layer has a protocol and no runs.** `docs/measurement-protocol.md`
fixes what the single null A/B got wrong: criteria committed before the run, arms
differing only in the agent, n fixed in advance at three or more per arm (B147 showed a
single draw disagreeing with itself), tasks drawn from the agent's own trigger including
one deliberately out of scope, and an evaluator that neither built the agent nor ran the
arms, judging unlabelled arms after catching its own planted defect. `runs.jsonl` is
empty. Every evidence cell in `docs/agent-registry.md` is still conformance or
containment — **not one says an agent does its job better than not having it.**

**B155 — an agent wrote its own registry row, and the mechanism allowed it.**
`docs/architecture-agent-factory.md` §2 names four human-owned parts and gives one reason
for all four: **they are what the agent is measured against.** The registry is one of
them. But every agent write-gate here allows `docs/`, so when `agent-builder` produced
`llm-component-architect` it also wrote that agent's registry row.

**The row it wrote was honest** — `withheld`, released `no`, evidence `none`, and it
added in its own words that the comparison is worth nothing while the evidence cell is
empty. That is not the point. An agent that can write its own row can write itself
`in use`, and nothing but its disposition stood in the way.

**CLOSED 2026-08-29.** Both gates now deny `docs/agent-registry.md` by name —
`agent-builder-scope.sh` (control `RG`, 30 rows) and the shared `docs-only-write.sh`
that `architect`, `rebuild-adjudicator` and `agent-fitness-review` depend on.

That shared gate had **no harness at all**, which made it the gate protecting the most
agents and the only one nobody could re-run. It has one now:
`.claude/validate/docs-only-write-controls.sh`, **26 cases, 26 pass**, mutation-tested —
a silent fail-open mutant scores 5/26 and a deny-everything mutant 21/26, so the harness
discriminates in both directions.

Two things it measured rather than assumed. The registry hole was real: before the fix,
case `RG` returned **allow**. And the gate's `python3` dependence **fails closed** —
cases `PY` and `PZ` confirm that with `bash` present and `python3` absent it denies
everything, including a legitimate `docs/` write. That was previously a reading of the
control flow; it is now a measurement.

**B156 — the first real use of the template found five defects in it, all now fixed
(template `1.1.0`).** Recorded because the pattern matters more than the list: a
standard nobody has built to is a draft, and the defects were invisible until an agent
tried to satisfy it.

1. **The hook bootstrap was unsatisfiable.** The skeleton invites a `hooks:` block,
   `agent-assembly` §4 forbids the builder from writing `.claude/hooks/`, and `agents.py`
   fails an agent whose hook command does not exist. **All three cannot hold on a first
   build.** The builder took the only green-and-true route available and pointed at
   `architect-rebuild-write-gate.sh` — a script named for a different agent — creating a
   coupling where tightening that gate for `architect-rebuild` silently changes this
   agent's wall. `04-wall.md` now names two legitimate routes and requires the coupling
   to be written into both agents' §2 when route B is taken.
2. **Nothing said a preloaded skill must be repo-local.** The checker resolves `skills:`
   against this repo only, which silently rules out all 84 library talents and every
   bundled skill. Decisive for this agent; now stated, with the alternative (read it at a
   step, do not preload it).
3. **The NOT-clause rule contradicted the checker for out-of-roster neighbours.** The
   checker only understands the `(use x)` form and only resolves it locally, so routing
   to a library talent is either invisible or a warning. Both forms are now described,
   with the honest note that an unverifiable route is a defect with no better alternative
   yet.
4. **`unevidenced` had no home.** `agent-shape` §1b produces a fourth provenance state
   and the template never said where to carry it. Adopted the builder's own convention: a
   *What is not evidenced here* table at the foot of each reference file, including
   `unevidenced by transfer` for a measurement borrowed from an adjacent domain — the
   more dangerous of the two, because it arrives carrying a number.
5. **`INDEX.md`'s mandatory list omitted two rules the checker enforces** — an eval
   artefact whose *filename* names the agent, and a registry row. A builder following only
   the template failed the checker twice.

**And `05-WORKED-EXAMPLE.md` concealed defect 1.** It is green only because
`worked-example-check.sh` stands up "the hook a real build would also have produced" —
quietly assuming an installation step the procedure forbids. The example is still
correct as an example; the harness is doing something the builder cannot.
