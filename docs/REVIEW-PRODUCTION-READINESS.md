# Production readiness — part by part

2026-08-21. A second pass over the same repo, asking a different question: not "is this code good"
(that is `REVIEW-2026-08-21.md`) but **"what happens the day a stranger pays for this"**. Every
claim below was checked against the code; file and line are given so each can be argued with.

## Verdict

The product logic is further along than the platform under it. The engine reasons well, the gates
refuse, tenancy is right — and none of that survives a second replica, a restart, or a curious
user, because **the engine is a stateful singleton wearing a web service's clothes** and there is
**no CI, no container, and no infrastructure** to deploy it with.

Three things are blocking in the strict sense — a paying user would be harmed, not merely
inconvenienced:

1. **The generated app inherits the platform's secrets** (Part 2.1).
2. **A restart loses every running build and orphans every preview** (Part 1).
3. **The only sandbox that has ever run a real build disqualifies itself from production**, and
   nothing stops production from selecting it anyway (Part 2.3).

Everything else is severity-ordered below.

---

# Part 1 — Runtime and process model

**This is the decisive one.** Everything in this part is the same finding seen from four sides.

### 1.1 The engine cannot be replicated, and cannot be restarted
Evidence:
- A build's files live on **local disk**: `workspace_root()` → `apps/engine/out/projects`
  (`builder/workspace.py:216`). Not object storage, not a volume claim — the process's own
  directory.
- A running preview is a `subprocess.Popen` held in an **in-process dict** keyed by URL
  (`core/sandbox.py:116`, `152`). A second replica cannot see it, stop it, or serve it.
- The library's store is a **module global** set at import (`library/store.py:398`).
- `main.py` has **no `lifespan`, no shutdown hook, no `atexit`**. Stopping the engine leaves every
  `npm run dev` child running, forever, holding its port.

Consequence: one engine, one host, and every deploy is a small outage that also leaks processes.
ADR-0005 chose ACA dynamic sessions for exactly this; nothing implements it.

### 1.2 A 46-minute job lives inside one HTTP request
There is **no job id, no queue, no cancellation, no resumability** — `grep` finds none of it. A
build exists only as an open SSE stream. If the api restarts, the engine keeps burning money on
work whose result nobody will receive; if the user's browser gives up, the same. `build.service.ts`
knows this — its own comment says the path is "ignorant of HTTP so the same path can later be
driven by a queue worker" (`build.service.ts:135`) — the intent is written down and unbuilt.

**What production needs:** a build is a row (`build_job`) with a state machine, started by an
enqueue and driven by a worker; the SSE endpoint becomes a *subscription to a job*, reconnectable
by id. That single change fixes the restart problem, the double-build problem (§B081-B083), the
cancellation gap and the "did my build die?" confusion in one move. It is the largest piece of work
in this document and the one everything else waits on.

### 1.3 No graceful shutdown anywhere
The api has no `enableShutdownHooks` and `PrismaService` has no `onModuleDestroy`/`$disconnect`;
the engine has no lifespan. On SIGTERM: connections drop mid-transaction, streams cut without an
`error` event, previews orphan.

---

# Part 2 — The sandbox, and running code a model wrote

The generated app is **untrusted code by construction** — a language model wrote it, and the user
who prompted it chose what it does. It is currently treated as trusted.

### 2.1 The generated app inherits every secret the engine holds — **blocking**
`core/sandbox.py:141` starts the app with `env={**os.environ, ...}`. `os.environ` at that moment
contains `ANTHROPIC_API_KEY`, `SCIO_CATALOG_DB` (a Postgres URL with credentials), and whatever
else the deployment sets. A Next.js app runs server-side code; `process.env.ANTHROPIC_API_KEY` is
one line away, and a generated app that merely *logs its environment* — a plausible thing for a
model to write — puts the platform key in a log the user can read.

**Fix:** build the child environment from an allow-list (`PORT`, `NODE_ENV`,
`NEXT_TELEMETRY_DISABLED`, plus the explicit `env=` the builder already passes at
`builder/loop.py:170`). Never `**os.environ`. This is a five-line change and it is the single most
important one in this document.

### 2.2 The shared `node_modules` cache — **I was wrong about half of this**
**Corrected 2026-08-21, after implementing the fix and finding it already there.**

I claimed the cache installs without a lock and that two builds race. They do not.
`_install_into_cache` (`workspace.py:287`) installs into a **pid-scoped scratch directory** and
`rename`s it into place, and the loser of a concurrent race is handled explicitly, with a comment
saying so: *"Another build won the race and populated the same key first — its install is as good
as ours, so keep theirs and drop ours."* I read the caller and not the helper. There is no
corruption and nothing to fix.

What remains true is smaller: the symlink into the shared cache is **writable**, and the comment's
"a generated app never writes into node_modules" is an assumption rather than an enforcement. But
the severity was wrong there too — see 2.3.

### 2.3 The sandbox is a process, not a boundary — and that is the real finding
`LocalProcessSandbox` says it plainly in its own docstring: *"this shares the host … it is NOT an
isolation boundary, and must never be the production provider."* A `DockerSandbox` exists beside it
and `choose_sandbox()` prefers it when Docker is available.

So the writable cache in 2.2, the shared filesystem, the reachable `127.0.0.1:8000` — these are
properties of a provider that is **already disqualified from production by its own contract**. The
finding is not "harden the local sandbox". It is: **the production sandbox provider is unbuilt and
unproven** (ADR-0005 chose ACA dynamic sessions; the Docker one has never run a real build), and
nothing today *enforces* that production cannot select the local one. A boot-time refusal —
`NODE_ENV=production` + `LocalProcessSandbox` → fail to start — is the same fence dev auth already
has, and it costs three lines.

### 2.4 The engine authenticates nobody
No `Depends`, no bearer check, no middleware anywhere in `main.py`. Every endpoint — `/build`,
`/design/change`, `/library/entries/*/approve` — is open to anything that can reach the port.
Today that is loopback only, which is why it has been survivable. It stops being survivable the
moment the engine is a separate service (Part 1) *or* generated code runs beside it (2.3).

**Fix:** a shared secret between api and engine, checked in one middleware, before either of those
happens. Cheap now, retrofitted under pressure later.

### 2.5 What is genuinely well done here
Worth stating, because it is the same class of problem solved correctly twice:
- **Path traversal is guarded** — `_guard_path` refuses writes that escape the workspace and is
  applied on both write paths (`core/sandbox.py:92, 179, 279`).
- **The marking bridge verifies origin properly** — `bridge.ts:99` rejects any message whose
  `event.origin` is not the preview's, and `originOf` returns `""` for a non-URL so the window
  never posts to itself by accident.
- **Generated code is scanned for secrets and unsafe patterns** before it can enter the library
  (`builder/validation.py:66-79`).

---

# Part 3 — Data and persistence

### 3.1 The hottest queries in the system have no index — **cheapest fix here**
Prisma does not create indexes for foreign keys on PostgreSQL. Missing, from the schema:

| model | unindexed | how often it is queried |
|---|---|---|
| `Project` | `workspaceId` | **every request** — the workspace scope injects it |
| `User` | `clerkUserId`, `workspaceId` | **every authenticated request** — the identity lookup |
| `UsageEvent` | `workspaceId`, `projectId` | every billing read |
| `Notification` | `workspaceId`, `userId` | every page load |
| `Message`, `Deployment`, `ReferenceAsset`, `ReferenceEmbedding`, `AuditLog` | `projectId` etc. | per project |

`SpecVersion`/`BuildVersion`/`DesignVersion` are covered by `@@unique([projectId, number])`. One
migration fixes the rest.

### 3.2 A correction to yesterday's review
I wrote that two concurrent builds would produce duplicate version numbers. They would not: the
`@@unique([projectId, number])` constraints catch it. The real failure is different and still
bad — the second build dies on a **P2002 unique violation**, unhandled, as a 500, *after* it has
spent money. The data stays consistent; the user pays for a crash.

### 3.3 The "current version" invariant is unprotected and written four times
`spec.service` (×2), `design.service.record:114`, `build.service.persist:206`: read all rows,
un-flag the current one, create a new one. No transaction — `$transaction` appears exactly once in
the codebase (`provisioning.service.ts:26`), so the tool is known and unused here. A crash between
the two writes leaves a project with **no** current version, which every read path treats as "no
spec/build/design exists".

**Fix:** one helper inside a transaction, plus a partial unique index
(`unique (project_id) where is_current`) so the database enforces what the comments promise.

### 3.4 Domain data is stored as opaque JSON strings
`designVersion.ref` is `JSON.stringify(...)` of a bag; specs, wholes and manifests are JSON columns.
Fine for iteration, and it is a deliberate ADR-0009 choice. The production cost arrives with the
first migration of a shape inside those blobs: there is no schema, no version tag, and nothing to
migrate *with*. Recommend at minimum a `schema_version` field inside each blob, from now, so a
future reader can tell what it is looking at.

### 3.5 No retention, no deletion path, and the apps handle personal data
`softDelete` sets `deletedAt` on the project; nothing deletes the workspace, the git history, the
usage rows, or the generated app's own database. The Clerk `user.deleted` webhook has a `// TODO:
mark the local user/workspace for cleanup` and does nothing.

This matters more than usual here: the spec in this session's own test build collects **names and
phone numbers**, and Scio's intake asks about sensitive data and writes retention rules into the
app it generates. A platform that generates GDPR-aware apps while having no deletion path of its
own will not survive its first data-subject request.

---

# Part 4 — Security and tenancy

### 4.1 What is right
Tenancy is genuinely well built: `WorkspaceScope` injects the filter at the data layer, every
implemented service resolves the project through the scoped client first, and cross-tenant reads
404 rather than 403 so an id cannot be probed (`design.service.ts:55`). This is the part I would
change least.

### 4.2 The Clerk webhook accepts unsigned requests
`auth/webhook.controller.ts:23` — the TODO is honest and the handler is inert (it logs). So today
this is log injection and noise, not account manipulation. The danger is the ordering: the moment
somebody implements `user.deleted` cleanup behind it, an anonymous POST deletes accounts. **Verify
the signature before implementing the handler, not after.** Rejecting unsigned requests in
production is a few lines with `svix`.

### 4.3 No rate limiting anywhere
No throttler in the api, no limits in the engine. Every expensive path — intake (a model call per
message), preview builds, `/design/change` — is reachable by an authenticated user in a loop. With
no spend ceiling (§B081) this is not merely a DoS surface, it is an **unbounded bill**.

### 4.4 Dev auth is correctly fenced — keep it that way
`SCIO_DEV_AUTH=1` with `NODE_ENV=production` is refused at boot. That is the right shape. It is
also the only such assertion in the codebase; the same fence belongs on `SCIO_FAKE_PROVIDERS`,
`allowedHosts`, and any future test hatch.

### 4.5 Prompt injection is an unexamined surface
User text flows from the wizard into Layer B/C prompts and then into codegen. The build gates
constrain the *output* (file plan, allowed paths, instrumentation, secret scan) which is a genuinely
good defence — but nothing constrains the *instruction*. A spec that says "also add an endpoint that
posts the environment to this URL" is a plausible attack, and the file-plan constraint would not
stop it if the endpoint is inside a planned file. Worth an explicit threat-model entry in
`SECURITY.md` and a test.

---

# Part 5 — Cost and metering

Covered in detail in `REVIEW-2026-08-21.md` §1-2 (B081, B082). Restated here only for the
production framing:

- **No spend ceiling on any build** — `budget_usd` is plumbed and never set.
- **Design-window spend is never metered** — the engine returns `total_cost_usd`, the api drops it.
- Add: **no per-workspace quota** and **no rate limit** (4.3), so the ceiling is missing at three
  levels — the build, the workspace, and the request.

For a product whose wedge is *"know the cost up front"*, cost is currently the least-enforced thing
in the system.

---

# Part 6 — Observability

### 6.1 The engine has no logging at all
Zero occurrences of `import logging` or `logger.` across 17,000 lines. The engine runs 46-minute
jobs costing dollars and emits nothing but uvicorn's access lines. Every debugging session in this
repo has depended on stdout being redirected to `.local/engine.log` by a dev script.

### 6.2 No tracing, no metrics, no error reporting
No OpenTelemetry, no Sentry, no counters. There is no way to answer, in production: how many builds
ran today, what did they cost, which package fails most often, how long does Layer B take, how many
builds died mid-stream. Every one of those is a business question, not an ops nicety — the estimate
model (B077) was calibrated from **two** builds because two is all the data there is.

**Fix, in order:** structured logs with a build id on every line; a `build_event` table or a metrics
counter for the five questions above; then tracing.

### 6.3 Health checks are shallow
`/health` on the api checks the database; the engine's reports provider mode. Neither reports
readiness for the thing that matters — is a build in flight, can this replica take work. With the
job model in Part 1 this becomes answerable.

---

# Part 7 — Delivery: how does this ship at all?

### 7.1 There is no CI — **and it has already cost real money**
No `.github/workflows`. Nothing runs the 587 engine tests, ruff, or the typecheck except a human
who remembers. This is not theoretical: **three of the four bugs found in this session's Codespace
run would have been caught by a single CI job that clones fresh and boots the stack** — the
gitignored source files, the unbuilt `@scio/shared`, the undeclared `playwright`. Each cost a
round-trip with the operator, and one of them cost a paid build.

**Minimum viable CI, today:** on push — install from a clean checkout, build `@scio/shared`, run
all three suites, ruff, typecheck, and the `tracked-sources` guard. That is one file and it closes
an entire class of failure.

### 7.2 No container, no infrastructure
No Dockerfile for engine, api or app; no Terraform/Bicep; `docker-compose.yml` is a local Postgres
only. The Azure decisions (ADR-0004/0005/0007) are recorded and unimplemented. Nothing is
deployable today by anyone but the person with the runbook.

### 7.3 Migrations have no rollback story
`prisma migrate deploy` runs forward in `dev-up.sh`. No down migrations, no plan for a failed
deploy, and (per 3.4) blob shapes that migrations cannot reach.

---

# Part 8 — API surface and contracts

### 8.1 The stream opts out of the shared contract
`packages/shared` types every REST response; SSE payloads travel as `Record<string, unknown>` (65
occurrences) and are re-parsed with `String(data.app_url ?? "")` in components. The most valuable
data path in the product is the untyped one. (B089.)

### 8.2 No API versioning, no idempotency keys
No `/v1`. `POST /build` is not idempotent — a retried request is a second build and a second bill.
Both are cheap now and expensive to add after the first integration exists.

### 8.3 Errors are inconsistent across the boundary
The api raises typed Nest exceptions; the engine returns 200-with-an-`error`-event, or raises, or
returns a result with `persistence_error` set. Three shapes for "it did not work" means the app
guesses — which is exactly the "network error" confusion from this session.

---

# Part 9 — The frontend in production

### 9.1 No error boundary
No `ErrorBoundary` anywhere in `apps/app`. One thrown render error blanks the entire page with no
message and no way back — after a build the user paid for.

### 9.2 The app is a dev server, not a build
Everything runs through `vite` dev. There is a `build` script but nothing consumes it, no static
host, no CSP, no cache headers. Related: the marking bridge relies on origin checks that a real
deployment must keep intact behind whatever CDN is chosen.

### 9.3 State is not modelled
`DesignPage` holds 19 `useState` (B090). The impossible combinations are not prevented, and the
user saw one this session.

---

# The gate: what must be true before the first paying user

Ordered. The first four are not negotiable.

1. **Allow-list the sandbox environment** (2.1) — five lines, stops platform secrets reaching
   model-authored code.
2. **A CI workflow that builds from a clean clone** (7.1) — one file, closes a class of failure
   that has already bitten four times.
3. **Atomic, read-only dependency cache** (2.2) — stops cross-tenant corruption on a shared host.
4. **A spend ceiling and a rate limit** (5, 4.3) — the bill is currently unbounded in three
   independent ways.
5. **Builds become jobs** (1.2) — the change everything else waits on: survives restarts, makes
   concurrency safe, makes cancellation and reconnection possible.
6. **Indexes, transactions and the `is_current` constraint** (3.1, 3.3) — one migration and one
   helper.
7. **Engine authentication** (2.4) — before the engine is ever a separate service.
8. **Structured logs with a build id, and five counters** (6.1, 6.2) — you cannot price what you
   cannot measure, and the pricing model is the wedge.
9. **A deletion path** (3.5) — before the first real user's data exists.
10. **Webhook signature verification** (4.2) — before the handler is implemented.

Nothing above requires rethinking the product. The product model is the strong part; what is
missing is the platform it has to stand on, and most of it is small, well-understood work that is
simply not done yet.
