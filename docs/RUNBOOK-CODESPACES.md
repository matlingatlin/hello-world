# Runbook — running Scio in a GitHub Codespace (open it on your phone)

The product runs happily on localhost and, until now, could only be *clicked*
there. This sandbox has no inbound path and lets nothing but ports 80 and 443
out, so no tunnel can work — measured in detail in `RUNBOOK-LOCAL.md`,
"Reaching it from another device" (B079).

A Codespace solves it from the other side: it runs the stack **and** forwards
ports, giving each one an https origin you can open anywhere you are signed in
to GitHub:

```
https://<CODESPACE_NAME>-<port>.app.github.dev
```

No deploy, no hosting decision, no key. Free clicking, because the engine falls
back to its stand-ins when there is no key to use.

---

## The five steps

1. **Open the repo in a Codespace** — on github.com: *Code ▸ Codespaces ▸ Create
   codespace on master*. First creation takes a few minutes: it builds the image
   (PostgreSQL 16 + pgvector), installs Node 20, Python 3.11, the pnpm workspace
   and the engine's venv.

2. **Start everything** — in the Codespace terminal:

   ```bash
   scripts/dev-up.sh
   ```

   The same script as everywhere else. It initialises the cluster, applies the
   Prisma migrations and starts engine, api and app; it prints the forwarded URLs
   rather than loopback ones when it sees `$CODESPACE_NAME`.

3. **Make the api port public** — once per Codespace:

   ```bash
   gh codespace ports visibility 3000:public -c $CODESPACE_NAME
   ```

   This is the step that is easy to skip and expensive to debug. A forwarded port
   is **private** by default, which means GitHub asks for a session cookie; the
   app's `fetch` to the api is cross-site, so the browser sends no cookie and the
   api answers with GitHub's sign-in page. The app reports that honestly as
   *"Can't reach the Scio API"*, and everything looks broken for a reason that has
   nothing to do with Scio. (Port visibility cannot be set in `devcontainer.json`
   — only from the **Ports** panel or the CLI.)

4. **Open the app URL on your phone**, signed in to GitHub with the same account:

   ```
   https://<CODESPACE_NAME>-5173.app.github.dev
   ```

   Sign in with any email — dev auth, no Clerk.

5. **Click it**: new project → wizard → review → build → reveal. On the free path
   the wizard asks one field at a time (B065) and the build is a stand-in that
   says so at the reveal. It costs nothing.

Stop with `scripts/dev-down.sh`, and stop the Codespace itself when you are done
— an idle Codespace still bills against your included hours.

## What gets wired, and where it comes from

Nothing is hard-coded. `scripts/codespace-env.sh` derives everything from
`$CODESPACE_NAME` and `$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN`, `dev-up.sh`
sources it when it sees a Codespace, and every value goes through `${VAR:-…}` so
anything you set yourself wins.

| what | value in a Codespace | why it must change |
|---|---|---|
| `VITE_API_URL` | `https://<name>-3000.app.github.dev` | the React app calls the api **from the browser**, which is not on this machine |
| `CORS_ORIGINS` | `https://<name>-5173.app.github.dev` | the api's allow list is never a wildcard |
| `APP_ORIGIN` | the same | the marking bridge posts only to this origin (`design.service.ts`) |
| `SCIO_APP_HOST` | `0.0.0.0` | a port is forwarded only if something listens on every interface |
| `SCIO_PREVIEW_HOST` | `0.0.0.0` | so is a preview |
| `SCIO_PUBLIC_URL_TEMPLATE` | `https://<name>-{port}.app.github.dev` | previews get a **random** port, so the engine is given the shape rather than a URL |

Vite is the other half: it has refused an unknown `Host` header since 5.4.12, so
`apps/app/vite.config.ts` names `.app.github.dev` in `server.allowedHosts` and
points HMR's websocket at port 443. Without that the forwarded URL answers
*"Blocked request. This host is not allowed."*

## When dev-up.sh gives up on the api

Two things went wrong on the first real runs, both fixed, both worth knowing about
because they are what a fresh machine looks like.

**`No module named uvicorn`.** The venv existed and was empty — a directory is
created first and the packages land second, so an install that dies in between
leaves exactly that. `dev-up.sh` now checks by *importing*, not by looking for
the directory, and rebuilds when the import fails.

**`Cannot find module '@scio/shared'` (× 30).** The shared package is the API
contract, its `main`/`types` point at `dist/`, and `dist/` is gitignored — so a
fresh clone has none, and `pnpm install` does not build workspace packages.
`dev-up.sh` now builds it when it is missing or older than its sources.


The first `nest start` in a fresh Codespace compiles the whole api from scratch
on two cores, which takes several minutes — longer than the 120s the script used
to wait, so it announced a failure while the api was quietly still building.
The waits are now 420s for the api (120s engine, 180s app) and a timeout prints
the tail of the server's own log plus the knob to turn:

```bash
SCIO_WAIT_API=900 scripts/dev-up.sh
```

`dev-up.sh` is idempotent — if the api came up after the script stopped watching,
just run it again and it carries on to the app. Check first with
`curl -s localhost:3000/health`.

## The design window (Level 2)

The preview is a second server on a **random** port. Codespaces auto-forwards it
when it starts, and the engine publishes it as
`https://<name>-<that port>.app.github.dev` instead of `http://127.0.0.1:<port>`
— that is what `SCIO_PUBLIC_URL_TEMPLATE` is for. But the same privacy rule
applies: the design window embeds the preview in an iframe, so **that port has to
be public too**, or the frame shows GitHub's sign-in page. Find it in the
**Ports** panel after the build (it is the one that appeared) and set its
visibility to Public.

## Real builds (this one costs money)

The engine uses its stand-ins whenever no key is configured, which is the default
in a fresh Codespace. To run a real build:

```bash
printf 'ANTHROPIC_API_KEY=sk-ant-…\nSCIO_ONLY_PROVIDER=anthropic\nSCIO_MODEL=claude-sonnet-5\nSCIO_MODEL_PASSES=1\n' > apps/engine/.env
scripts/dev-down.sh && scripts/dev-up.sh
```

`apps/engine/.env` is gitignored and read at import (`config.py`); a variable
already in the environment always wins over it. Check
`curl -s localhost:8000/health` says `"providers":"real"` and `"builder":"model"`.
`SCIO_FAKE_PROVIDERS=1` forces the free path back on even when a key is present —
useful for clicking around without spending anything. See `RUNBOOK-FIRST-RUN.md`
for what a real run costs (the last one: 46 minutes, $2.69).

## What has been verified, and what has not

Verified here, by running the stack with `CODESPACE_NAME` set:

- the api returns `Access-Control-Allow-Origin` for the forwarded app origin and
  nothing for a stranger,
- Vite serves `200` for the forwarded `Host` and blocks an unknown one,
- the app's module graph resolves `VITE_API_URL` to the forwarded api URL,
- app and api both answer on the container's non-loopback address, so there is
  something for Codespaces to forward,
- the engine process carries `SCIO_PUBLIC_URL_TEMPLATE`, and the engine's own
  tests pin the loopback → forwarded translation.

**Not** verified from here: an actual Codespace boot. This sandbox cannot create
one, so the image build and the postCreate install run for the first time on your
machine. If the image fails, it will be in `.devcontainer/Dockerfile` (the PGDG
apt repo) or in `post-create.sh`; both are small and readable, and the error
appears in the Codespace's creation log.
