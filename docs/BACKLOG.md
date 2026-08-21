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
| B075 | The app fetches /intake twice per page load (React StrictMode double-mount) — free now, but it doubled the old cost | PP5 | P2 | todo |
| B076 | A feature package can fail purely on the 16k codegen output cap — the reply is cut off and the part is lost | PP5 | P0 | done |
| B077 | The estimate is optimistic on time: 14–33 min predicted, 46 min actual on a 7-part build | PP5 | P1 | done |
| B078 | Generated apps render-block on a Google Fonts stylesheet — the app waits on a third party | PP5 | P0 | done |
| B063 | Decide customer-facing pricing (markup + currency) — the estimate shows build cost, not a price | PP4 | P0 | todo |
| B079 | The operator cannot open the product from their own device: the sandbox has no inbound path and no free tunnel fits its egress — deploy the app + api somewhere reachable | PP5 | P0 | todo |
| B080 | Codespaces run mode: the whole stack with forwarded, phone-openable URLs (no deploy) | PP5 | P0 | done |
| B081 | A build has no spend ceiling — budget_usd is plumbed through and never set | PP4 | P0 | done |
| B082 | Design-window spend is never metered — preview + change costs are returned and dropped | PP4 | P0 | done |
| B083 | Two builds can run on one project and share (and wipe) one workspace directory | PP5 | P0 | done |
| B084 | The reveal's actions all lead to placeholders — /ship (own it), /live (refine), /settings | PP8 | P0 | todo |
| B085 | applyWorkspaceScope fails OPEN for upsert/createMany — make it throw instead | PP9 | P1 | done |
| B086 | A dropped connection still reads as "the build stopped" — reconnect, do not declare | PP5 | P1 | todo |
| B087 | build_package is 226 lines doing six jobs — split the attempt body out of the loop | PP6 | P1 | todo |
| B088 | "Make this the current version" is written 4x, none transactional — one helper + a partial unique index | PP3 | P0 | done |
| B089 | Type the SSE events in packages/shared — the build stream is the one path that opts out | PP5 | P1 | todo |
| B090 | DesignPage: 19 useState is a state machine — make the impossible combinations unrepresentable | PP6 | P1 | todo |
| B091 | BLOCKING: the generated app inherits the engine's whole environment (ANTHROPIC_API_KEY, SCIO_CATALOG_DB) — allow-list it | PP9 | P0 | done |
| B092 | BLOCKING: no CI — a clean-clone workflow would have caught 3 of this week's 4 Codespace bugs | PP10 | P0 | done |
| B093 | Refuse to boot with LocalProcessSandbox when NODE_ENV=production — it disqualifies itself in its own docstring and nothing enforces it | PP9 | P0 | done |
| B094 | Builds must become jobs: no id, no queue, no cancellation, no resume — a restart loses every build | PP10 | P0 | todo |
| B095 | Missing indexes on every hot path (Project.workspaceId, User.clerkUserId, UsageEvent, Notification…) | PP3 | P0 | done |
| B096 | The engine authenticates nobody — a shared secret before it is ever a separate service | PP9 | P0 | done |
| B097 | No graceful shutdown: previews orphan, streams cut without an error event, Prisma never disconnects | PP10 | P1 | done |
| B098 | The engine has zero logging; no tracing, metrics or error reporting anywhere | PP10 | P0 | done |
| B099 | No rate limiting and no per-workspace quota — the bill is unbounded at three levels | PP9 | P0 | done |
| B100 | No deletion path: soft-delete leaves workspaces, git history and usage rows; user.deleted does nothing | PP9 | P0 | todo |
| B101 | Clerk webhook accepts unsigned requests — verify BEFORE implementing the handler | PP9 | P1 | done |
| B102 | No error boundary in the app — one thrown render blanks the page after a paid build | PP2 | P1 | done |
| B103 | No API versioning and no idempotency key on POST /build — a retry is a second bill | PP3 | P1 | todo |
| B104 | Prompt injection is an unexamined surface — gates constrain output, nothing constrains the instruction | PP9 | P1 | todo |
| B105 | design.test.tsx is flaky: two different tests failed on two runs, three later runs clean — a flaky test in CI teaches people to ignore CI | PP2 | P0 | todo |
| B106 | BLOCKING: the spend ceiling is enforced PER RELAY CALL, not per build — sending $3.76 authorises ~$50-80. The fix for B081 does not do what it claims | PP4 | P0 | todo |
| B107 | BLOCKING: LocalDockerSandbox.start() ignores its env argument, so the marking bridge and the verification layer are dead on any Docker host — silently | PP6 | P0 | todo |
| B108 | Shutdown stops local previews and leaks Docker containers — _containers is per-instance and nothing enumerates it | PP10 | P0 | todo |
| B109 | The engine has no pinned dependency set — pyproject uses >= ranges with no lockfile, so CI and production resolve different versions | PP10 | P1 | todo |
| B110 | Neither the design path nor intake has a spend ceiling; intake is not metered either | PP4 | P1 | todo |
| B111 | The throttler is keyed by IP, so one office NAT shares 120 req/min — key it by workspace | PP9 | P1 | todo |
| B112 | Accessibility has never been measured: 13 aria attributes, 5 labels, 0 role, 0 alt across 8 form-driven pages | PP2 | P1 | todo |
| B113 | usage_event has no (workspace_id, created_at) index — every billing question is "spend in a period" | PP3 | P1 | todo |
| B114 | SandboxProvider declares env in its abstract signature and one of two implementations ignores it — add a provider conformance test | PP6 | P0 | todo |

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
