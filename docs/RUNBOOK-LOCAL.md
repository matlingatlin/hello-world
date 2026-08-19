# Runbook — running the whole product locally

One command brings up **engine + api + app + Postgres** in this sandbox, with no
Clerk, no hosted database, no Docker and no API key:

```bash
scripts/dev-up.sh          # start everything
scripts/dev-down.sh        # stop it again (--wipe also deletes the database)
```

Then open <http://127.0.0.1:5173> and sign in with any email.

This exists because the engine was proven and tested long before anyone had
*used* the product. Opening it needed a Clerk account, two keys and a database
someone else hosted — so nobody ever clicked through it, and the first
click-through found four real bugs in an hour (see the CHANGELOG for
2026-08-12).

---

## What it starts

| | where | what it is |
|---|---|---|
| app | <http://127.0.0.1:5173> | Vite dev server, `VITE_DEV_AUTH=1` |
| api | <http://127.0.0.1:3000> | Nest, `SCIO_DEV_AUTH=1`, `APP_ORIGIN` set, docs at `/docs` |
| engine | <http://127.0.0.1:8000> | FastAPI, fake providers unless a key is set |
| Postgres | `127.0.0.1:55432`, db `scio` | a real PostgreSQL 16 **process** |

Logs are in `.local/*.log` (gitignored). Ports are overridable:
`SCIO_APP_PORT`, `SCIO_API_PORT`, `SCIO_ENGINE_PORT`, `SCIO_PGPORT`,
`SCIO_PGDATA`.

## Prerequisites

The sandbox already has Node, pnpm, the engine's `.venv` and PostgreSQL 16. One
package is **not** in the base image and the script checks for it:

```bash
apt-get install -y postgresql-16-pgvector
```

The api's first migration begins `CREATE EXTENSION "vector"` (pgvector, for
reference retrieval), so without it migration `0001_init` fails on its second
line. The script stops with that exact message rather than a Prisma stack trace.

`PGDATA` lives at `/var/lib/postgresql/scio-dev` — outside the repo, because
Postgres refuses to run as root and the data directory has to belong to the
`postgres` user. It also means a database can never end up in a commit.

## Dev auth

Both halves are behind a flag, and both are additive — production still means
Clerk, unchanged.

- **api** (`SCIO_DEV_AUTH=1`) binds `DevIdentityVerifier` instead of
  `ClerkIdentityVerifier` behind the same `IdentityVerifier` interface
  (ADR-0008). The bearer token *is* the identity: `dev` → `dev@scio.local`,
  `dev:ada@example.com` → that user. Everything downstream — provisioning,
  workspace scoping, the guard — is the real thing.
- **app** (`VITE_DEV_AUTH=1`) swaps Clerk's provider, gate, sign-in screen and
  user button for local equivalents (`src/lib/auth.tsx`). You sign in by typing
  an email; it is kept in `localStorage`.

**A different email is a different workspace**, so tenant scoping can be
exercised by hand:

```bash
curl -H "Authorization: Bearer dev"                 localhost:3000/projects
curl -H "Authorization: Bearer dev:ada@example.com" localhost:3000/projects
```

`SCIO_DEV_AUTH=1` together with `NODE_ENV=production` is refused at boot, not
honoured — dev auth accepts any `dev` token and must never run in production.

## The click-through

1. **Sign in** — any email.
2. **New project** — describe it in a sentence.
3. **Wizard** — answer in your own words. On the free path expect **one field
   per answer** (see below), and expect the wizard to notice a contradiction and
   ask about it.
4. **Review** — the whole in prose, the spec field by field, the assumptions,
   and the cost estimate as a range. Approve it.
5. **Build** — one progress line per part, streamed over SSE.
6. **Reveal** — the built app running in an iframe, plus what is true about the
   build.

## Level 2 — the design window

Approving a spec now asks one question: **just build it**, or **shape the design first**.
The second is Level 2, at `/projects/:id/design`:

1. A preview is built (streamed, same per-part progress as a build) and embedded.
2. **Use / Mark.** In Mark, clicking anything in the preview adds it to *your changes*;
   the app's own behaviour is suppressed so marking a Submit button does not submit.
3. Each change gets a note. **Generate again** sends all of them plus the free prompt as
   ONE change, and only the packages they touch are rebuilt. The panel then shows which
   files changed and how many others were byte-identical.
4. A marking that argues with the approved spec comes back as a **question** and nothing
   is built: *Keep it as-is*, or *Change the plan*. Dropping a protection asks a second
   time and records an **allowance** on a new spec version rather than rewriting the
   security posture.
5. **Versions** lists every change, and *Return to this version* really checks that
   commit back out (and refuses if its code no longer matches its instrumentation).

If the preview has stopped — pressing **Build it** recreates the workspace and takes the
preview with it — the window says so and offers **Build the preview again**.

`POST /projects/:id/design/preview` builds the app with the marking bridge in it, so the
design window can hear about clicks it cannot see (the preview is cross-origin). The
bridge posts only to `APP_ORIGIN`, which `dev-up.sh` sets for you; without it the api
refuses to generate a preview rather than handing back a window where nothing is
clickable. A delivery build — the ordinary `POST /projects/:id/build` — carries no bridge.

**Open the app on the origin `APP_ORIGIN` names.** The bridge's target origin is baked
into the preview at build time, so visiting `localhost:5173` when `APP_ORIGIN` says
`127.0.0.1:5173` makes marking silently do nothing. The design window waits for the
bridge to say hello and tells you this in so many words rather than looking merely
unresponsive — but the fix is to use the right origin, or to set `APP_ORIGIN` to yours
and generate the preview again.

## Free vs real

Without keys the engine runs its stand-ins: `StandInIntakeProvider` for gate 1
and `StandInProvider` for the builder. The pipeline is real — every gate, every
guardrail, the SSE stream, the sandbox, the reveal — but the *content* is not
model output. The intake stand-in files each answer under the question that was
asked, so a spec takes about twelve answers instead of three or four; the
builder's stand-in emits placeholder files, which the reveal says out loud.

For a real build, put a key in the environment before starting:

```bash
ANTHROPIC_API_KEY=sk-ant-… SCIO_MODEL=claude-sonnet-5 SCIO_MODEL_PASSES=1 \
  scripts/dev-up.sh
```

Check <http://127.0.0.1:8000/health> says `"providers":"real"` and
`"builder":"model"`. See `RUNBOOK-FIRST-RUN.md` for what a real run costs and
what to watch for, and for `SCIO_VERIFY_DATA=1`, which runs the build against a
real in-process database and drives the generated app.

## When something is wrong

| symptom | cause |
|---|---|
| every request 401s | the app and api disagree about dev auth — both flags, or neither |
| every request blocked by CORS | `CORS_ORIGINS` does not name the app's origin |
| `extension "vector" is not available` | pgvector is missing — see Prerequisites |
| the wizard repeats one question | an engine older than 2026-08-12; the intake stand-in is what fixed it |
| a code change has no effect | something survived `dev-down.sh`; check `ps` — `nest start` forks a child |
| "Can't reach the Scio API" on the build screen | the api really is down; a StrictMode abort used to cause this and no longer does |
| clicking the preview in Mark mode adds nothing | the app is open on a different origin than `APP_ORIGIN` — see Level 2 |
| the design preview shows "Internal Server Error" | it stopped (usually a later build recreated the workspace) — press *Build the preview again* |
