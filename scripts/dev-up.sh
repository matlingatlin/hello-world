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

mkdir -p "$RUN"

say() { printf '\n\033[36m▸ %s\033[0m\n' "$*"; }
die() { printf '\n\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

wait_for() { # wait_for <name> <url> <seconds>
  local name=$1 url=$2 timeout=$3 waited=0
  while ! curl -fsS -o /dev/null "$url" 2>/dev/null; do
    sleep 1
    waited=$((waited + 1))
    [ "$waited" -ge "$timeout" ] && die "$name did not come up in ${timeout}s — see $RUN/$name.log"
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
  wait_for engine "http://127.0.0.1:$ENGINE_PORT/health" 60
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
    CORS_ORIGINS="http://127.0.0.1:$APP_PORT,http://localhost:$APP_PORT" \
    APP_ORIGIN="http://127.0.0.1:$APP_PORT" \
    ENGINE_URL="http://127.0.0.1:$ENGINE_PORT" \
    PORT="$API_PORT" \
    setsid npx nest start >"$RUN/api.log" 2>&1 & echo $! >"$RUN/api.pid")
  wait_for api "http://127.0.0.1:$API_PORT/health" 120
fi

# --------------------------------------------------------------------------
# 4. The app — dev auth, pointed at the local api
# --------------------------------------------------------------------------
say "App"
if curl -fsS -o /dev/null "http://127.0.0.1:$APP_PORT" 2>/dev/null; then
  printf '  already running on port %s\n' "$APP_PORT"
else
  (cd "$ROOT/apps/app" && VITE_DEV_AUTH=1 \
    VITE_API_URL="http://127.0.0.1:$API_PORT" \
    setsid npx vite --host 127.0.0.1 --port "$APP_PORT" --strictPort >"$RUN/app.log" 2>&1 & echo $! >"$RUN/app.pid")
  wait_for app "http://127.0.0.1:$APP_PORT" 90
fi

cat <<EOF

  Open  http://127.0.0.1:$APP_PORT
  Sign in with any email — dev auth, no Clerk. A different email is a different workspace.

  api      http://127.0.0.1:$API_PORT      (docs at /docs)
  engine   http://127.0.0.1:$ENGINE_PORT/health
  postgres 127.0.0.1:$PGPORT  db 'scio'  ($PGDATA)
  logs     $RUN/*.log

  Stop everything with scripts/dev-down.sh
EOF
