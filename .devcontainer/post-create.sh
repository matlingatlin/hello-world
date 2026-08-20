#!/usr/bin/env bash
#
# Once per Codespace: everything scripts/dev-up.sh assumes is already there.
#
# It does NOT start anything and does not touch the database — dev-up.sh owns
# the cluster (initdb, pg_ctl, `prisma migrate deploy`) and is idempotent, so
# migrations are applied by the same code path here as on a laptop rather than
# by a second one that could drift.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "▸ pnpm"
corepack enable
corepack prepare "$(node -p "require('./package.json').packageManager")" --activate
pnpm install --frozen-lockfile

echo "▸ engine venv"
python3 -m venv apps/engine/.venv
apps/engine/.venv/bin/pip install --quiet --upgrade pip
# db: the library's Postgres catalog. providers: the real model SDKs, so that
# adding a key to apps/engine/.env is the only step a real build needs.
apps/engine/.venv/bin/pip install --quiet -e "./apps/engine[dev,db,providers]"

echo "▸ prisma client"
(cd apps/api && npx prisma generate >/dev/null)

echo "▸ ready — run scripts/dev-up.sh"
