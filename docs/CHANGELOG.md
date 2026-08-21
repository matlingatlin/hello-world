# Changelog
Running log of decisions and changes for Scio. Newest first.
See CLAUDE.md, "Documentation & checkpoint protocol", for how this is maintained.

## [unreleased]

### Fixed
- 2026-08-21 — **B076 fixed this for packages and repeated the mistake for chunks.**
  The first real build driven from a Codespace — the whole product, against Claude, from the
  operator's own browser — came back *4 of 5 parts work*. `pkg_feature_booking` failed with the
  exact message B076 exists to make impossible: *"the reply hit the output-token limit and was cut
  off — Return the files complete, and shorter."*

  The cause is in B076's own retry loop. It asked `_generate_chunk` for the **same paths** on every
  attempt, so an over-budget chunk was sent twice unchanged and hit the cap twice — while
  `CHUNK_TOKEN_BUDGET`'s docstring, two hundred lines up, says why that cannot work: *"a package
  that does not fit cannot be made to fit by asking again."* True of packages, equally true of
  chunks, and the code did it anyway.

  A chunk that comes back truncated is now **halved**, and the halves go back on the front of the
  queue: 7 files → 3 → 1. Only a single file that still will not fit is retried at the same size
  (`CHUNK_RETRIES`), because there is nothing left to split and half a file on disk is the thing
  that must never happen. Bounded by construction — at most 2n-1 calls for n files — and the
  existing cost-guard test now pins all five calls of a package that cannot fit at all.

  Also from that run, both good: the estimate held for a **third** independent build
  (~$0.86–$3.18 estimated, **$1.85** spent, 176k tokens), and the preview URL rewrite works —
  the design window embedded `https://<codespace>-55917.app.github.dev`, not loopback.

  engine 587 (+2), ruff clean.

- 2026-08-20 — **"The build stopped — network error", about a build that was running fine.**
  The first real build from a Codespace died in the browser after a minute or two, twice: once on
  the design preview, once on the delivery build at "0 of 5 parts done". Nothing was wrong with
  either — the api logged no failure, and `design.service` never reached its
  *"preview … produced nothing"* warning, so `finished` had arrived. What broke was the **stream**.

  A real build is silent for minutes at a time. The engine learned this on its own hop, where
  undici gives up after 300s of quiet, and fixed it with a comment frame every 15s — and its
  comment names the next victim exactly: *"every SSE client ignores it — including proxies, which
  drop idle connections for the same reason"*. The api → browser hop never got one. On localhost
  nothing sits in between, so it could not show up here; put a Codespace's port forwarder in the
  middle and a quiet minute kills it.

  `apps/api/src/common/sse.ts` now opens every stream with the same heartbeat, used by both the
  build and the design-preview controllers, plus `X-Accel-Buffering: no` for proxies that would
  otherwise hold a stream until it is "big enough". The timer is cleared when the client leaves —
  the build itself keeps running, which is the promise the build screen already makes.

  api 97 (+4).

- 2026-08-20 — **A design build died on an optional dependency that was never declared.**
  Clicking "shape the design" in the Codespace returned `No module named 'playwright'`. Playwright
  is the preview's senses — screenshot, classified console, click resolution — and `preview.py`
  says in its own docstring that it is optional, with `is_available()` there to ask. Nothing on
  the build path ever asked: `SandboxPreview.observe()` imported it regardless. So a build that
  had genuinely succeeded, with the app built and being served, reported a missing Python module.

  It is now declared (`apps/engine[vision]`) so it can be installed at all, and the build path
  asks first: without a browser it returns `Observation.blind()` and records
  *"the browser checks (console, screenshot) — nobody opened the page"* as an **unjudged**
  remainder, the same pattern already used for an interaction criterion nobody could drive. An
  empty console because nobody looked must never read as a clean one.

  The tell was in the test counts: the suite went 582 passed / 6 skipped → 576 / 15 the moment
  this sandbox's venv was rebuilt from the declared extras. Nine interaction-channel tests had
  been passing on a Playwright somebody installed by hand, years of runs ago, and never wrote
  down — the same shape as the gitignored sources and the pre-built `dist/`. With the extra
  declared and installed: **585 passed, 6 skipped**.

- 2026-08-20 — **Three source files had never been committed, and nobody could have noticed.**
  `.gitignore` carried a bare `workspace/` under "Scratch". A pattern without a leading slash
  matches at every level, so it also matched `apps/api/src/modules/workspace/` — and
  `workspace.module.ts`, `workspace.controller.ts` and `workspace.service.ts` existed only on the
  machine they were written on. The rule one line higher already carries the comment explaining
  exactly this, from the time `build/` swallowed `src/modules/build`; the scratch rule never
  learned it. Anchored to `/workspace/` (the engine's real workspaces live in
  `apps/engine/out/projects`, already ignored), and the three files are committed.

  Nothing could have caught it: every test and every dev run reads the working tree, where the
  files are present. So there is now a test that reads what a *clone* gets —
  `apps/api/test/tracked-sources.spec.ts` compares `git ls-files` against the `.ts`/`.tsx` files
  on disk under `apps/api/src`, `apps/app/src` and `packages/shared/src`, and names any file the
  repo does not have. Proven to fail: un-staging `workspace.module.ts` turns it red. A separate
  one-off check over a `git archive` of the tree confirmed all **169** relative imports in those
  three trees resolve in a fresh checkout.

  Also, the engine's venv is repaired by `dev-up.sh` rather than assumed: a venv directory is
  created before its packages land, so an install that dies in between leaves one that exists and
  is empty — which is what "No module named uvicorn" meant on the second Codespace. The check is
  an `import`, not a directory test. Verified by emptying the venv here and starting over.
  `post-create.sh` no longer stops at its first failure either; it reports which steps failed and
  says that `dev-up.sh` repairs the ones that matter, because a half-finished setup that says
  nothing is what produced the confusing error in the first place.

  api 93 (+3).

### Added
- 2026-08-20 — **Three source files had never been committed, and a .gitignore rule was why.**
  The third Codespace run failed on `Cannot find module './modules/workspace/workspace.module'`.
  The file was there on this machine and had never been in the repo: `.gitignore` carried a bare
  `workspace/` for scratch directories, and an unanchored pattern matches at **every** level — so
  it also matched `apps/api/src/modules/workspace`, and quietly excluded the controller, the module
  and the service. The rule one line above it already carried the comment explaining exactly this,
  written when a bare `build/` excluded `src/modules/build`. The lesson was in the file and the
  next rule did not learn it. Now `/workspace/`, anchored, and the three files are committed.

  Guarded, because twice is a pattern: `apps/api/test/tracked-sources.spec.ts` compares what is on
  disk under `apps/api/src`, `apps/app/src` and `packages/shared/src` against `git ls-files` and
  names anything missing. It reads what a **clone** gets, which is the thing no other test does —
  every suite and every dev run reads the working tree, where the file is right there. Proven to
  fail by un-tracking one file, then restored. Verified separately that all **169** relative
  imports across api, app and shared resolve inside `git archive` of the tree.

  **Also: an empty venv is not a missing dependency.** The run before that died on
  `No module named uvicorn` — the venv directory existed and held nothing, because the directory is
  created first and the packages land second. `dev-up.sh` now checks by *importing* rather than by
  looking for the directory, and installs when the import fails. `post-create.sh` was rewritten to
  match: every step reports its own failure and the script keeps going, instead of aborting halfway
  and leaving a machine that looks set up. Verified by emptying the venv here and running from that
  state.

- 2026-08-20 — **`dev-up.sh` now repairs a half-built machine instead of trusting one.** The
  second Codespace failed with `No module named uvicorn`: the venv had been created and never
  filled, because `post-create.sh` died somewhere before its pip install and said nothing. Two
  changes, one principle — **a fresh clone has to work anywhere, not only where setup happened to
  succeed**. `dev-up.sh` checks the venv by importing `uvicorn, fastapi` (a directory is not an
  install) and rebuilds it if that fails; `post-create.sh` no longer aborts on the first bad step
  but runs them all, names the ones that failed, and says dev-up will retry. Verified by emptying
  the venv here and starting from that state: `installing scio-engine … installed`, then engine,
  api and app all `200`.

- 2026-08-20 — **A fresh clone could not build the api at all: nobody had ever started from one.**
  The second Codespace run died with 30 × `Cannot find module '@scio/shared'`. The shared package
  is the API contract both sides compile against, its `main`/`types` point at `dist/`, and `dist/`
  is gitignored — so a fresh clone has none and `pnpm install` does not build workspace packages.
  It worked here only because somebody built it once, weeks ago, and every run since has been
  standing on that. `dev-up.sh` now builds `@scio/shared` when it is missing **or older than its
  sources**, which also closes the quieter version of the same bug: editing the contract and
  compiling against yesterday's types. Verified by deleting `dist/` and starting from scratch.

  Worth naming: both Codespace failures were invisible to every test suite, because tests run
  where the artefacts already exist. The environment that had never been used is the one that
  found them — same lesson as the first click-through (B064).

- 2026-08-20 — **The first real Codespace run: `dev-up.sh` gave up on the api while it was
  still building.** `✗ api did not come up in 120s`, and nothing was wrong — a fresh Codespace
  compiles the whole Nest api from scratch on two cores, which takes longer than that. The 120s
  was measured in one sandbox and quietly assumed everywhere. A timeout only bounds *failure*
  (`wait_for` returns the moment the health check passes), so waiting longer costs a healthy
  start nothing: engine 120s, api 420s, app 180s, each overridable (`SCIO_WAIT_API=900 …`).
  A timeout now also prints the tail of that server's own log and the knob to turn, because
  "did not come up" is a dead end and the log is a diagnosis. Documented in
  `RUNBOOK-CODESPACES.md`; found by the operator on the first real run, which is the only place
  it could have been found.

- 2026-08-20 — **B080: the stack runs in a Codespace, with URLs you can open on a phone.**
  Yesterday's answer to "let me click it from my phone" was a measured *no* (B079). A Codespace
  answers it from the other side: it runs the stack **and** forwards ports, so each one gets an
  `https://<name>-<port>.app.github.dev` origin — no deploy, no hosting decision, no key, and
  free clicking because the engine falls back to its stand-ins when there is no key.

  `.devcontainer/` builds an image with PostgreSQL 16 + pgvector (the api's first migration begins
  `CREATE EXTENSION "vector"`) and adds Node 20 and Python 3.11 as features; `post-create.sh`
  installs the workspace and the engine's venv. `scripts/dev-up.sh` is the **same command** there —
  it sources `scripts/codespace-env.sh`, which derives `VITE_API_URL`, `CORS_ORIGINS`,
  `APP_ORIGIN`, the bind hosts and a preview-URL template from `$CODESPACE_NAME`. Nothing is
  hard-coded and every value goes through `${VAR:-…}`, so the local path is byte-for-byte what it
  was: `dev-up.sh` with no Codespace still prints `http://127.0.0.1:5173`.

  Two things needed more than config. **Vite** has refused an unknown `Host` since 5.4.12, so
  `.app.github.dev` is named in `server.allowedHosts` and HMR is pointed at port 443 — verified
  live: the forwarded host gets `200`, an unknown one still gets *"Blocked request"*. And the
  **preview** runs on a random loopback port that a phone cannot reach, so
  `core/public_url.py` translates what the engine *publishes* (`http://127.0.0.1:41337` →
  `https://<name>-41337.app.github.dev`) while it keeps dialling loopback itself. It rewrites
  nothing without a template, and never touches a URL that is already public.

  Verified by running the stack with `CODESPACE_NAME` set: the api returns
  `Access-Control-Allow-Origin` for the forwarded app origin and nothing for a stranger, the app's
  module graph resolves `VITE_API_URL` to the forwarded api, both servers answer on the
  container's non-loopback address, and the engine process carries the template. **Not** verified:
  an actual Codespace boot — this sandbox cannot create one, and the runbook says so rather than
  implying otherwise.

  The one step that cannot be automated: a forwarded port is **private** by default, and a private
  port answers a cross-site `fetch` with GitHub's sign-in page, which the app honestly reports as
  the api being down. `gh codespace ports visibility 3000:public` — port visibility cannot be set
  from `devcontainer.json`. `dev-up.sh` prints that line when it sees a Codespace.

  engine 592 (+10), api 90, app 74, ruff and typecheck clean.
  Runbook: `docs/RUNBOOK-CODESPACES.md`.

### Investigated
- 2026-08-20 — **The stack cannot be exposed from this sandbox (B079).** The task was a
  phone-openable URL in FAKE mode; the outcome is a measurement, not a URL. The stack came up
  free and correct (`/health`: `"providers":"fake"`, `"builder":"standin"` — forced with
  `SCIO_FAKE_PROVIDERS=1`, so the operator key already in `apps/engine/.env` could not be used
  by accident), and then every route out failed on the same rule: **only ports 80 and 443 leave
  this sandbox**, 443 is TLS-terminated and re-issued by the egress gateway, and there is no
  inbound path or platform preview at all.

  Four tunnels, four different ports: `cloudflared` needs **7844** and said so itself
  (`UDP … FAIL`, `TCP … FAIL`, `Cloudflare API 443 PASS`; `--protocol http2` changes the
  transport, not the port); `localtunnel`'s control plane answered over 443 and handed out port
  **25105**, which times out; `tunnelmole` dials `wss://…:**8083**` and hangs without ever
  opening a socket; the SSH services (`serveo`, `localhost.run`, `pinggy`) need port 22, and
  there is no `ssh` binary. `ngrok` is named as unsupported through this proxy in
  `/root/.ccr/README.md` and needs an account token that cannot be created from in here.

  The one useful positive: a plain `Upgrade: websocket` over HTTP/1.1 on 443 returns **101
  Switching Protocols** through the gateway, so a WebSocket relay on 443 is the shape that
  *would* work — there is no signup-less service offering it. Negotiating h2 silently degrades
  the upgrade to a `200`, which is worth knowing for whatever we deploy.

  No code changed: with no public origin to point at, the `VITE_API_URL` / `CORS_ORIGINS` /
  `APP_ORIGIN` overrides the kickoff allowed would have been config nothing exercises. Recorded
  in `docs/RUNBOOK-LOCAL.md` ("Reaching it from another device") with the port matrix, and as
  **B079**: deploy the app *and* the api — the browser calls the api directly — and note that
  Vite refuses an unknown `Host` since 5.4.12, so a public hostname needs `server.allowedHosts`.

### Fixed
- 2026-08-20 — **B076–B078: no silent package loss, a calibrated range, and fonts we serve ourselves.**

  **B076 — a package cannot be lost any more.** Two rules, both deterministic. First,
  `check_files_complete` judges what a package wrote against `planned_files`, the same file plan the
  manifest's package→file map is built from: a missing or empty file is a named, retryable finding.
  A package that comes back with six of its eight files is not a smaller package, it is an app
  missing a form — and every other gate only ever looked at the files that *did* arrive. Second,
  a package whose files will not fit in one reply is generated in **bounded chunks**
  (`file_chunks`, `CHUNK_TOKEN_BUDGET = 11000`), each chunk retried on its own before the package
  fails. The first real run proved the old approach could not work: the reply hit the 16k cap, the
  model was told to "return the files complete, and shorter", it hit the cap again, and
  `pkg_feature_workout` was gone. Eight files of real code do not become five files of real code
  because the prompt asked nicely. Chunk two is handed chunk one's code verbatim so exports and
  names line up.

  Writing the check found the same bug in our own tests: `feature_code` had always written **five of
  the eight files** a feature package plans, and the docstring said so out loud. The fixtures are
  complete now, and `conftest.complete_reply` / `scripted_codegen` let a focused test stay focused
  without describing an impossible build.

  **B077 — the estimate range now contains the builds it claims to predict.** Calibrated, not
  chosen: 5 generated + 1 assembled took 10.8 min against a 13.6 min point (ratio 0.79); 7 generated
  took 45.9 min and $2.69 against 18.5 min / $1.39 (ratios 2.48 and 1.93). The old band of
  0.75–1.8 excluded *both* real measurements — it advertised "up to 33 minutes" for a 46-minute
  build and "up to $2.51" for one that cost $2.69. Now 0.7–2.6, with a test pinning all three
  observations inside it and a second test keeping the band under 4.5× so it still says something.

  **B078 — a delivered app no longer waits on a font CDN.** A real build wrote
  `@import url('https://fonts.googleapis.com/…')` into `globals.css`; the app then blocked its first
  paint on a host the sandbox refuses, for **12,692 ms**. The design-tokens contract and the codegen
  house rules now say to use `next/font` (downloaded at build time, served from the app), and
  `check_delivered_quality` fails any package that ships an `@import` or `<link>` to a font CDN —
  because a rule the model is merely asked to follow is followed most of the time.

  engine 572 (+10), api 90, app 74, typecheck and ruff clean.

- 2026-08-20 — **B071–B074 closed: the build's own cost, estimated-vs-spent, and a cache with a key.**
  Three gaps between what shipped earlier and what the kickoff's definition of done literally asks
  for.

  **A build's cost is on the build.** `build_version.cost_usd` and `tokens` (migration `0005`),
  written in `persist()` beside the honest status. `usage_event` keeps being the per-workspace
  metering ledger; the columns are the build's own provenance, readable without a join. Both
  nullable, because a build recorded before they existed genuinely has no figure and `0` would be a
  claim rather than an absence.

  **The reveal compares.** `approve()` now freezes the estimate into the spec version's
  `assumptions` beside the whole — read server-side from the project, never trusted from the client,
  the same reason `assumed` is extracted there. So the reveal shows the estimate the user actually
  approved against rather than whatever the draft says by the time a build finishes. On the build
  from last night that reads: **`version 1 · b3699f8e66bc · estimated ~$1.05–$2.51 · $2.69 spent ·
  249k tokens`**. With no estimate to compare against it shows the spend alone rather than inventing
  one.

  **The cache has a key.** `draft_confirmation_hash` — a sha256 over stable-sorted JSON of the spec
  the cached whole and estimate describe. Invalidation was already correct by construction (every
  writer of `draft_spec` writes them together); the hash is what keeps it correct the day a fourth
  writer appears, and the failure it prevents is the worst kind — a confident summary of a spec that
  no longer exists. A test writes `draft_spec` behind the service's back and asserts exactly one
  recompute, a fresh whole, and a free load after it.

  engine 562 (+1), api 90 (+3), app 74 (+2), typecheck and ruff clean.

  **Measured live, and one measurement corrected.** `GET /intake` answers in **7–16 ms** with no
  model call. The browser, however, took 12.7 s to render the review screen — and that turned out to
  be nothing to do with the product: the page blocks on a Google Fonts stylesheet this sandbox
  refuses, which fails after **12,692 ms**. Of the 33 requests a full page load makes, the api
  accounts for 43 ms and Vite for 101 ms. Worth knowing on its own — a render-blocking external font
  means the whole app waits on a third party — but it is not B071, and reporting it as B071 would
  have been wrong.

- 2026-08-20 — **the keep-alive, B073 and the estimate, all measured on one real 7-part build.**
  45m51s, `claude-sonnet-5`, one pass.

  **The keep-alive works.** The build survived a **24-minute silence** between
  `pkg_connector_notifications` and `pkg_feature_general` — five times the 300-second limit that
  had torn down the two builds before it. Proven on the wire beforehand as well: 4 keep-alive
  frames in 75 seconds from the live engine while Layer B was thinking.

  **B073 is closed with a real number.** `usage_event` has its first row ever: **$2.69,
  248,952 tokens, claude-sonnet-5**, and the reveal shows what the build actually spent beside the
  version it produced. Before this the figure was computed, passed to the browser, and dropped.

  **What the build produced**, honestly: 5 of 7 parts work, `pkg_feature_general` needs a look (it
  has operations and no test file), and `pkg_feature_workout` **failed** — *"the reply hit the
  output-token limit and was cut off"*. That is a part lost for a purely mechanical reason: a
  feature package writes eight files and `CODEGEN_MAX_TOKENS` is 16,000. Recorded as **B076**.

  **The estimate is optimistic on time.** It predicted 13.9–33.3 minutes and $1.05–$2.51; the build
  took **45m51s** and cost **$2.69**. Cost was 7% over the top of its range, which is defensible for
  a range; time was 38% over, which is not. Recorded as **B077**.

  One promise verified by accident: the watching client died six minutes before the end (its own
  timeout), and the api still consumed the rest of the stream and persisted the build version, the
  honest status and the usage row. "You can leave this page — the build keeps running" is true.

- 2026-08-20 — **a real build was being killed by a five-minute timeout.** A build is silent while
  Layer B runs, then Layer C, then the first package — minutes before a single `progress` event
  exists. Node's `fetch` (undici) gives up on a response body after **300 seconds** without a
  chunk, so a build whose first event took **313 seconds** had its stream torn down mid-flight, and
  the build view told the user *"The build stopped"* about a build that was working perfectly. The
  api logged `produced no result: terminated`, the engine logged nothing at all, and the app it had
  been writing was thrown away.

  Only a real run could surface it: with fake providers nothing is ever quiet for five minutes, so
  every test and every free click-through passed. The engine now emits an SSE keep-alive comment
  every 15 seconds while a stream is thinking (`main.with_heartbeat`). A comment frame carries no
  `data:`, so both the api's `parseFrame` and the app's `streamSse` already drop it — and it stops
  proxies dropping idle connections for the same reason. The pending step is *shielded*, so the
  timeout is a moment to speak rather than a reason to cancel the work in flight.

  Also recorded (B075): the app issues **two** `GET /intake` per page load, because React
  StrictMode mounts twice. Harmless now that the response is a database read; before B071 it
  doubled the cost of opening a page.

  A correction to yesterday's note: the browser timings in that run measured the **Vite dev server**,
  not the api. Every page in this sandbox takes ~12.7s to render, including the projects list, which
  calls nothing. The api numbers stand and were re-measured directly: `GET /intake` 12.7s → 0.007s,
  with **zero `/architecture` calls** across three browser page loads.

- 2026-08-19 — **B071–B074: what the first real run surfaced.** Each was measured, not guessed.

  **B071 — a page load no longer costs a model call.** `GET /projects/:id/intake` re-derived the
  confirmation prose and the cost estimate on every request, which is a real Layer B + Layer C run:
  **12.7 seconds and money, every time somebody opened or refreshed the wizard or the review
  screen.** They are derived from the spec, so they are now computed when the spec CHANGES and
  stored beside it (`project.draft_whole` / `draft_estimate`, migration `0004`). Every path that
  writes `draftSpec` writes them in the same update, so they cannot describe an older spec; a
  project specced before this computes once and stores the result. Re-measured on the same project:
  **12.7s → 0.008s**, and a project taken through the wizard afterwards never pays at all, because
  the turn that finished the spec already stored them.

  **B072 — the wizard no longer states a number it does not have.** While that request was in
  flight it said "Nothing yet — answer the first question" and "0 of 6 core answers", with Continue
  disabled, to someone whose spec was complete. "Not loaded" and "nothing answered" were the same
  state. They are now distinct: "Reading your project…", and the same on the review screen, which
  used to render an empty field list with an approve button under it.

  **B073 — the product can finally say what a build cost.** The engine computed `total_cost_usd`,
  the api passed it to the browser, and it was dropped there: `usage_event` had zero rows since
  ADR-0009 defined it. Tokens are now carried the same five hops the cost already travelled
  (relay → loop → result → orchestrate → pipeline), a finished build writes one `usage_event`
  (cost, tokens, model), and the reveal shows what it actually spent beside the version line. A
  build that spent nothing writes no row — `$0.00` would read as a measurement rather than as
  "every part came from the library".

  **B074 — a test fixture is not a leak.** The contribute gate refused `pkg_auth`, which had passed
  all five build gates, because its model-written test contained `guest@example.com` and
  `https://app.example.com/auth/callback` — names RFC 2606 and RFC 6761 reserve for exactly this.
  Those are now exempt; a real domain still fails. Verified against the actual artefact: the
  package the first run refused now contributes as `auth.1.1`.

  **Two things found while fixing those, both worse than what they were found under:**

  - The gate's "what looks like an API key" rule matched only the legacy `sk-<alnum>` shape. A real
    `sk-ant-api03-…` or `sk-proj-…` key stopped the match at the first hyphen and **sailed through
    the one check meant to stop exactly that**. Now matches the modern shapes and Google's.
  - The `.env` loader added an hour earlier made the engine's test suite pick up an operator's
    configuration: the relay's ordering tests asserted against whatever `SCIO_MODEL` named, and
    `test_api.py` started making **real model calls** — 100 seconds and real money for a unit-test
    run. `SCIO_SKIP_ENV_FILE`, set by `conftest`, makes the suite hermetic again (31 relay/api
    tests: 99s → 1.3s). The library store is now isolated per test for the same reason.

  engine 563 tests (+8), api 87 (+4), app 72 (+2), typecheck and ruff clean.

- 2026-08-19 — **the engine now reads `apps/engine/.env`.** `docs/RUNBOOK-FIRST-RUN.md` has said
  since it was written that this file is "the whole configuration for a real run", and nothing read
  it: `config.py` looked only at `os.environ`, so a correctly-filled `.env` produced a stand-in
  build and a `/health` reporting `providers: fake` — the exact symptom the runbook's own
  troubleshooting table points at, with no way to tell a missing key from an unread one. Found the
  first time the product was brought up in real mode; it blocked bring-up entirely.

  The loader is deliberately tiny and dependency-free (`export` prefixes, comments, blank lines and
  surrounding quotes, nothing else — this is a file that holds a key, and a shell parser nobody
  audits does not belong in it). Two rules keep it compatible with ADR-0004's "never from committed
  files": the file is gitignored and never shipped, and **a variable already in the real environment
  always wins**, so a deployment's secret can never be shadowed by a stray local file. `/health`
  now also reports `config_from_env_file` — the NAMES it took from the file, never the values — so
  "the key never arrived" and "the key is wrong" stop looking identical.

### Added
- 2026-08-19 — **the first full REAL run: the whole product, in a browser, against Claude.** Engine
  + api + app + local Postgres + dev auth, `claude-sonnet-5` at one pass, no external services.
  `/health` reported `providers: real`, `builder: model`. Walked new project → wizard → review →
  "Just build it" → build → reveal.

  **What worked.** Intake with a real model took **10 turns** and filed every answer correctly —
  `data_ownership_sensitivity` came back as `{owner: me, sensitive: true, kinds: [names, phone
  numbers]}` from one sentence, and `role_permissions`, `scheduling`, `compliance` and
  `notifications` all landed in their own slots. The review screen showed a genuine paragraph of
  prose ("…the whole flow revolves around sittings scheduled every 30 minutes between 17:00 and
  22:00, Stockholm time"), 17 spec rows and an estimate of **~$0.49–$1.17 · ~10–24 min · 6 parts ·
  1 reused · 5 built** — the library hit is real: `pkg_feature_booking` was ASSEMBLED from the seed
  blueprint with no model call. The build took **~11 minutes** and finished **6 of 6 parts
  passing**, no remainders, `standin: false`. The reveal embedded the running app, which serves
  instrumented HTML and renders "Book your table". The generated code is real Next.js — server
  actions, zod validation, RLS-aware data access, `data-scio-id` on every element.

  **What the run surfaced** (recorded as B071–B074, nothing else changed per the kickoff):

  - **Every load of the wizard or the review screen costs a real Layer B + Layer C model call and
    ~12 seconds** (measured: 10.6s, 12.7s). `GET /projects/:id/intake` re-derives the whole and the
    estimate from scratch on each request instead of storing them with the draft spec. A page
    refresh now costs money.
  - **While that is in flight the wizard says "Nothing yet — answer the first question" and "0 of 6
    core answers"**, with "Continue to review" disabled. That is not a blank panel, it is a false
    statement about the user's own data — the one thing this product's screens are not allowed to
    do.
  - **A build's actual cost is recorded nowhere.** `usage_event` is empty, `build_version` has no
    cost column, and `honest_status` carries none. The engine computes `total_cost_usd` and the api
    passes it through to the browser, where it is dropped. The product can predict a cost and never
    tell you what it really spent.
  - **The contribute gate refuses real packages over test fixtures.** `pkg_auth` passed all five
    build gates and was rejected because its model-written test contains `guest@example.com` and
    `https://app.example.com/auth/callback` — names RFC 2606 reserves for exactly this purpose. The
    leakage rules cannot currently tell a fixture from a customer's address.

- 2026-08-19 — B061: **contribute-back — the library grows from real builds.** The component
  library is the product's nave (ADR-0014): the more of an app that comes from curated, tested
  parts, the cheaper and more predictable a build is. It had four hand-written entries and no way
  to get a fifth. Now every delivery build offers its work back, and what survives a sequence of
  refusals is kept — see ADR-0016 for the reasoning.

  **Search side.** The matcher no longer asks "is this the same entity"; the **category narrows**
  and the **contract decides**. A contract is what a thing does with the project's own words
  removed — canonical operations, routes and files, all against `__ENTITY__`
  (`library/identity.py`). An entry may cover more than a package needs, never less, and the files
  must be exactly the file plan. Because the entity is taken out of it, a project that says
  "reservations" matches what a project that said "bookings" contributed, and neither ever shared a
  word. Layer C and the assembler both read the **store** rather than the seed directory, so what
  the library learns is what the next build can use.

  **Contribute side** (`library/contribute.py`): skip what carries an entry id (it came from the
  library — without this the library contributes its own entries back to itself forever) → require
  every build gate → generalize → re-verify → gate → dedup on the contract → take an id from the
  store. Ids are `category.seqno.version` and the **store assigns the seqno under a lock**, so two
  builds contributing to `booking` at once get 2 and 3. Categories are canonical with a proposal
  path (`library/categories.py`), so `login`, `signin` and `user_account` all land in `auth`
  instead of starting three spellings of one thing; an unrecognised area is *proposed*, unconfirmed
  and matched against by nothing, until a person confirms it.

  **Quality is the build's own gates**, not a fresh opinion. "Better" — the only thing that lets a
  candidate replace an entry projects already assemble — is Pareto on evidence that was actually
  counted: no worse on anything, better on something. Lighthouse and accessibility are not measured
  in the build yet (B048), so `Quality.scores_measured` records which evidence an entry carries and
  the gate reads the right one rather than inventing a number. A build never replaces a seed.

  **A model is used for generalization only**, and not trusted there either: the entity
  substitution runs deterministically first, and a reply that drops a `data-scio-id`, returns a
  different set of files or cannot be parsed is discarded in favour of the deterministic result.
  Nothing is added without being **re-verified**: the entry is adapted to a sample entity it has
  never seen (`widget`) and checked for empty files, surviving placeholders, instrumentation and
  the validation agents. Contributed entries are **provisional** and reviewable
  (`GET /library/entries`, approve/reject, propose/confirm a category), stored in Postgres in the
  engine's own `library_*` tables — Prisma keeps owning the product's schema. Without
  `SCIO_CATALOG_DB` the engine still matches and assembles from the seeds and reports
  `persistent: false` rather than pretending.

  engine 555 tests (+36), ruff clean; api and app untouched and green. The delivered app is
  unchanged: contributing happens after the build and swallows its own failures, and a Level 2
  preview contributes nothing at all.

  **Run against the local stack, which found five things no test did.** (1) The engine could not
  connect: it is handed the api's `DATABASE_URL`, and psycopg rejects Prisma's `?schema=public`.
  (2) The obvious fix encoded the space in `-c search_path=…` as `+`, and Postgres reported an
  unrecognised parameter called `+search_path`. (3) Eight concurrent contributions were handed
  `booking.1.1` four times and three of them were silently overwritten — reading the high-water
  mark and inserting afterwards is two transactions, so id assignment and insertion now happen
  under one lock. (4) The `library` event was a plain dict and the SSE writer only handled models,
  which surfaced a *successful* build to the user as a failed one. (5) Layer C matched against the
  seed directory and then the assembler did too, so the library could learn and never use what it
  learned. All five are fixed, and (1)–(3) are locked down by tests that skip loudly without a
  database.

  **The acceptance story, run for real** (`scripts/dev-up.sh`, no keys): a booking app assembled
  `feature-booking` from the seeds and contributed nothing (the assembled package was skipped as
  "already the library's"); a workout app had no match, so it generated, and contributed
  `auth.1.1` and `workout.1.1` — provisional, in Postgres, with `workout` recorded as a proposed
  category; a second workout app **discarded** both as "not worse"; and a third **assembled both
  from what the first build taught**, with no model call for either.

- 2026-08-19 — B066: **correct a misfiled spec field without redoing the wizard.** The wizard
  sometimes files an answer under the wrong slot — "guests and staff" lands in *what it manages*
  instead of *who it's for*. The review screen showed that faithfully and offered no way out except
  starting over, which nobody does: they approve a spec they can see is wrong, and every layer below
  builds the wrong thing correctly. Every field on the review screen is now editable
  (`apps/app/src/pages/SpecPage.tsx`), with the right control for the shape — a list is typed as a
  list and split client-side, and the sensitivity field gets its three parts instead of a JSON blob
  nobody can be expected to type. **"Belongs under" is the fix for the actual defect**: choosing a
  different field sets the answer there and empties the wrong one in ONE request, so the spec is
  never briefly holding the same answer under two headings.

  Three properties make a correction worth trusting, and each is a rule rather than a hope:

  **A correction is authoritative.** It is recorded as `stated` with `provenance:
  ["corrected-on-review"]` — deliberately not a message id, so a model can never forge it — and
  `intake/extraction.apply_extraction` now refuses to overwrite a field carrying that mark, saying
  so in the extraction report. Without this the very next wizard turn re-extracts the same old
  conversation, re-files the same misfiling, and the correction evaporates silently. Verified live:
  after correcting *who it's for* to "guests, staff", telling the wizard *"just guests, nobody else"*
  left the correction standing.

  **A correction is re-validated, not just stored** (`intake/correction.py`, `POST /intake/correct`,
  `POST /projects/:id/draft-spec/field`). It goes back through Layer A's own gate and trigger logic,
  so a correction that OPENS work says which: one role corrected to two triggers `role_permissions`,
  and sensitive data triggers `compliance`. The review screen shows exactly that — *"Correcting Who
  it's for opened this"* — and asks for it **inline**, which is the whole point: no wizard restart
  for one extra sentence. Re-detection runs too, so a correction can settle the contradiction it
  caused. The response is a whole turn rather than a diff, because the narrative, the assumptions
  and the cost estimate are all derived from the spec, and a screen showing prose about a spec that
  no longer exists is the quiet wrongness this screen exists to prevent.

  **The gate is held where it is enforceable.** The review screen disables approve while anything is
  open, and `spec.service.approve` now asks the engine's gate and refuses (409, naming what is
  missing) rather than freezing a contract Layer B would reject minutes later in the build view. An
  unreachable engine is *not* a refusal — we cannot prove a spec unbuildable during an outage, so
  approve behaves as it always did. Relatedly, a 4xx from the engine is no longer reported as
  "the engine is not reachable": `EngineRefusedError` passes the engine's own message through as a
  400, so typing a list into a sentence field says *"'purpose' needs a sentence"* instead of
  announcing an outage that is not happening.

  engine 519 tests (+18), api 83 (+9), app 70 (+12), typecheck and ruff clean.

  **Clicked through in a browser against the local stack** (`scripts/dev-up.sh`, dev auth, local
  Postgres, no keys): review screen with 13 correctable rows → corrected *who it's for* to "guests,
  staff" → *"That change needs a bit more"* with `role_permissions` asked inline (and no "belongs
  under" on it, because it IS the field being asked) → approve disabled throughout → moved *what it
  manages* into *what users can do*, the source row disappearing → answered the remaining
  conditionals inline → the panel cleared, the estimate came back (6 parts) and approve enabled →
  approved, landing on *"How involved do you want to be?"*. The frozen `spec_version` carries the
  corrected values and their `corrected-on-review` provenance. The only console failures were
  Google Fonts, which the sandbox blocks and always has.

- 2026-08-19 — B068: **gate 2b — the design window: the half a person touches.** Gate 2a built the
  backend and nothing could reach it; `/design` was a placeholder and approving a spec went straight
  to a build. Now approving asks **one question** — *just build it* or *shape the design first* —
  and Level 2 is a real screen (`apps/app/src/pages/{InvolvePage,DesignPage}.tsx`,
  `src/lib/bridge.ts`). The preview is built streamed (same per-part progress a build shows) and
  embedded; a **Use / Mark** toggle arms the in-preview bridge, and while armed the app's own
  behaviour is suppressed so marking a Submit button does not submit and navigate away from the
  thing being marked. **The pending list IS the change set**: each marking becomes a line with an
  editable note and a remove, and *Generate again* sends all of them plus the free prompt as ONE
  change — a change is usually several small things noticed together, and making people submit them
  one at a time is what makes a design tool feel expensive. Afterwards the panel shows the isolation
  proof in the engine's own numbers ("changed components/booking-form.tsx, 3 other files untouched")
  and names every marking the engine skipped, keeping it in the list so it can be reworded rather
  than lost. The parent half of the bridge is origin-pinned both ways, never posts to `"*"`, and
  **returns data rather than rendering it** — React escapes by construction, which is the fix for
  the spike's `innerHTML` lesson.

  Two calls were open going in, and both were settled for usability without giving up the wedge:

  **Conflicts are answered here, not back in the wizard.** Sending someone to the wizard to say
  "actually anyone should see the menu" is bad product. So a conflict renders inline with two
  answers: *Keep it as-is*, which drops that one marking, and *Change the plan*, which is a real
  amendment (`POST /projects/:id/spec/amend`, frozen as a new `spec_version`). The two kinds are
  deliberately different acts: a `non_goal` amendment **removes the non-goal** from the spec, while
  `auth`/`access` ask a **second time**, name the protection by the sentence the question quoted,
  and record an **allowance** rather than rewriting the security posture. The architecture still
  says the data is sensitive; the record says what the user permitted anyway, and the engine's
  `detect_conflicts` skips only the exact `spec_says` that was allowed — an allowance is never a
  switch that turns the questions off. Known cost, stated in the code and in the UI: an allowance
  lets code and posture drift, and a deeper change belongs in the wizard.

  **Versions really restore.** A list you cannot return to is decoration. An applied change is now a
  **commit** (`design/change.commit_change`, manifest in the same commit), the design version stores
  its sha, and *Return to this version* runs `git read-tree -u --reset` and commits the result **on
  top of HEAD** — forward, not backward, so changing your mind twice still works. A restore is a
  write, so it goes through the same guardrail as everything else: the manifest is rebuilt from the
  restored source and the instrumentation re-verified, and a tree that no longer verifies is undone
  and refused with the reason rather than served (a preview whose ids do not match its manifest is
  one where marking lands in the wrong package — B039). A version that was never committed says so
  instead of offering a button that cannot work.

  Recorded as ADR-0015 (answering a design conflict). api 74 tests (+7), app 58 (+20), engine 501
  (+12), typecheck and ruff clean.

  **Clicked through in a browser against the local stack** (`scripts/dev-up.sh`, dev auth, local
  Postgres, no keys): new project → wizard → approve → *"How involved do you want to be?"* → shape
  the design first → preview built and embedded → **the bridge said hello** → marked two elements →
  wrote a note on each → added a prompt → Generate again → *"changed app/layout.tsx, app/page.tsx,
  components/site-header.tsx, lib/supabase.ts (16 other files untouched)"*, the list cleared, the
  preview reloaded and **marking still worked afterwards** → *"make the bookings public"* → the
  question, with nothing built → *Change the plan* → the second confirmation naming the protection
  → *Yes, allow it* → the allowance frozen on spec version 2 (`allowances` + an `amendments` record
  with the note and the timestamp; the spec's own content untouched) and the change applied → four
  design versions each with their own commit → *Return to this version* → v4 "returned to version 1",
  with v2 and v3 still in the list and still returnable → *Build it* → the build view.

  Two things it could not settle honestly, both recorded rather than papered over: the `non_goal`
  conflict could not be raised through the browser because the stand-in wizard filed "no payments
  for now" under `sign_in` rather than `non_goals` (B065/B066's known problem — the conflict
  detector was right to see no contradiction), so the `access` conflict carried that path instead;
  and **"Build it" recreates the workspace**, which throws away the design history the versions
  panel points at (B070).

  **Four things only running it could have found**, all fixed here:

  1. **The free path could not do a design change at all.** Without keys the relay returns a digest,
     so `/design/change` died with "No FILE blocks in the reply" — the stand-in builder covered the
     build and nothing covered this. It now answers a directed change by returning the same files
     with one comment at the top naming what was asked, which exercises the whole round trip
     (isolation, instrumentation, commit, version) while leaving every `data-scio-id` where it was,
     and says in the file itself that no model wrote it.
  2. **The "preview never said hello" warning cried wolf.** Its countdown started when the page
     rendered, but a dev preview compiles on first request and can take half a minute — so the
     warning appeared on a preview that was merely still starting. It now starts at the iframe's
     `load`.
  3. **A preview that had stopped left a dead iframe with no way out.** It happens for real — a
     delivery build recreates the workspace and takes the preview with it — and the window's answer
     was an "Internal Server Error" frame and nothing else. The warning now carries a **Build the
     preview again** button, exercised live: dead preview → rebuilt → bridge said hello → marking
     worked.
  4. **`tests/test_preview_bridge_live.py` leaked its Next servers.** `npx next dev` forks `next`,
     which forks `next-server`; terminating the process we started left **two next-servers holding
     12 GB** after a full engine run, and the next thing to want memory — a browser — simply could
     not start. Each server now gets its own process group, and the group is killed. Exactly the
     lesson `scripts/dev-down.sh` already carries, in the one place that had not learned it.
- 2026-08-12 — B067: **gate 2a — the design window's backend: preview builds carry the marking
  bridge, and a batch of markings changes only what it touches.** Level 2 is "show me before you
  build it", and this is the half that has no UI. **The preview is a different build**: pass
  `shell_origin` and the app carries the bridge the spike proved (`builder/preview_bridge.py`);
  leave it out and it does not. The injection is a webpack entry declared in the app's own
  next.config.js behind `SCIO_PREVIEW_MODE` — the same shape the verification data layer already
  uses — so **the generated code is untouched**, which matters because the manifest maps ids to
  source lines, isolation compares file hashes, and directed regeneration rewrites whole packages;
  editing `layout.tsx` to add a preview feature would disturb all three. Verified against a real
  Next server, both ways: the bridge is in exactly one bundle with the flag and in **zero** bundles
  without it, while `data-scio-id` is still there. **`POST /design/change` applies a BATCH**
  (`design/`): each marking resolved strictly and individually — one unaddressable marking is named
  and skipped, the rest still apply, because failing a batch whole teaches people to mark one thing
  at a time — then grouped by package, then one relay per affected package, then the core's
  `directed_regenerate` per package, unchanged. A package whose regeneration loses a `data-scio-id`
  is rolled back and reported; a model that edits a file its package does not own is refused; every
  other package is byte-identical, and the count is what the window shows. **A marking that argues
  with the approved spec is a question, not a build**: deterministic detection against the
  architecture's non-goals, its auth mode and its sensitivity posture, matched on the project's own
  canonical vocabulary (so "reservations" in a non-goal catches "booking" in a note). Nothing is
  built and nothing is spent — the user decides. api: `POST /projects/:id/design/preview` (streamed,
  like a build), `GET /projects/:id/design`, `POST /projects/:id/design/change`, all
  workspace-scoped, and **every applied change is a design version** carrying the workspace, the
  preview URL and the manifest markings resolve against. One design decision the tests forced:
  generating a preview with no `APP_ORIGIN` configured now **refuses**, because the alternative is a
  design window embedding an app that cannot report a single click with nothing anywhere saying why.
  489 engine tests (+26), api 67 (+14), app 38, typecheck clean.
- 2026-08-12 — **Spike (spikes/design-marking): the in-iframe marking bridge works end to end —
  gate 2's riskiest mechanic is de-risked.** Verdict: build the design window on a bridge, and keep
  the split it enforces. The parent genuinely cannot read into the preview (`SecurityError`, checked
  in the browser rather than assumed) because the preview is always on its own origin — so a
  preview-mode script inside it captures clicks on `[data-scio-id]`, draws the marker itself, and
  postMessages the element's identity out, origin-pinned in both directions. The whole chain ran on
  the booking blueprint: mark → resolve to `pkg_feature_booking` @ `components/booking-form.tsx:70`
  → mock directed change → reload → "Book a table" became "Reserve our table" with 2 files changed,
  **7 byte-identical** and `layout.tsx` untouched. Click to resolved marking: **150 ms**. **The
  bridge is absent from the delivered app** (flag off → no script, every id still present) —
  checked, not asserted. The finding that shapes gate 2: **the preview reports, the parent decides.**
  The bridge sends the clicked node *and* the nearest instrumented ancestor and never substitutes
  one for the other; `core/resolver` refuses on an uninstrumented element by name, which is what
  keeps B039's "a marked button rewrites the app shell" bug dead on the far side of a security
  boundary. Also learned: click coordinates do not survive the crossing (different viewport, an
  unreadable scroll offset), so the marker must be drawn inside the preview and never painted
  from the parent; and everything the preview sends is untrusted second-origin input — a refusal message containing
  `<div>` was interpolated into the shell's innerHTML and became one. 8 browser-free tests cover the
  payload seam; `run_spike.py` runs the whole thing.
- 2026-08-12 — B064: **the product can be run and clicked through locally — and doing it for the
  first time found four real bugs** (`scripts/dev-up.sh`, `docs/RUNBOOK-LOCAL.md`). One command
  brings up engine + api + app + a real PostgreSQL 16 **process** (no Docker; pgvector is the one
  package that must be installed, and the script says so by name rather than letting migration 0001
  fail on its second line). Auth is swappable on both sides now, not just the backend: `SCIO_DEV_AUTH`
  binds a `DevIdentityVerifier` behind ADR-0008's existing interface, `VITE_DEV_AUTH` swaps Clerk's
  provider/gate/sign-in/badge for local equivalents (`app/src/lib/auth.tsx`), and the bearer token
  *is* the identity — so a different email is a different workspace, and tenant scoping can be
  exercised by hand. Production is untouched: Clerk unless the flag is set, and `SCIO_DEV_AUTH` with
  `NODE_ENV=production` is refused at boot rather than honoured.
  **The click-through is the point, and it worked**: new project → wizard (12 answers, one
  contradiction caught and settled) → review (the whole in prose, the spec field by field, the
  assumptions, and the estimate — `~$2.48–$5.94 · ~21–51 min · 7 parts · 1 reused`) → build (7/7
  parts, streamed) → reveal, with the built app running in the iframe. **Four bugs no test could
  have caught**, because tests call the api in-process and render components without StrictMode:
  (1) **no CORS** — the api had never been called from a browser, so nothing loaded at all;
  (2) **the wizard looped forever without keys** — `FakeProvider` returns a digest, extraction
  cannot parse a digest, nothing was ever recorded, and gate 1 could never close, so the free path
  could not reach a build. Fixed with `StandInIntakeProvider`, which files each answer under the
  question that was asked — one field per turn, every value the person's own words with real
  provenance, never invented; (3) **a contradiction could never be resolved** — the question
  described the clash without naming which answer to revise, so the reply landed nowhere and the
  gate stayed shut; it now restates the field's own question; (4) **StrictMode killed every build** —
  the page's cleanup aborted the SSE stream, the double-mount guard stopped it restarting, and the
  AbortError was displayed as "Can't reach the Scio API" on a healthy backend, which also
  contradicted the screen's own promise that you can leave and the build keeps running.
  Two smaller ones fixed on the way: the api's GET `/intake` returned a hard-coded empty gate, so a
  reload showed "0 of 6" however far along you were and the review screen could never show the whole
  or the estimate (it now recomputes the gate — deterministic and free — and fetches the
  confirmation once buildable); and `dev-down` missed `nest start`'s child process and the engine's
  leaked `next dev` sandboxes, which is how a "restarted" service went on serving old code.
  463 engine tests (+1), api 53 (+6), app 38, typecheck clean.
- 2026-08-12 — B060b: **"it works, and it is private" is now a criterion a build passes or fails**
  (`core/interaction.py`, `core/interaction_runner.py`, `layerc/scripts.py`). B060 is complete.
  The vision loop could see that a page rendered; it could not see that pressing the button did
  anything, so Layer C had to mark "works end to end and persists" and "a guest cannot read another
  guest's booking" unobservable (B054) and nobody checked the two things the user actually cares
  about. **Both now gate the build.** A criterion can carry a short declarative script — `fill` /
  `click` / `reload` / `assert_present` / `assert_absent` / `assert_row` / `as_user` — driven by
  Playwright against the app running with data (B060a), targeting `data-scio-id`. The `reload` is a
  real navigation, which is the whole point: it separates "React still has it in state" from "it was
  saved". **The scripts are derived deterministically** from the architecture graph: a create
  operation's inputs become the fields to fill, its screens become the routes to visit, its entity
  becomes the table to look in; an owner column plus an identity becomes the two-user isolation
  script, in which each user must see their OWN row as well as not the other's — "nobody sees
  anything" is a broken list, not privacy. No model is asked to invent a step. **The channel is
  first-class evidence**: a fifth gate alongside instrumentation, validation and console; failures
  feed the capped repair loop with one actionable line ("could not expect Ada present — 'Ada' was
  not on the page"); a package that fails it never pays for a critique. **It refuses to bluff**:
  where no script can be derived honestly — an operation with no screen, an app with no identity to
  isolate by — the criterion stays exactly what B054 made it, and a preview that cannot drive
  (no browser, no data layer) reports "nobody drove it" rather than passing. Markers are unique per
  attempt, so a repair cannot pass on the row the previous attempt left behind. **Proven live**,
  against a real browser and a real PostgreSQL: a correct booking feature passes persistence (row in
  the database) and isolation (each guest sees only their own); the same app with a silently failing
  insert fails persistence; the same schema with `using (true)` instead of `using (owner_id =
  auth.uid())` — RLS on, a policy present, a code review passed — fails isolation. Two defects fixed
  on the way: the acting user was a module-level `let`, which Next's split bundling would have left
  the API route setting and the pages never reading (now on `globalThis`, like the pglite instance),
  and the verification endpoint's logic was trapped inside a Next route where nothing could test it
  (now `verify.ts`, with the route a four-line wrapper). The endpoint also resolves entity → relation
  (`booking` → `bookings`) and errors by name rather than answering zero, because a count of zero
  reads as "it was not saved". 462 engine tests green (+37), api 47, app 38, typecheck clean.
- 2026-08-12 — B060a: **the verification data layer — generated apps now run WITH data**
  (`library/verification/`). Built on the spike's approach A. A build in verification mode runs
  against a real in-process PostgreSQL (pglite), so "the booking actually saves" and "a guest
  cannot read another guest's booking" stop being criteria Layer C has to scope out as
  unobservable (B054) and become things a build can check. **What ships is unchanged**: the app's
  own `lib/supabase.ts` still imports real `@supabase/supabase-js` and is never rewritten — a
  second client is written into a gitignored `.scio/verification/` and swapped in by next.config.js
  *only* when `SCIO_VERIFY_DATA=1`; pglite is a devDependency so it cannot ship. **RLS is really
  enforced**: every app query runs inside a transaction as the non-superuser `authenticated`/`anon`
  role with the JWT claim GUCs set, exactly as PostgREST does, plus an `auth.uid()/role()/email()`
  shim so generated Supabase-idiom policies resolve. Both roles get full table grants on purpose —
  the POLICY decides, not the grant, which is how Supabase itself is set up. **Lifecycle is owned**:
  one fresh database per build, the app's own migrations applied verbatim, and the ~40 MB discarded
  when the build ends. **Proven live**: the assembled booking blueprint, driven through its real
  form in a browser, inserted a booking that was still there after a reload — `persisted: true` —
  then the dev server stopped and the database was freed. Three real defects found on the way and
  fixed: the sandbox never considered an app "ready" if its root route 404s (`HTTPError` subclasses
  `URLError`, so a serving app waited out the full 180s timeout); Next bundles server components
  and server actions separately, so a module-level singleton gave each its own pglite on one
  directory (now keyed on `globalThis` — one process, one database); and a `resolve.alias` is
  silently beaten by Next's tsconfig-paths resolver, so the swap uses
  `NormalModuleReplacementPlugin`. 425 engine tests green (+20).
- 2026-08-12 — **Spike (spikes/local-data): a generated app CAN persist data in this sandbox, with
  no Docker.** Verdict: yes, via approach A — `@electric-sql/pglite` (PostgreSQL 18.3 as in-process
  WASM) behind a swapped `lib/supabase.ts` that answers with supabase-js's `{data, error}` shape.
  The fixture is the booking blueprint's real code, emitted by the engine's own adapter; nothing was
  seeded and nothing in the app was changed. Playwright filled the real form, submitted it through
  the app's own server action, and the booking was still there after a page reload **and after a
  full process restart** — verified in the UI and by reading the database directly. The fidelity
  gaps are written down honestly: RLS is bypassed by default (pglite connects as superuser) but **is
  enforceable** by doing what PostgREST does — `begin; set local role authenticated; set local
  request.jwt.claim.sub = …` — measured working, which would turn "a guest cannot read another
  guest's booking" from an unobservable criterion into a testable one; there is no GoTrue/`auth`
  schema, so `auth.uid()` policies need a small shim; the client shim covers only the calls the
  blueprint makes (PostgREST-the-binary is the escape hatch); and pglite is single-writer, so
  verification must own the database lifecycle — a lesson learned the hard way when clearing the
  data directory under a running server left it serving stale rows while new writes vanished.
  Recommendation for B060 in `spikes/local-data/FINDINGS.md`. Fixture only, not wired into apps/.
- 2026-08-12 — B046: **a deterministic cost + time estimate at the spec gate** (`engine/estimate.py`).
  Pricing a build never calls a model — a spec is priced every time someone finishes the wizard, and
  most specs are priced far more often than they are built, so an LLM price tag would eat the margin
  on projects that never build. The estimator reads the plan's assemble-vs-generate decision, the
  chosen model's price from matrix.yaml, and the pass-count from the run profile: an **assembled part
  is priced at zero**, a generated one at a documented token heuristic keyed on package kind plus its
  architecture slice (operations, screens, tables). **The heuristic is calibrated against the real
  runs and lives in one commented place** — the observed per-package costs are tabled in the module,
  and a test asserts the range still contains the $1.42 the third real run actually cost, so drifting
  away from the one real invoice we have fails the suite. Output is always a **range**, never a
  false-exact figure (low = everything passes first time, high = about half the packages need a
  repair round), plus the **composition** — "5 parts · 1 reused · 4 built" — which is where the
  library's saving becomes visible to the person deciding whether to press build. Exposed as POST
  /estimate and on the /plan response; the api passes it to the review screen and **degrades to the
  part count** when the engine could not price the plan. The app's "rough parts" placeholder is
  replaced by the real range, the composition, and the explicit framing: "For the base build. Every
  change you make afterwards adds — and you only pay once you approve." **Measured**: the booking
  spec with the blueprint reused estimates $0.43–$1.04 on Sonnet at two passes, against the $1.42
  that same plan cost fully generated. 405 engine + 47 api + 38 app tests green.
- 2026-08-12 — B045: **the component library, first slice — match → fetch → adapt → assemble**
  (docs/LIBRARY.md, ADR-0014). Between Layer B and Layer C the engine now asks the catalog whether
  it already knows how to build each package; a match is *assembled* (no relay call at all), and
  anything else generates exactly as before. **A catalog entry is a contract with files attached**
  (`library/entry.py`): what it provides in canonical vocabulary, the exact files it writes, its
  token bindings, its `data-scio-id`s, and quality metadata — an entry that is not tested AND
  security-reviewed is never offered. Entries are written against an `__ENTITY__` placeholder, so
  adapting to a project is a deterministic substitution rather than a model call. **Seeded**: three
  UI entries (button, field, empty state) and one full booking blueprint that carries its own
  correct imports — including `app/actions/` and `lib/validation/` per the file-plan rule — and an
  id on every element. **The matcher is strict** (`library/matcher.py`): vetted entry, same
  canonical entity, every owned operation covered, and files exactly equal to the package's file
  plan; the relay is asked only to break a genuine tie between two entries that pass all four, and
  a tie it cannot break generates rather than guesses. **Assembly is verified like generation**
  (`library/assembler.py`): the instrumentation verifier and the app-wide manifest still run, and
  `data-scio-package` is stamped by the builder because that is per-project; only the relay and the
  repair loop are skipped. Layer C marks every package assemble-vs-generate and reports "1 of 5
  parts from the library". **The contribute-back gate is built and tested** (`library/gate.py`) —
  it rejects untested, unreviewed, low-scoring, ungeneralized or leaky candidates (a customer's
  name, a URL, a key); the contribution itself is deliberately stubbed, because a catalog that
  fills up automatically fills up with things nobody chose. **Proven live**: a booking spec built
  5 of 5 packages with the blueprint assembled and *no model asked anything about it*, then served
  `/booking` and `/booking/new` at HTTP 200 with the full instrumentation intact. Also fixed while
  there: a circular import between `builder` and `library` that only passed by import-order luck,
  and `zod` added to the locked stack — the second real run's generated `lib/auth.ts` imported it
  while it was not installed, which stayed invisible only because no rendered route imported that
  module. 382 engine tests green (+39), ruff clean, all three TS workspaces typecheck.
- 2026-08-12 — B059: **hardened what the SECOND real run surfaced**. That run went 4 of 5 parts
  working (from 0 of 5), with nothing blocked and nothing failed; two things it exposed are now
  fixed. (1) **The file plan was narrower than the stack's idiom.** The booking feature imported
  `@/app/actions/booking` and `@/lib/validation/booking` — a server action for the form that
  mutates data, and the validation schema its own "inputs are validated server-side" criterion
  demands. Neither had a legal path, so the model invented both, the import boundary caught them
  (correctly) and the app broke on dangling modules. `app/actions/<entity>.ts` and
  `lib/validation/<entity>.ts` are now part of a feature package, and the rule is written down in
  file_plan.py: every file the contract's own criteria imply gets a home here, or the model will
  invent one. (2) **A third-party host's failure is no longer the app's failure.** The design
  tokens package burned a whole repair round because the sandbox blocks fonts.googleapis.com and
  `ERR_CONNECTION_RESET` was classified as "an error from the app's own code". The console
  classifier now has a `third_party` origin, decided by host rather than by a list of URLs — it
  never fails a build and still shows up in `suppressed`, so the filter stays auditable.
  **Verified against the real run's own output**: both invented imports are now in bounds (0
  findings), and the real console error classifies as `third_party`. 343 engine tests green (+7).
- 2026-08-12 — B054: **hardened what the first real run surfaced** — three defects a real model
  exposed that every existing test had passed. (1) **"Done when" is now a contract, not a wish
  list** (`layerc/criteria.py`): a criterion declares which planned files would produce it and
  which channel can observe it (`render` → the critique, `validation` → a deterministic agent,
  `unsupported` → recorded and judged by nobody). Only observable criteria reach the critique, so
  the real run's three "no evidence was provided" failures cannot recur; `validate_plan` now
  catches a criterion no file in the package's plan would produce **before** generation (an error)
  and warns about one nothing can observe (never a failure). pkg_foundation's "done when" is now
  the shell and its routes — not a test runner and security headers it neither owns nor could
  show — and its *goal* stopped promising them too. What nobody verified still travels to the
  reveal as a "Not verified:" remainder, so "works" never quietly means "unchecked". (2) **An
  import-boundary guardrail** (`validation.py`): imports are resolved deterministically and
  anything outside the package's own files plus its declared dependencies is a build failure fed
  back as a fix — the real run wrote `@/lib/env` and `@/types/supabase`, files no package
  produces, and every other gate passed it because no rendered route imported them. The contract
  prompt now states the boundary explicitly as well. (3) **`data-scio-package` is stamped, not
  requested** (`core/stamping.py`): the builder knows which package it is generating, so it writes
  the tag itself; the model supplies only the id. The verifier now requires BOTH attributes on the
  same element and fails a build that has an id without a package — previously the manifest
  inherited the nearest tag above, which is the silent wrong answer the spike warned about.
  **Verified against the real run's own output**: the guardrail catches both invented imports, and
  stamping fills all three untagged `<li>` elements. 336 engine tests green (25 new), ruff clean,
  all three TS workspaces typecheck.
- 2026-08-12 — Build-vs-adopt analysis added to docs/STRATEGY.md (section G): adopt prompt caching
  (cache the static package-prompt prefix; ~90% off reads) and the Batch API (50% off, stacks) for
  cost; evaluate the Advisor tool (vs our multi-pass) and the memory tool/stores; keep our own
  orchestration + instrumented sandbox + marking->code and the library + fleet learning. Grounded in
  Anthropic's API docs.
- 2026-08-12 — B053: **prepared for the first REAL run against Claude** (the run itself is the
  operator's — their key, their environment). Four things. (1) **Real model ids**: matrix.yaml now
  carries `claude-fable-5`, `claude-opus-5`, `claude-opus-4-8`, `claude-sonnet-5`, `claude-haiku-4-5`
  with output-token prices, and a note telling the operator to confirm ids + pricing in the Anthropic
  console before spending — ids are complete as written, never suffixed with a date (the old
  `claude-haiku-4-5-20251001` was not a valid id). (2) **The "1 + Claude" run profile**
  (`execution/profile.py`): `SCIO_ONLY_PROVIDER` / `SCIO_MODEL` / `SCIO_MODEL_PASSES` narrow the whole
  engine to one vendor and one model without editing YAML, and **setting 1 runs that model twice —
  generate, then self-review** (STRATEGY §E), with tests proving the doubling, proving the second pass
  really receives the first, and proving a caller that asks the relay for one pass still gets one.
  `/health` now reports what would actually happen (`providers`, `profile`, `builder`), so a key that
  never reached the process is caught before a build, and the build view shows the models it ran.
  (3) **The sandbox runs REAL generated code** — the B052 gap. A workspace is now *generated*, not
  borrowed: package.json for the locked stack (Next.js + TypeScript + Tailwind + Supabase, ADR-0011,
  pinned) plus tsconfig/next.config/postcss/Tailwind config, then `npm install` as an **explicit
  blocking step before anything serves** — which is the answer to "the sandbox won't install
  dependencies during startup" (a dev server that installs on first boot dies mid-startup). Installs
  go to a cache keyed by the dependency set and are symlinked in, so the first build pays ~35s and
  every later one pays a symlink; a prepared `SCIO_SCAFFOLD_DIR` or the repo's spike app still works
  offline. **Verified live here**: the full path built a real Next.js app into an npm-installed
  workspace — 5 parts, all 4/4 checks, dev server serving `/booking` with the instrumentation intact
  and Tailwind compiled (11KB of CSS, preflight present). Also raised codegen's output budget to
  16,000 tokens (a package is several complete files; the 4,096 default cut the third one in half)
  and made a truncated reply a named, retried failure instead of "no usable files" — half a component
  never reaches disk. (4) **docs/RUNBOOK-FIRST-RUN.md**: the operator's exact steps (Postgres +
  migrations, Clerk, `ANTHROPIC_API_KEY`, the 1+Claude env, the three services, wizard -> review ->
  build -> reveal), what to watch for (real code is not stand-in code; the instrumentation contract
  meets a real model for the first time; how to verify the install without spending anything; every
  build leaves a dev server running — with the cleanup), the cost shape, and a symptom table. The
  fake stand-in remains the default whenever no key is set, and `SCIO_FAKE_PROVIDERS=1` still forces
  it — that is how CI runs. 310 engine + 46 api + 35 app tests green, ruff and all three builds clean.
- 2026-08-12 — B052: **the build + reveal wired end to end — the whole path now runs**. Input ->
  understanding -> plan -> built, assembled, running app -> reveal, across app <-> api <-> engine,
  fake-driven. Engine: POST /build streams the whole pipeline (Layer B -> Layer C -> B041b's
  orchestrated package build into ONE running app), emitting `started` (the real schedule + the
  whole), `progress`/`package` per part, then `finished` (running URL, git_sha, honest aggregate);
  a workspace is scaffolded from a prepared app (SCIO_SCAFFOLD_DIR / SCIO_WORKSPACE_ROOT) because
  the sandbox refuses to install dependencies during startup, and the preview is left running so
  the reveal can embed it. Without keys the code comes from a new **stand-in builder** — it reads
  the contract it is given and writes instrumented placeholder files, so the pipeline is testable
  without keys; it is labelled as such everywhere, including on the reveal, because the pipeline is
  real and the code inside is not. API: POST /projects/:id/build relays the stream to the browser
  as SSE and persists a build_version (+ git_sha + the whole honest status, not just the good news)
  with the preview URL, moving the project building -> ready/error; GET .../build/latest reads it
  back so the reveal survives a reload. App: a real build view (the schedule drawn from the plan,
  parts ticked off as they actually finish, "you can leave — we'll notify you", no fake progress
  bar) and a real reveal (the running app embedded, "what you built" from the approved whole, and a
  trust receipt where what needs a look and what was never built are as visible as what works).
  Level 1: approving the spec goes straight to the build. 283 engine + 46 api + 35 app tests green,
  all three build. **Verified live**: an approved booking spec ran the whole path through the engine
  — 5 parts in dependency order, all 4/4 checks, assembled into one Next.js app at a live URL,
  committed as version 1, and `/booking` renders the operations Layer B derived from the spec.
  Also fixed: the root .gitignore's bare `build/` had been silently excluding
  apps/api/src/modules/build from git since phase 3.2.
- 2026-08-12 — B051: **gate 1 wired end to end** — the UI now runs the real engine. app <-> api <->
  engine: a turn in the wizard hits POST /projects/:id/intake/message, which loads the project's
  conversation, appends what was said, calls the engine's /intake/step, persists the messages and the
  updated spec, and answers with the next question. New in the api: an EngineClient (ENGINE_URL) that
  separates failures by consequence — the turn itself throws (503, "the engine is not reachable")
  while the review screen's decorations degrade to null so the user still sees their spec; a
  workspace-scoped intake module; and a real spec freeze (POST /projects/:id/spec/approve) writing a
  spec_version with the assumptions read off the spec's own metadata, marking it current and setting
  the project to the new `spec_locked` status. New in the app: the real wizard (conversation + a live
  wholeness panel that tags every assumed and inferred field, honest 'n of 6 core answers' progress,
  contradictions surfaced as "needs your call") and the real review screen (the whole above the
  field-by-field spec, the assumptions listed, a part count explicitly marked rough — not a price —
  and the three exits: adjust, not now, freeze). Schema: `project.draft_spec` for the working spec
  (a spec_version is a contract and is never rewritten in place) + `spec_locked`, migration 0002
  generated. 273 engine + 35 api + 21 app tests green, all three build. Two real bugs were caught by
  checking the contract against the *running* engine rather than the mocks: Layer B's `whole` is an
  object, not a string (the review screen would have silently always fallen back), and on the fake
  provider the whole was a hash digest — the engine now uses its deterministic grounded narrative
  whenever no real model is available, because a digest must never be the thing a user approves.
- 2026-08-12 — B050 / 4.3: the intake agent — extraction + next-question (apps/engine/intake).
  **Gate 1's brain is now complete**: a conversation goes in, a typed AppSpec with provenance
  comes back, and the wizard asks the one thing still missing. The split is deliberate — WHICH
  field to ask is decided by Layer A's gate (deterministic, free, unarguable), only the WORDING
  goes to the relay. Extraction is grounded by rules the prompt cannot bend: a value claimed as
  "stated" must cite a real user message or it is dropped (an empty slot becomes a question; an
  invented one becomes the wrong app), an inference is recorded as `derived`, never at high
  confidence, and never over something the user actually said — while a later stated answer does
  correct an earlier one. Values outside the schema are dropped, placeholders ("unknown", "n/a")
  count as no answer, the defaulted-and-flagged fields keep their "assumed" tag, and list answers
  merge through Layer B's canonical vocabulary so "reservations" is recognised as the "bookings"
  already recorded — keeping the user's own wording, because Layer A records what was said and
  Layer B decides naming. Every question carries an example structurally ({question, example}),
  falling back to INTAKE-SCHEMA.md's own wording when the model's reply is unusable. Contradictions
  ("no sign-in" + several roles; "not sensitive" + payment data; a non-goal the app also needs) are
  detected by rule and **asked about, never resolved** — the gate stays shut until the user
  decides. Exposed as POST /intake/step -> { updated_spec, buildable, next_question | null,
  contradictions[] } (+ the gate verdict and an auditable extraction report of what was rejected
  and why). 272 tests + lint green; the service boots and answers live on the fake provider. The
  refined confirmation / "the whole" stays Layer B's job; gate wiring is B043.
- 2026-08-07 — Strategy & moat written (docs/STRATEGY.md): the full user flow with its three
  connecting gaps (intake agent, cost estimate, component library), and the bigger ideas that make
  Scio structurally better + cheaper than Lovable — the library as a growing 5-layer asset,
  build-without-the-LLM, fleet learning, determinism-first, a measurable quality gate, speed, and
  predictable pricing (the compounding moat). Plus honest core-vs-moat sequencing and a Settings
  control for model passes (1 = same model twice; more = best -> review -> best).
- 2026-08-12 — B041b: full build-plan orchestration + incremental app assembly
  (apps/engine/builder/orchestrate.py). **Scio now generates a whole app end to end**:
  intake -> Layer A -> Layer B -> Layer C -> built, tested, instrumented, running app —
  fake/scripted-driven here, real the moment keys are added. Packages build in Layer C's
  topological order, each generated INTO the workspace the earlier ones already occupy, with
  one sandbox, one URL and one app-wide manifest — so package N integrates with 1..N-1 rather
  than being correct alone and wrong together. Each package is told what is already standing
  (files + ids already taken) on top of its contract. The guardrails became app-wide: the id
  snapshot now covers every built package, so a new package colliding with an earlier id is
  rejected and rolled back at the moment it is written. Cross-package failure isolation: a
  package that cannot meet its "done when" at the cap is isolated, its dependents are marked
  **blocked** (transitively, naming the root cause) and never built on broken ground, while
  independent packages keep building; the aggregate says "2 of 5 parts work" with every
  remainder named. The assembled app is persisted as one build_version + git_sha with the
  app-wide manifest even when parts need a look, and per-package progress events stream for
  the build view's real progression. 233 tests + lint green. **Verified live**
  (scripts/verify_build_plan.py): five packages assembled into ONE running Next.js app —
  `/`, `/booking` and `/menu` all render in the same server, each showing the foundation's
  shell *and* its own package's elements, no console failures, 19 instrumented elements
  app-wide, one commit. That live run also caught a real bug the scripted tests hid:
  Playwright's sync API refuses to run inside a running asyncio loop, so the preview is now
  driven off the event loop.
- 2026-08-12 — B041a: the single-package build loop (apps/engine/builder) — the relay, the
  core and Layer C's contracts joined into one capped loop: generate -> write ->
  instrumentation verify -> validation agents -> run + look (screenshot + classified console)
  -> critique against the package's "done when" -> fix -> repeat, capped. All three B040
  guardrails hold *inside* the loop: a fix that drops a data-scio-id is rejected and rolled
  back to the previous code (the file on disk is proven unchanged), a favicon 404 passes while
  the identical message from /api/... fails, and a package that runs out of attempts comes back
  as "needs a look" with named remainders instead of a silent pass. Deterministic parts stay
  deterministic — file paths per package (file_plan), security/quality/tests/contract agents
  (validation) — and judgment is used only where judgment is needed (critique), where an
  unparseable verdict counts as a fail. Code arrives in a strict FILE-block format; paths
  outside the package (and any `..` traversal) are dropped rather than written. Each build is
  persisted as a build_version + git_sha with its manifest **in the same commit**, so a
  restored version carries its own marking->code coupling. 213 tests + lint green, and the
  real preview path was run live: dev server booted, Playwright rendered and screenshotted the
  page, and the favicon 404 was suppressed rather than failing the build. Full-plan
  orchestration (dependency order, assembly, aggregate status) is B041b/B042.
- 2026-08-09 — B040: the real sandbox + marking->code core (apps/engine/core) — the shared
  hard part gates 2 and 3 both run on, **with both spike guardrails enforced in code**.
  SandboxProvider with local docker/process implementations (AcaSandbox wired per ADR-0005
  but never run here and honest about it); the manifest **derived from source** by a builder
  rather than hand-written; the coupling persisted beside the code so a project resumes with
  markings intact. Guardrails: (1) the verifier rejects any regeneration that loses a
  data-scio-id — the spike's silent failure is now a failed build, and the change is rolled
  back; (2) the resolver raises instead of climbing to a parent, naming the ancestor as
  evidence rather than using it as an answer; (3) the console classifier judges by source, so
  a favicon 404 passes while the identical message from /api/... fails. Directed regeneration
  enforces isolation by hash and refuses a regenerator that reaches outside its package.
  200 tests + lint green, and scripts/verify_core.py proved all eight steps against a real
  running sandbox (boot, screenshot, classified console, strict click resolution, the lost-id
  refusal, a change touching 1 file with 5 byte-identical, and a rejected regeneration rolled
  back cleanly).
- 2026-08-09 — B039 spike: the sandbox + marking->code mechanic proven locally
  (spikes/sandbox-marking, see FINDINGS.md). **Verdict: the mechanic is sound — build it.**
  End to end: a SandboxProvider interface with a local implementation serving a live preview
  (ready in ~7s), Playwright capturing screenshot + console, a click at (x,y) resolving to
  its element -> Layer C package -> source line, a directed change touching only that
  package's file, and a hash proof that the other 5 files stayed byte-identical. 16 tests.
  **Headline finding: a lost data-scio-id does not fail loudly — the click falls through to
  the nearest instrumented ancestor and resolves to the WRONG package**, so a directed change
  would rewrite the app shell instead of the marked button. Defences: emit the manifest from
  the builder, and verify instrumentation after every regeneration. Second finding: a missing
  favicon logs a console 404 on every load whose text names nothing, so the vision loop must
  classify console noise by source URL or it would fail every build ever made. Not proven:
  isolation (no Docker daemon here — it ran as a process), ACA at scale, and real LLM
  regeneration.
- 2026-08-09 — B038: Layer C built in the engine (apps/engine/layerc) — **the A -> B -> C brain
  is now complete**. A Layer B architecture becomes a validated build plan: deterministic
  decomposition into foundation / schema / auth / one-package-per-feature / connectors / tokens,
  a dependency graph topologically ordered (foundation first, schema and tokens before the
  features that use them, auth before protected features), sibling packages flagged
  parallelizable. Each package carries a full contract — its architecture slice in detail, its
  dependencies' *interfaces* only (never their code), the why, the house rules, canonical
  vocabulary, scope guard and testable acceptance criteria — assembled into the builder's prompt.
  Plan validation before building catches dropped nodes, cycles, missing dependencies, broken
  order and incomplete contracts. The relay is consulted only for genuinely ambiguous grouping.
  API: POST /plan. 155 tests + lint green; full A->B->C chain verified live, including a
  decomposition fix so operation-less shell screens (Home) belong to the foundation package
  instead of silently vanishing.
- 2026-08-07 — Layer C defined (ADR-0013 + docs/LAYER-C.md): decompose the architecture graph into
  a dependency-ordered graph of small, contract-bearing build packages (per-feature granularity),
  with deterministic grouping, topological ordering, and plan validation before building. This is
  the marking->code mapping and the basis for directed regeneration, cost control, and failure
  isolation.
- 2026-08-07 — Full technical architecture written (docs/ARCHITECTURE.md, replacing the skeleton):
  service topology, the agent set (intake, architect, planner, design, builder, vision/critique,
  validation) on the matrix + multi-pass relay, the shared A->B->C + sandbox + marking->code +
  vision-loop core, end-to-end gate flow, data/persistence, cross-cutting security & cost,
  type-awareness, and the built-vs-to-build sequence.
- 2026-08-07 — Product overview written (docs/PRODUCT-OVERVIEW.md): the full refined vision —
  one engine / three gates, the shared A->B->C + sandbox + marking->code core, lifecycle &
  persistence, reference RAG, cost/estimate/budget, build-failure handling, security, wait UX,
  and the three types (app/website/automation) with build order. Captured from the spec walkthrough.
- 2026-08-09 — B034: Layer B built in the engine (apps/engine/layerb) — a buildable
  AppSpec now yields all three LAYER-B.md outputs. Deterministic backbone (no LLM):
  canonical vocabulary collapsing variant terms to one name, entities → tables with
  relations and RLS on, sign_in → auth (no sign-in means no auth tables and contact-based
  identity), roles → RBAC, actions → typed operations + screens/routing, sensitivity →
  secure-by-default posture, conditionals → connectors, look → design tokens; every node
  records the spec field it came from. Rule validation runs BEFORE any generation and
  returns violations plus the exact spec fields to reopen surgically (missing entity,
  ghost permission, no-login-vs-roles/user-data conflict, dangling FK). The whole is
  generated through the B031 relay from a grounded fact set with assumptions flagged from
  Layer A metadata, falling back to a deterministic narrative if no model answers. The
  playbook (playbook.yaml: locked ADR-0011 stack, structure, naming, secure-by-default,
  tests, a11y) assembles into build context. API: POST /architecture (422 on a
  non-buildable spec). 115 tests + lint green; live runs verified, including a derivation
  fix so "book a table" yields create_booking rather than create_table.
- 2026-08-09 — B031: engine execution machinery (apps/engine/execution) — the layer
  Layer B, extraction and codegen will run on. A ModelProvider abstraction with
  Anthropic / OpenAI (incl. Azure OpenAI) / Google implementations plus a deterministic
  FakeProvider bound via a registry, so the whole flow runs with no API keys; a
  data-driven capability matrix (matrix.yaml: 7 task types → ranked models with
  cost/latency/context metadata) with top_n selection; the transparency narration; and
  the multi-pass relay (best model → review passes → final pass back in the best),
  with structured Pydantic hand-off between passes, per-task pass count, a hard 4-pass
  cap, timeouts + retries, and a budget hook for 4.5 metering. API: POST /generate
  streams narration + each pass + result as SSE, POST /generate/plan previews the
  selection, GET /matrix/tasks lists the rankings. 56 tests + lint green; live SSE run
  verified. No extraction, no Layer B logic, no codegen yet — those build on this.
- 2026-08-07 — Layer B defined (ADR-0012 + docs/LAYER-B.md) and generated-app stack locked
  (ADR-0011: Next.js + TypeScript + Tailwind + Supabase). Layer B manufactures the prompt
  substrate: the whole, a machine-readable architecture graph, and the generation playbook,
  with rule-based validation before generation.
- 2026-08-08 — Layer A built in the engine (apps/engine — the engine scaffold now exists:
  Python + FastAPI + Pydantic, ruff + pytest, .env.example, /health): the INTAKE-SCHEMA
  as typed models (FieldMeta with value/source/confidence/provenance, DownstreamTag enum,
  AppSpec with core / conditional / defaulted-and-flagged fields), is_buildable() per the
  gate rule, trigger detection (incl. multiple-roles and sensitive-data derived triggers),
  downstream-tag mapping for Layer C, and POST /intake/validate returning the verdict +
  what's still needed. 21 tests + lint green; service boot verified live. No extraction/LLM
  calls yet (4.3); matrix + multi-pass is the next engine kickoff (B031).
- 2026-08-07 — Layer A intake schema defined (ADR-0010 + docs/INTAKE-SCHEMA.md): six core
  fields + conditional follow-ups + non-goals, per-field metadata (value/source/confidence/
  provenance), downstream build-area tags, and the is_buildable gate rule. Part of a
  three-layer model: A intake -> B understanding -> C build plan.
- 2026-08-08 — Phase 3.5a real React app, step 1 (apps/app): Vite + React + TS + Tailwind
  scaffold with the DESIGN.md tokens as CSS variables (light default + dark toggle, fonts
  loaded), design-system components from the prototype (buttons, status chips, sidebar,
  topbar, state cards, logo tile), React Router shell, Clerk sign-in guarding the app, and
  a typed API client (@scio/shared) that attaches the Clerk JWT and surfaces 401/400/network
  errors. Projects (GET, with loading/empty/error states) and Create (POST → back to list)
  are wired end-to-end; remaining screens are placeholders for step 2 (B022). Degrades
  gracefully without Clerk keys (config notice) or backend (error state + retry). Build +
  8 frontend tests green; full-stack run documented in apps/app/README.md.
- 2026-08-08 — Phase 3.4 project CRUD (apps/api): first real persisted endpoints —
  POST/GET/PATCH/DELETE /projects with workspace-scoped access via the 3.3 scoping
  (create stamps workspace_id, list excludes soft-deleted and sorts newest first,
  cross-tenant access is 404), class-validator DTOs in @scio/shared with a global
  ValidationPipe (400 on invalid bodies), soft-delete via deleted_at, and OpenAPI
  schemas for all five endpoints. Proven by an e2e test suite (fake identity, two
  workspaces): full lifecycle, validation, 401, cross-tenant isolation — 20 tests green.
  This completes the Phase 3 backend foundations (auth + projects).
- 2026-08-08 — Phase 3.3 backend auth (apps/api): Clerk session-JWT verification behind a
  swappable IdentityVerifier interface (ADR-0008), global auth guard with @Public()
  exemptions (/health, Clerk webhook stub), get-or-create provisioning (first authenticated
  request creates the user AND their MVP one-per-user workspace in a transaction), and
  request context (@CurrentUser/@CurrentWorkspace) wired through every module. Tenant
  scoping is now enforced at the data layer via a WorkspaceScope Prisma extension that
  filters/stamps workspace_id on scoped models. Proven with a fake verifier in tests
  (13 passing) + live 401/public-route checks; no real Clerk keys in this environment.
- 2026-08-08 — Phase 3.2 backend skeleton (apps/api): NestJS + Prisma with the full
  DATA-MODEL schema (12 models + pgvector reference_embedding, initial migration,
  docker-compose Postgres), typed API contract in packages/shared (@scio/shared),
  Swagger at /docs, GET /health with DB connectivity, module stubs for
  workspace/user/auth/project/spec/design/build/deployment/reference/usage/notification,
  and an SSE stream stub. Build, boot, health and tests verified green. Auth logic and
  CRUD deliberately left for 3.3/3.4.
- 2026-08-07 — Phase 3.1 data model defined (ADR-0009 + docs/DATA-MODEL.md): workspace-scoped
  tenant isolation, git-backed version content, JSONB for spec/whole/status, pgvector for RAG,
  deployment + notification tables added, billing deferred to Phase 12.
- 2026-08-07 — Phase 2 app-shell prototype complete: every screen clickable with mocked
  data (projects, create/type-select, wizard + wholeness panel, spec gate, involvement,
  design mode with numbered annotation, build view, reveal + honest status, live feedback,
  versions, ship/export, settings, error & empty states, notifications) -> apps/app/prototype.html.
- 2026-08-07 — Phase 1 (brand) complete: logo (assets/logo/scio-logo.svg, concept B tile
  monogram) and first marketing site (apps/website/index.html). Design tokens already in
  docs/DESIGN.md.
- 2026-08-07 — Phase 0.2 stack decisions: cloud Azure (ADR-0004), sandbox ACA dynamic
  sessions (ADR-0005), backend Node/TS + Python engine (ADR-0006), database Postgres on
  Azure (ADR-0007), auth Clerk (ADR-0008).
- 2026-08-07 — Established the full planning baseline in the repo: repo + docs, CLAUDE.md
  (with the documentation & checkpoint protocol), wedge (ADR-0001), name Scio (ADR-0002),
  visual identity (ADR-0003) + docs/DESIGN.md, the customer journey (docs/UX-FLOW.md), and
  the full build plan (docs/PROJECT-PLAN.md).

### Next
- Step 4: add API keys, verify the capability matrix's model IDs, and make a real end-to-end run
  against Claude. Then the component library (the nave) and the cost estimate, per docs/STRATEGY.md.
