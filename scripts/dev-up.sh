#!/usr/bin/env bash
#
# Bring the whole product up locally — engine + api + app + Postgres — with no
# external services at all.
#
# Why this exists: the engine was proven and tested, but nobody had ever clicked
# through the product, because opening it needed a Clerk account, two keys and a
# database somebody else hosted. This script removes all three:
#
#   Postgres   a real PostgreSQL 16 process (the binaries are installed; NOT Docker)
#   auth       SCIO_DEV_AUTH / VITE_DEV_AUTH — the bearer token is the identity
#   engine     its own fake providers, so a full build costs nothing
#
# Nothing here changes what ships. Production still means Clerk and a hosted
# database; dev mode is additive and behind flags, and the api refuses to run
# dev auth when NODE_ENV=production.
#
# Usage:
#   scripts/dev-up.sh          start everything (idempotent)
#   scripts/dev-down.sh        stop everything
#
# Optional, for a REAL build instead of the free fake one:
#   ANTHROPIC_API_KEY=… SCIO_MODEL=claude-sonnet-5 SCIO_MODEL_PASSES=1 scripts/dev-up.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$ROOT/.local"                       # pids, logs — gitignored
PGBIN="${PGBIN:-/usr/lib/postgresql/16/bin}"
# Outside the repo on purpose: PGDATA must be owned by the postgres user (it
# refuses to run as root), and it must never end up in a commit.
PGDATA="${SCIO_PGDATA:-/var/lib/postgresql/scio-dev}"
PGPORT="${SCIO_PGPORT:-55432}"
ENGINE_PORT="${SCIO_ENGINE_PORT:-8000}"
API_PORT="${SCIO_API_PORT:-3000}"
APP_PORT="${SCIO_APP_PORT:-5173}"

DATABASE_URL="postgresql://scio@127.0.0.1:$PGPORT/scio?schema=public"
export DATABASE_URL

# Where the BROWSER reaches things, which is not always where they run. Locally
# that is loopback and always has been; in a Codespace it is a forwarded https
# origin per port, derived from $CODESPACE_NAME. One file works that out, and
# everything below just reads the answer.
if [ -n "${CODESPACE_NAME:-}" ] && [ -f "$ROOT/scripts/codespace-env.sh" ]; then
  # shellcheck source=codespace-env.sh
  . "$ROOT/scripts/codespace-env.sh"
fi

APP_HOST="${SCIO_APP_HOST:-127.0.0.1}"
APP_URL="${APP_PUBLIC_URL:-http://127.0.0.1:$APP_PORT}"
API_URL="${VITE_API_URL:-http://127.0.0.1:$API_PORT}"
APP_ORIGIN="${APP_ORIGIN:-http://127.0.0.1:$APP_PORT}"
CORS_ORIGINS="${CORS_ORIGINS:-http://127.0.0.1:$APP_PORT,http://localhost:$APP_PORT}"

mkdir -p "$RUN"

say() { printf '\n\033[36m▸ %s\033[0m\n' "$*"; }
die() { printf '\n\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# How long to wait for each server. A timeout only bounds FAILURE — wait_for
# returns the moment the health check passes — so being generous costs a healthy
# start nothing. The old 120s for the api was measured in one sandbox and was
# wrong everywhere else: the first `nest start` compiles the whole project, and
# on a 2-core Codespace that takes longer than two minutes. Nothing was broken;
# the script just stopped watching.
ENGINE_TIMEOUT="${SCIO_WAIT_ENGINE:-120}"
API_TIMEOUT="${SCIO_WAIT_API:-420}"
APP_TIMEOUT="${SCIO_WAIT_APP:-180}"

wait_for() { # wait_for <name> <url> <seconds>
  local name=$1 url=$2 timeout=$3 waited=0
  while ! curl -fsS -o /dev/null "$url" 2>/dev/null; do
    sleep 1
    waited=$((waited + 1))
    if [ "$waited" -ge "$timeout" ]; then
      # A dead end is not a diagnosis: show what the server itself said.
      printf '\n\033[31m✗ %s did not come up in %ss\033[0m\n' "$name" "$timeout" >&2
      printf '  the last lines of %s:\n\n' "$RUN/$name.log" >&2
      tail -n 20 "$RUN/$name.log" 2>/dev/null | sed 's/^/  /' >&2
      printf '\n  Still building? Give it longer: SCIO_WAIT_%s=900 scripts/dev-up.sh\n' \
        "$(printf '%s' "$name" | tr '[:lower:]' '[:upper:]')" >&2
      exit 1
    fi
  done
  printf '  %s is up (%s)\n' "$name" "$url"
}

# --------------------------------------------------------------------------
# 1. PostgreSQL — a real server process, no Docker
# --------------------------------------------------------------------------
say "Postgres"

[ -x "$PGBIN/initdb" ] || die "no PostgreSQL binaries at $PGBIN — apt-get install postgresql-16"
# The one thing that is not in the base image. The api's first migration does
# CREATE EXTENSION "vector" (pgvector, for reference retrieval), and without it
# migration 0001 fails on its second line.
[ -f /usr/share/postgresql/16/extension/vector.control ] ||
  die "pgvector is missing — apt-get install -y postgresql-16-pgvector"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  printf '  initialising a new cluster at %s\n' "$PGDATA"
  mkdir -p "$PGDATA"
  chown postgres:postgres "$PGDATA"
  chmod 700 "$PGDATA"
  # trust auth on loopback only: this cluster exists for one sandbox and holds
  # nothing but dev data.
  su postgres -c "$PGBIN/initdb -D '$PGDATA' -U scio --auth=trust -E UTF8" >"$RUN/postgres-init.log" 2>&1
fi

if su postgres -c "$PGBIN/pg_isready -h 127.0.0.1 -p $PGPORT" >/dev/null 2>&1; then
  printf '  already running on port %s\n' "$PGPORT"
else
  su postgres -c "$PGBIN/pg_ctl -D '$PGDATA' -l '$PGDATA/server.log' -w -t 60 \
    -o '-p $PGPORT -k /tmp -c listen_addresses=127.0.0.1' start" >"$RUN/postgres.log" 2>&1 ||
    die "Postgres did not start — see $PGDATA/server.log"
  printf '  started on port %s\n' "$PGPORT"
fi

psql "postgresql://scio@127.0.0.1:$PGPORT/postgres" -tAc \
  "select 1 from pg_database where datname='scio'" | grep -q 1 ||
  psql "postgresql://scio@127.0.0.1:$PGPORT/postgres" -q -c "create database scio owner scio"

say "Migrations"
(cd "$ROOT/apps/api" && npx prisma migrate deploy) | sed 's/^/  /'

# --------------------------------------------------------------------------
# 1b. @scio/shared — the API contract both sides compile against
# --------------------------------------------------------------------------
# `main` and `types` point at dist/, and dist/ is gitignored. So a fresh clone
# has none, `pnpm install` does not build workspace packages, and the api dies
# with 30 x "Cannot find module '@scio/shared'" — which is what the first real
# Codespace run did. It only ever worked here because someone built it once.
say "Shared types"
SHARED_DIST="$ROOT/packages/shared/dist/index.js"
if [ ! -f "$SHARED_DIST" ] || [ -n "$(find "$ROOT/packages/shared/src" -newer "$SHARED_DIST" -print -quit 2>/dev/null)" ]; then
  printf '  building @scio/shared\n'
  (cd "$ROOT/packages/shared" && npx tsc -p tsconfig.json) || die "@scio/shared did not build"
  printf '  built\n'
else
  printf '  up to date\n'
fi

# --------------------------------------------------------------------------
# 1c. The engine's venv — present, and actually populated
# --------------------------------------------------------------------------
# A venv can exist and be empty: the directory is created first and the packages
# land second, so an install that dies in between leaves exactly that. The first
# Codespace got one, and the engine failed with "No module named uvicorn" — a
# message about a missing module, for a machine that had simply never finished
# setting up. Repaired here rather than trusted from postCreate, so a fresh
# clone anywhere is self-healing.
say "Engine deps"
VENV="$ROOT/apps/engine/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  printf '  creating the venv\n'
  python3 -m venv "$VENV" || die "python3 -m venv failed — is python3-venv installed?"
fi
if "$VENV/bin/python" -c "import uvicorn, fastapi" >/dev/null 2>&1; then
  printf '  present\n'
else
  printf '  installing scio-engine — a minute or two, once per machine\n'
  "$VENV/bin/pip" install --quiet --upgrade pip
  # db: the library's Postgres catalog. providers: the real model SDKs, so that
  # adding a key to apps/engine/.env is the only step a real build needs.
  "$VENV/bin/pip" install --quiet -e "$ROOT/apps/engine[dev,db,providers]" ||
    die "the engine's dependencies did not install — pip's error is above"
  printf '  installed\n'
fi

# --------------------------------------------------------------------------
# 2. The engine — fake providers unless a key is in the environment
# --------------------------------------------------------------------------
say "Engine"
if curl -fsS -o /dev/null "http://127.0.0.1:$ENGINE_PORT/health" 2>/dev/null; then
  printf '  already running on port %s\n' "$ENGINE_PORT"
else
  # setsid, not just nohup: each server gets its own session, so it survives the
  # shell that started it and dev-down can take its whole process tree down.
  # SCIO_CATALOG_DB: where the component library keeps what it learns from
  # builds (B061). The same database the api uses, but its own `library_*`
  # tables, created by the engine — Prisma owns the product's schema, the
  # engine owns the library's, and neither migrates the other's.
  (cd "$ROOT/apps/engine" && SCIO_CATALOG_DB="$DATABASE_URL" \
    setsid .venv/bin/python -m uvicorn scio_engine.main:app \
    --host 127.0.0.1 --port "$ENGINE_PORT" >"$RUN/engine.log" 2>&1 & echo $! >"$RUN/engine.pid")
  wait_for engine "http://127.0.0.1:$ENGINE_PORT/health" "$ENGINE_TIMEOUT"
fi
printf '  %s\n' "$(curl -fsS "http://127.0.0.1:$ENGINE_PORT/health")"

# --------------------------------------------------------------------------
# 3. The api — dev auth, local database, local engine
# --------------------------------------------------------------------------
say "API"
if curl -fsS -o /dev/null "http://127.0.0.1:$API_PORT/health" 2>/dev/null; then
  printf '  already running on port %s\n' "$API_PORT"
else
  (cd "$ROOT/apps/api" && SCIO_DEV_AUTH=1 \
    DATABASE_URL="$DATABASE_URL" \
    CORS_ORIGINS="$CORS_ORIGINS" \
    APP_ORIGIN="$APP_ORIGIN" \
    ENGINE_URL="http://127.0.0.1:$ENGINE_PORT" \
    PORT="$API_PORT" \
    setsid npx nest start >"$RUN/api.log" 2>&1 & echo $! >"$RUN/api.pid")
  wait_for api "http://127.0.0.1:$API_PORT/health" "$API_TIMEOUT"
fi

# --------------------------------------------------------------------------
# 4. The app — dev auth, pointed at the local api
# --------------------------------------------------------------------------
say "App"
if curl -fsS -o /dev/null "http://127.0.0.1:$APP_PORT" 2>/dev/null; then
  printf '  already running on port %s\n' "$APP_PORT"
else
  (cd "$ROOT/apps/app" && VITE_DEV_AUTH=1 \
    VITE_API_URL="$API_URL" \
    setsid npx vite --host "$APP_HOST" --port "$APP_PORT" --strictPort >"$RUN/app.log" 2>&1 & echo $! >"$RUN/app.pid")
  wait_for app "http://127.0.0.1:$APP_PORT" "$APP_TIMEOUT"
fi

cat <<EOF

  Open  $APP_URL
  Sign in with any email — dev auth, no Clerk. A different email is a different workspace.

  api      $API_URL      (docs at /docs)
  engine   http://127.0.0.1:$ENGINE_PORT/health
  postgres 127.0.0.1:$PGPORT  db 'scio'  ($PGDATA)
  logs     $RUN/*.log

  Stop everything with scripts/dev-down.sh
EOF

if [ -n "${CODESPACE_NAME:-}" ]; then
  cat <<EOF
  A forwarded port is PRIVATE by default, and a private port answers a browser
  fetch with GitHub's sign-in page — which the app reads as the api being down.
  Make the api port public once per Codespace:

    gh codespace ports visibility $API_PORT:public -c \$CODESPACE_NAME

  See docs/RUNBOOK-CODESPACES.md.

EOF
fi
