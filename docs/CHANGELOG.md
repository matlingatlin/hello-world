# Changelog
Running log of decisions and changes for Scio. Newest first.
See CLAUDE.md, "Documentation & checkpoint protocol", for how this is maintained.

## [unreleased]

### Added
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
