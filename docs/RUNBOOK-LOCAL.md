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
| engine | <http://127.0.0.1:8000> | FastAPI, fake providers unless a key is set, `SCIO_CATALOG_DB` set |
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
curl -H "Authorization: Bearer dev"                 localhost:3000/v1/projects
curl -H "Authorization: Bearer dev:ada@example.com" localhost:3000/v1/projects
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
   and the cost estimate as a range. **Every field here is correctable**: press
   `correct` on a row to change it, or use *Belongs under* to move an answer the
   wizard filed in the wrong slot. A correction that opens new work (two roles
   trigger `role_permissions`) says so and asks for it inline, and approve stays
   disabled until it is answered. Then approve it.
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

## The library, growing

Every delivery build offers its work back to the component library (B061), and
the engine keeps what survives in the same Postgres, in its own `library_*`
tables:

```bash
curl -s localhost:8000/library/entries | python3 -m json.tool | head -40
curl -s -X POST localhost:8000/library/entries/booking.1.1/approve
curl -s -X POST localhost:8000/library/entries/booking.1.1/reject
```

`persistent: false` in that listing means `SCIO_CATALOG_DB` is unset — the
library still matches and assembles from the seeds, it just cannot keep anything
it learns. `dev-up.sh` sets it for you.

Contributed entries are **provisional** until somebody approves one. They are
offerable while provisional (they cleared every gate a seed does, plus a
re-verification a seed never had) — what provisional changes is that the listing
says so.

A preview build (Level 2) contributes nothing: it is a draft the user is about
to change.

## Reaching it from another device — you can't, and here is why

The stack binds loopback inside a sandbox that has **no inbound path at all**: no
platform port-forward, no preview URL, nothing that can dial in. So the only way
to open the product on a phone is an outbound tunnel, and every free tunnel fails
on the same rule.

Outbound, measured against `example.com`:

| port | result |
|---|---|
| 80 | open |
| 443 | open |
| 22 | blocked |
| 8080 | blocked |

Only 80 and 443 leave, and 443 is TLS-terminated and re-issued by the egress
gateway (`O = Anthropic, CN = Egress Gateway SDS Issuing CA`), which also
allowlists by host. Every tunnel wants a port that is not 443:

| tool | needs | result |
|---|---|---|
| `cloudflared` (quick tunnel) | TCP/UDP **7844** to the Cloudflare edge | its own pre-check: `UDP … FAIL`, `TCP … FAIL`, `Cloudflare API 443 PASS`. `--protocol http2` does not help — http2 is the transport, 7844 is still the port |
| `localtunnel` | a random high port (**25105** on the run we tried) | control plane over 443 answers and hands out the port; connecting to it times out |
| `tunnelmole` | `wss://service.tunnelmole.com:**8083**` | client hangs with no socket ever opened |
| `ngrok` | an account token, and `tunnel.ngrok.com:443` | `/root/.ccr/README.md` names ngrok as unsupported through this proxy; no token can be created from in here anyway |
| `serveo`, `localhost.run`, `pinggy` | SSH | no `ssh` binary, port 22 blocked, and SSH-on-443 gets no banner — the interceptor is waiting for a ClientHello |

What *does* pass is an ordinary WebSocket on 443: an `Upgrade: websocket` over
HTTP/1.1 returns `101 Switching Protocols` through the gateway. So the shape that
would work is a relay speaking WebSocket on 443 — there just isn't a free,
signup-less one. Note that HTTP/2 must be avoided: negotiate h2 and the upgrade
silently degrades to a plain `200`.

**The answer is a Codespace** (B080): it runs the stack *and* forwards ports, so
each one gets an `https://<name>-<port>.app.github.dev` origin openable from a
phone — no deploy, no hosting decision, no key. `scripts/dev-up.sh` is the same
command there; it derives the forwarded URLs from `$CODESPACE_NAME` and wires
`VITE_API_URL`, `CORS_ORIGINS` and `APP_ORIGIN` to them. See
**`RUNBOOK-CODESPACES.md`**.

A real public deploy — for people who are not you, without a Codespace running —
is still open (B079). Whatever hosts it has to expose **both** the app and the
api, because the browser calls the api directly.

## When something is wrong

| symptom | cause |
|---|---|
| every request 401s | the app and api disagree about dev auth — both flags, or neither |
| every request blocked by CORS | `CORS_ORIGINS` does not name the app's origin |
| `extension "vector" is not available` | pgvector is missing — see Prerequisites |
| the wizard repeats one question | an engine older than 2026-08-12; the intake stand-in is what fixed it |
| approve is refused with "this spec still needs…" | the gate is genuinely shut — answer what the review screen lists |
| a correction "doesn't stick" after a wizard turn | it should; extraction refuses to overwrite `corrected-on-review`. If it does, that rule broke |
| a code change has no effect | something survived `dev-down.sh`; check `ps` — `nest start` forks a child |
| the library never grows | check `persistent` in `/library/entries`; then read the `library` event in the build log for the refusal reason |
| "Can't reach the Scio API" on the build screen | the api really is down; a StrictMode abort used to cause this and no longer does |
| clicking the preview in Mark mode adds nothing | the app is open on a different origin than `APP_ORIGIN` — see Level 2 |
| the design preview shows "Internal Server Error" | it stopped (usually a later build recreated the workspace) — press *Build the preview again* |
