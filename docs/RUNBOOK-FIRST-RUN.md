# Runbook — the first REAL run

Everything built so far has run against the stand-in: a deterministic builder that
writes correctly instrumented placeholder files. That proves the *pipeline*. It
proves nothing about the code. This runbook is how you point the same pipeline at
a real Claude key for the first time, in your own environment, and see what it
does.

Read the whole thing once before starting. It takes ~20 minutes of setup and one
build; the build costs real money (see [Cost](#cost)).

- **Status:** written for B053. The run itself is operator-driven and has not
  happened yet — what it surfaces gets hardened next (B054).
- **Related:** `docs/STRATEGY.md` §E (model passes), ADR-0006 (engine + providers),
  ADR-0011 (the generated-app stack), `docs/COSTS.md`.

---

## 0. What you need

| Thing | Why | Notes |
|---|---|---|
| Node 20+ and pnpm | api, app, and the generated app's `npm install` | `node --version` |
| Python 3.11+ | the engine | |
| Docker | Postgres (and, if present, a real sandbox boundary) | |
| A Clerk instance | sign-in (ADR-0008) | free tier is fine |
| An Anthropic API key | the actual point | `console.anthropic.com` |
| ~2 GB free disk | the generated app's `node_modules` | cached and shared across builds |

**Before you spend anything**, open the Anthropic console and check two things
against `apps/engine/src/scio_engine/execution/matrix.yaml`:

1. the **model id strings** are current, and
2. the **prices** still match `cost_per_mtok` (which is USD per 1M *output*
   tokens — the relay prices a pass on its output).

The matrix is data, not code: edit the YAML, restart the engine, done. Ids are
complete as written — never append a date suffix.

---

## 1. Postgres + migrations

```bash
# repo root
docker compose up -d db

cd apps/api
cp .env.example .env        # DATABASE_URL already points at the compose db
pnpm install
pnpm prisma:migrate         # applies migrations
pnpm prisma:generate
```

Check: `docker compose ps` shows `db` healthy, and `pnpm prisma:migrate` ends with
migrations applied (or "No pending migrations").

## 2. Clerk keys

In the Clerk dashboard → **API keys**, from the *same* instance for both:

```bash
# apps/api/.env
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# apps/app/.env   (cp .env.example .env first)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

Mismatched instances is the classic failure: the app signs you in, every API call
returns 401.

## 3. The engine: the key, and the 1 + Claude profile

```bash
cd apps/engine
cp .env.example .env
```

Then set these five in `apps/engine/.env` — this is the whole configuration for a
real run:

```bash
ANTHROPIC_API_KEY=sk-ant-...

SCIO_ONLY_PROVIDER=anthropic
SCIO_MODEL=claude-sonnet-5
SCIO_MODEL_PASSES=1
```

What they mean:

- `ANTHROPIC_API_KEY` — **the switch**. With no provider key set, the engine runs
  the fake provider and the build uses the stand-in. Set it and everything becomes
  real. (`SCIO_FAKE_PROVIDERS=1` forces the fake path back on regardless — that is
  how CI runs, and it must keep working.)
- `SCIO_ONLY_PROVIDER=anthropic` — no OpenAI or Gemini call is attempted.
- `SCIO_MODEL=claude-sonnet-5` — every task ranks this one model. Any current id
  works, including one the matrix does not list yet.
- `SCIO_MODEL_PASSES=1` — **1 means one model, run twice**: it generates, then
  reviews its own work (STRATEGY §E). It is not one raw call. Leave it unset for
  the full 4-pass relay over the ranked matrix — better output, roughly 4× the
  spend on a single model, more with several.

Swap `claude-sonnet-5` for `claude-opus-5` when you want the strongest code and
accept the price; `claude-haiku-4-5` is the cheapest way to check that the wiring
is alive.

## 4. Start the three services

```bash
# terminal 1 — engine
cd apps/engine
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,providers]"      # 'providers' pulls in the Anthropic SDK
uvicorn scio_engine.main:app --reload --port 8000

# terminal 2 — api
cd apps/api && pnpm dev                # http://localhost:3000

# terminal 3 — app
cd apps/app && pnpm install && pnpm dev  # http://localhost:5173
```

**Check the engine before doing anything else:**

```bash
curl -s localhost:8000/health
```

```json
{
  "status": "ok",
  "providers": "real",
  "profile": "claude-sonnet-5 only, 2 passes (setting 1: one model, generate then self-review)",
  "builder": "model"
}
```

If it says `"providers": "fake"` and `"builder": "standin"`, **stop**: the key did
not reach the process (wrong file, not exported, server started before the edit).
Everything downstream would be placeholder code that looks like a successful build.

## 5. The run

Sign in at <http://localhost:5173>, then:

1. **New project** — name it something small and concrete. A restaurant booking
   app is the shape everything has been tested against.
2. **Wizard (gate 1).** Answer in your own words. Now the questions come from a
   model instead of the guide's canned list: they should be specific to what you
   just said, and a contradiction should come back as a question rather than
   being silently resolved. The wizard closes when the spec is buildable.
3. **Review (gate 1 → 2).** Read *the whole* — the narrative of what will be
   built. This is the thing you approve, and it is the first time a real model
   writes it. Approve it.
4. **Build.** Watch the events: `started` names the plan and the models, then one
   `progress`/`package` pair per part. Expect **minutes**, not seconds — a real
   model writing several complete files per package, twice, plus a dev server
   recompiling and a browser looking at it between packages.
5. **Reveal.** The running app, embedded, plus the honest summary: what works,
   what needs a look, what is blocked, and the remainders.

Then actually *use* the app in the frame. That is the only test that matters.

---

## What to watch for

This run exercises four things for the first time. Each has a specific failure
signature.

**1. Real code is not stand-in code.** The stand-in emits exactly the files the
contract names, always parseable, always instrumented. A real model writes prose
around code, invents a file, occasionally returns a diff. The guardrails are built
for this — a path outside the package is dropped, a lost `data-scio-id` fails the
build and rolls it back — so the interesting outcome is not "it worked", it is
*which guardrail fired and whether its message told you why*. Watch the per-package
`attempts` in the build events.

**2. The instrumentation contract meets a real model.** Every element must carry
`data-scio-id` and `data-scio-package`; the manifest is derived from the source, so
marking→code coupling is only as good as the model's compliance. If packages fail
on `[instrumentation]`, the rules in the codegen prompt need strengthening — that
is a prompt fix, not a code fix, and it is the most likely thing this run surfaces.

**3. The sandbox now installs and runs a REAL app.** The workspace is generated
(not borrowed): `package.json` for the locked stack — Next.js + TypeScript +
Tailwind + Supabase (ADR-0011), pinned — plus tsconfig, next.config, postcss and a
default Tailwind config, then `npm install` as an **explicit step before anything
serves**. That ordering is the fix for the constraint the spike found: a dev server
told to install on first boot dies mid-startup, so `LocalProcessSandbox.start()`
refuses a directory without `node_modules`.

The install goes to a cache keyed by the dependency set (`SCIO_DEPS_CACHE`,
default `apps/engine/out/deps`) and is symlinked in, so:

- the **first** build pays ~35 s and ~200 MB;
- every build after that pays a symlink.

Verify it yourself before the run, without spending anything on models:

```bash
cd apps/engine && source .venv/bin/activate
python - <<'PY'
from scio_engine.builder.workspace import prepare_workspace
ws = prepare_workspace("install-probe")
print(ws, sorted(p.name for p in ws.iterdir()))
print("node_modules ->", (ws / "node_modules").resolve())
PY
```

Then serve what it made:

```bash
cd apps/engine/out/projects/install-probe && npm run dev
```

If npm is unavailable or the network is blocked, the build falls back to the
repo's spike app (`spikes/sandbox-marking/example-app`) when that has
`node_modules`, or fails with `WorkspaceUnavailable` and npm's own error — never
by quietly building something that cannot run. `SCIO_SCAFFOLD_DIR` points at a
prepared directory instead, for an offline machine.

**4. Every build leaves a dev server running.** By design: the reveal embeds the
app you just watched being built, so tearing the sandbox down at the last event
would hand you a dead frame. Nothing reaps them yet.

```bash
# after a session — see what is still up, then stop it
ps aux | grep "next dev"
pkill -f "next dev"

# workspaces and screenshots accumulate too (the deps cache is worth keeping)
rm -rf apps/engine/out/projects/*
```

Restarting the engine does **not** stop them: they are child processes of a
process that has already handed the URL to the browser.

---

## Cost

`SCIO_MODEL_PASSES=1` on a five-package plan is roughly: 5 packages × 2 codegen
passes + a critique per package + Layer B's whole + intake turns ≈ 20-25 model
calls, most of them writing several complete files. Codegen is allowed up to
16,000 output tokens per call (a package is several whole files; the old 4,096
default cut the third one in half).

Budget accordingly, and set `budget_usd` if you want a hard stop — a relay that
would exceed it raises `BudgetExceeded` rather than spending. Sonnet is roughly a
third of Opus's output price; Haiku is roughly a fifth of Sonnet's.

## If it goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `/health` says `fake` / `standin` | no key in the process | check `apps/engine/.env`, restart uvicorn |
| `ProviderError: anthropic SDK not installed` | missing extra | `pip install -e ".[providers]"` |
| `not_found_error: model` | id is wrong or unavailable to your key | check the console; do not add a date suffix |
| Packages fail on `[codegen]` "cut off" | package is bigger than the output budget | it retries automatically; if it persists, raise `CODEGEN_MAX_TOKENS` |
| Packages fail on `[instrumentation]` | the model dropped a `data-scio-id` | expected finding — strengthen the codegen rules |
| `WorkspaceUnavailable: npm install failed` | network or registry | run the install probe above on its own |
| Build never starts, `not_buildable` | spec did not pass gate 1 | finish the wizard |
| 401 on every API call | Clerk key mismatch | same instance for api and app |

Everything the run surfaces goes back into the backlog as **"Harden the first real
run"** — that is the point of doing it.
