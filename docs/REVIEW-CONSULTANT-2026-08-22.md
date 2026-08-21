# External review — 2026-08-22

Commissioned as an outside pass against one question: **what stands between this
repository and production?** Reviewed at `41e9442`.

**A disclosure first, because it changes how you should weigh this.** I am not an
independent reviewer of this repository. I wrote a large part of the code
committed this week and I wrote both earlier review documents. What I can do
better than a stranger is verify; what I can do worse is see my own work
sideways. So this pass is deliberately weighted toward **the code nobody has
reviewed — mine, from yesterday** — and toward the modules the earlier reviews
never opened.

---

## 1. The verdict, in five lines

1. **The spend ceiling shipped yesterday does not work.** It is enforced per
   relay call, not per build, so a build with 20 model calls gets 20 × the
   ceiling. My own commit message claims otherwise.
2. **The Docker sandbox silently discards the environment it is given**, which
   means the design window's marking bridge and the verification data layer are
   both dead on any host with Docker — the host closest to production.
3. Yesterday's shutdown fix covers only the local sandbox; **Docker containers
   still orphan**.
4. "The engine now has logging" is two lines in the lifespan. Zero in the
   builder. No production question is answerable.
5. Everything the earlier reviews found about the platform stands, and the
   product still ends at a placeholder.

## 2. The blocking list

Three, all of which would harm a paying user rather than annoy them. Two are
mine, from yesterday.

**B1 — The cost ceiling is per model call, not per build.** `execution/relay.py:196`
creates `result` fresh inside each `run_relay`, and the guard at `relay.py:212`
compares `result.total_cost_usd + cost` — the running total *of that one relay
invocation*. `builder/loop.py:366` and `:398` pass the same `budget_usd` into
every codegen call, `builder/critique.py:212` into every critique. A seven-package
build makes at least fourteen relay invocations and more once chunking splits a
package. Sending $3.76 therefore authorises roughly **$50–80**, not $3.76.

*Breaks today:* the estimate is still a prediction with no consequence, which is
exactly the finding the fix claimed to close. Worse than before, because the
CHANGELOG now says it is handled.
*Fix:* a build-scoped accumulator — a small `Spend` object created per build,
passed into `RelayOptions`, incremented across every call, and checked against
one ceiling. Half a day. Do not ship the per-call number as a build ceiling in
the meantime; it reads as protection and is not.

**B2 — `LocalDockerSandbox.start()` ignores its `env` argument.**
`core/sandbox.py:263` takes `env: dict[str, str] | None` and the word `env` then
appears exactly once in the whole method — the parameter itself. The `docker run`
at `:286` passes no `-e` flags at all. Meanwhile `builder/loop.py:170` calls
`self.sandbox.start(app_dir, env=self.env)`, and that env carries
`SCIO_PREVIEW_MODE` and `NEXT_PUBLIC_SCIO_SHELL_ORIGIN`
(`builder/preview_bridge.py:28-29`) — the two variables that put the marking
bridge into a preview build.

*Breaks today:* `choose_sandbox()` (`core/sandbox.py:340`) prefers Docker when the
daemon is reachable. On such a host, every preview build silently produces an app
**without the bridge**, so the design window renders a preview where clicking
does nothing — and nothing reports why, because the flag was simply never
delivered. The same silence applies to the verification data layer's
configuration. This is a whole feature that works in the environment it was
developed in and fails in the one nearest production.
*Fix:* pass the allow-listed environment as `-e` flags, reusing
`child_environment()`. An hour, plus a test that asserts the flags are on the
command line.

**B3 — Shutdown stops local previews and leaks Docker containers.**
`close_all_previews()` (`core/sandbox.py:357`) walks `LocalProcessSandbox._live`
only. `LocalDockerSandbox` keeps its handles in a **per-instance**
`self._containers` (`:249`), which nothing enumerates — so containers survive the
engine that started them, holding ports and memory, and even a second provider
instance in the same process cannot stop them.
*Fix:* the same class-level registry the local provider got yesterday, and one
`docker rm -f` loop in the lifespan. An hour.

## 3. Part by part

### Part 1 — Runtime and process model
Unchanged from the earlier review and still the finding everything waits on:
workspaces on local disk, no job id, no queue, no cancellation, no resume. What
*did* change yesterday is shutdown — partially, see B3. The api gained
`onModuleDestroy`/`$disconnect` (`prisma.service.ts`); the engine gained a
lifespan (`main.py:71`).

**New, and not in the earlier review:** `ThrottlerModule.forRoot([{ ttl: 60_000,
limit: 120 }])` (`app.module.ts:28`) applies to **every** route including the SSE
build stream. A build stream is one request that lives for 46 minutes, so it
costs one token of the budget and is fine — but the same guard now also counts
the design window's polling and the wizard's per-keystroke traffic against a
single global bucket keyed by IP. Two users behind one office NAT share 120
requests a minute. **Severity: medium.** Key the throttler by workspace, not by
address.

### Part 2 — Trust boundaries
The allow-list fix (`core/sandbox.py:105-122`) is correct for the local provider
and is the right shape: an explicit tuple, everything else arriving through the
caller's `env=`. It has a test that asserts the key is absent.

But see **B2**: the Docker provider takes the same argument and drops it, so on a
Docker host the allow-list is not a tightening — the environment is simply empty,
including the parts the app *needs*. Two findings, one root: `SandboxProvider`
declares `env` in its abstract signature (`core/sandbox.py:46`) and only one of
two implementations honours it. **An abstract method whose contract one
implementation silently ignores is worse than no abstraction**, because every
caller is written against the promise. A conformance test that runs the same
assertions against every provider would have caught both B2 and B3.

### Part 3 — Data
Migration 0006 lands the indexes and the three partial unique indexes; I verified
them live in the dev database (`pg_indexes` shows
`spec_version_one_current_per_project` and siblings). The four version writes are
now transactional. This part is in good shape.

**One gap the earlier review missed entirely:** `usage_event` has no index on
`created_at`, and every billing question is "spend in a period". `UsageEvent` now
has `workspaceId` and `projectId` indexes from 0006 but a monthly invoice query
filters by time. **Severity: low now, certain later** — add
`@@index([workspaceId, createdAt])` before the first invoice, not after.

### Part 4 — Security and tenancy
The engine token (`main.py:47-64`) uses `secrets.compare_digest` and fails open
only when unset, which is the right trade for a local stack. The webhook now
refuses unsigned requests when a secret is configured and refuses entirely in
production without one.

**Not fixed and worth restating:** signature *presence* is checked, the signature
itself is not verified. The comment says so honestly. That is fine only while the
handler stays inert.

### Part 5 — Cost
B1 above is the headline. Two further gaps neither earlier review named:

- **The design window has no ceiling at all.** `budget_usd` reaches the engine
  through `/build` only; `/design/change` takes `passes` and no budget
  (`design/change.py:221`). Every directed change is unbounded. It is now
  *metered* (yesterday's fix) — so you will be able to see the overspend you
  could not prevent.
- **Intake is neither metered nor capped.** `intake/extraction.py:305` and
  `intake/questions.py:177` each run a relay per user message, and
  `intake.service.ts` writes no usage event. A wizard conversation is cheap per
  message and unbounded in length.

### Part 6 — Observability
`grep` finds **two** `log.` call sites in the whole engine, both in the lifespan
(`main.py:72, 77`), and **zero** in `builder/`. The five questions test:

| question | answerable today |
|---|---|
| how many builds ran | no |
| how long did they take | no |
| what did they cost | only per build version, by querying Postgres |
| how often do they fail | no |
| which package fails most | no |

So the honest status of yesterday's change is: **a logger exists**. Observability
does not. My own CHANGELOG entry — "It has logging for the first time" — is true
and misleading, and I am flagging it as such.

### Part 7 — Delivery
CI now exists (`.github/workflows/ci.yml`) and is deliberately uncached. I could
not observe it run — see §6 below. No container, no IaC, unchanged.

**New finding:** the engine has **no pinned dependency set**. `pyproject.toml`
declares `fastapi>=0.115`, `pydantic>=2.9` and so on with no lockfile anywhere,
so CI, a Codespace and production each resolve whatever is newest that day. The
node side has `pnpm-lock.yaml` and is fine. **Severity: medium** — this is how a
green CI and a broken production happen on the same commit. `pip-compile` or
`uv lock` and a committed `requirements.txt`.

### Part 8 — API and contracts
Unchanged: no versioning, no idempotency key on `POST /build`, SSE payloads
untyped. Yesterday's `ensureCanStart` improved one shape — a refusal before the
stream is a real status code — and that is the pattern the rest should follow.

### Part 9 — Frontend
The error boundary exists and is tested. Accessibility is thin and previously
unmeasured: **13** `aria-*` attributes, **5** `<label>` elements, **0** `role=`,
**0** `alt=` across eight pages of a form-driven wizard. **Severity: low against
the blocking list, high against the product's own claim** — STRATEGY sells
accessibility scores at the reveal (B048) for apps this product builds, while the
product itself has not been measured once.

### Part 10 — Craft
The earlier review's craft section stands. One addition: **20 `except Exception`
blocks in the engine**. I read the ones in `library/matcher.py:207` and
`library/generalize.py:271` and they are deliberate and well-reasoned — *"a
matcher that cannot decide generates; it never guesses"*. That is category 3, not
a defect.

But it is category 4 in one respect: written before cost was a first-class
concern, that rule means **a provider outage silently converts assembly into
generation** — the expensive path — with no signal and, until B1 is fixed, no
ceiling. The reasoning was right when written and is now half-right.

### Part 11 — The product against its claim
Unchanged and still the largest product gap: `/live`, `/ship`, `/settings`,
`/versions` and `/notifications` are all `PlaceholderPage` (`App.tsx:15-22`).
After a build that costs real money, every onward action is a dead end, and
ownership — the MVP promise — is the screen that does not exist.

## 4. What is good

- **The version invariant is now enforced by the database**, not by four hopeful
  code paths. Partial unique indexes are the right instrument.
- **The allow-listed child environment** is the correct shape and has a test that
  asserts the *absence* of a secret, which is the hard direction to test.
- **The refusal-before-the-stream pattern** (`build.controller.ts`) — a 409 for a
  build that should never start, an event for one that fails half-way.
- **`unjudged`** remains the best idea in this codebase: a criterion nobody could
  check rides along instead of being silently dropped. It is the pattern B1's fix
  should follow when a build stops at its ceiling.
- **The deliberate exception handling in the library** is genuinely well-reasoned
  and should not be "cleaned up" into propagating errors.

## 5. The gate, ordered by dependency

1. **B1 — build-scoped spend accumulator.** *Non-negotiable.* Everything about
   pricing rests on it, and it currently reads as done.
2. **B2 — Docker sandbox honours `env`**, plus a provider conformance test.
   *Non-negotiable.* A silently disabled feature is worse than a missing one.
3. **B3 — Docker containers stopped on shutdown.**
4. **Pin the engine's dependencies.** Cheap; prevents a class of "green here, red
   there".
5. **Ceilings on the design and intake paths**, once B1 gives you the mechanism.
6. **Real observability** — a build id on every line, and the five counters.
7. **Builds become jobs.** The large one; everything about restarts and
   cancellation waits here.
8. **Throttle by workspace, not IP.**
9. **The ship screen.** Not a platform item, but the product does not deliver its
   promise without it.
10. **Deletion path, webhook signature verification, `usage_event` time index** —
    all before the first real user's data exists.

## 6. What I could not verify

- **The CI workflow has never run.** I cannot execute GitHub Actions here. I
  verified its premises against a fresh `git archive` — the workspace sources are
  present, `packages/shared/dist` is correctly absent, `playwright` is declared —
  but the first real run may still fail on something environmental.
- **The Docker sandbox has never run a build**, here or anywhere. B2 and B3 are
  read from the code, not observed. They are unambiguous in the source, but the
  behaviour under a real `docker run` is unconfirmed.
- **No load, soak or failure testing** was performed. Everything about
  concurrency in this document is reasoned from code, not measured.
- **`design.test.tsx` is flaky** (B105): two different tests failed on two
  consecutive runs and three later runs were clean. I did not find the cause, and
  a flaky test in the CI just added will teach people to ignore red.

## 7. Where the earlier reviews were wrong

Held up: the runtime/statefulness finding, the tenancy assessment, the placeholder
gap, the missing indexes, the four-times-unprotected invariant.

Wrong or overstated:

- **"Two builds produce duplicate version numbers"** — false;
  `@@unique([projectId, number])` catches it. Corrected in place at the time.
- **"The dependency cache races"** — false. `_install_into_cache` builds in a
  pid-scoped scratch and renames, and handles the loser explicitly. I had read the
  caller and not the helper. Corrected at the time.
- **"`user.clerk_user_id` has no index"** — false; a field-level `@unique` creates
  one. My scan only read block attributes.
- **"Blocking: builds share a mutable `node_modules`"** — overstated. It is a
  property of a provider that disqualifies itself from production.

Missed entirely, and found only in this pass:

- The per-call versus per-build budget scope (**B1**) — the most consequential
  finding in any of the three documents, and it was introduced *by the fix for an
  earlier finding*.
- The Docker provider ignoring `env` (**B2**), and with it the abstract-method
  conformance gap.
- The unpinned engine dependencies.
- The intake and design paths having neither meter nor ceiling.
- Accessibility never measured.
- `usage_event` lacking a time index.

The pattern is worth naming: **four of the six things missed live in code paths
that never run during development** — the Docker provider, a second relay call, a
month-boundary query, a fresh dependency resolution. This codebase's blind spot
is not carelessness; it is that only one environment has ever been exercised.
