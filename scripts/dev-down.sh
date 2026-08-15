#!/usr/bin/env bash
#
# Stop what dev-up.sh started. Safe to run twice, and safe to run when only
# some of it is up.
#
# The database is stopped, not deleted: the point of a local run is that your
# projects are still there tomorrow. Pass --wipe to start from empty.
#
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$ROOT/.local"
PGBIN="${PGBIN:-/usr/lib/postgresql/16/bin}"
PGDATA="${SCIO_PGDATA:-/var/lib/postgresql/scio-dev}"

# Matched on the command line, not on a recorded pid. `setsid` puts each server
# in its own session and does not necessarily keep the pid the shell saw, so a
# pid file quietly stops matching — which is how a "restarted" engine went on
# serving the previous build's code for half an hour.
stop() { # stop <name> <pattern>
  local name=$1 pattern=$2 pids
  pids="$(pgrep -f "$pattern" || true)"
  [ -n "$pids" ] || return 0
  # shellcheck disable=SC2086
  kill -TERM $pids 2>/dev/null
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    pgrep -f "$pattern" >/dev/null || break
    sleep 1
  done
  # shellcheck disable=SC2086
  pgrep -f "$pattern" >/dev/null && kill -KILL $(pgrep -f "$pattern") 2>/dev/null
  printf '  stopped %s\n' "$name"
}

# Each of these forks: `nest start` compiles and then runs `dist/main` as a
# CHILD, and killing only the parent leaves the child holding port 3000 — which
# looks exactly like "already running" to dev-up.sh, so the next start silently
# keeps serving the previous build's code.
stop app "vite.*--port|vite\.js"
stop api "nest.*start|apps/api/dist/main"
stop engine "uvicorn scio_engine.main"
# The dev servers the ENGINE started to preview generated apps. One per build,
# and nothing else ever reaps them — three were still running after an hour.
stop "build sandboxes" "engine/out/projects/.*next"
rm -f "$RUN"/*.pid

if [ -s "$PGDATA/PG_VERSION" ]; then
  su postgres -c "$PGBIN/pg_ctl -D '$PGDATA' -m fast stop" >/dev/null 2>&1 &&
    printf '  stopped postgres\n'
fi

if [ "${1:-}" = "--wipe" ]; then
  rm -rf "$PGDATA"
  printf '  wiped %s — the next dev-up.sh starts from an empty database\n' "$PGDATA"
fi
