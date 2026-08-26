#!/usr/bin/env bash
#
# Once per Codespace: the slow, one-time setup, done up front so the first
# `scripts/dev-up.sh` is quick.
#
# Nothing here is REQUIRED. dev-up.sh builds @scio/shared and repairs the
# engine's venv itself, because both have to work on any fresh clone, not only
# on a machine where this script happened to succeed. So a step that fails here
# is reported and the rest still runs — a half-finished setup that says nothing
# is what produced "No module named uvicorn" on a Codespace whose venv had been
# created and never filled.
#
# It does not touch the database: dev-up.sh owns the cluster and the migrations,
# and one code path for that is better than two that can drift.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

failed=()
step() { # step <name> <command...>
  printf '\n▸ %s\n' "$1"
  shift
  if "$@"; then return 0; fi
  printf '  ✗ failed — scripts/dev-up.sh will try again\n' >&2
  failed+=("$1")
}

step "pnpm" bash -c '
  corepack enable &&
  corepack prepare "$(node -p "require(\"./package.json\").packageManager")" --activate &&
  pnpm install --frozen-lockfile'

step "shared types" bash -c 'cd packages/shared && npx tsc -p tsconfig.json'

step "engine venv" bash -c '
  python3 -m venv apps/engine/.venv &&
  apps/engine/.venv/bin/pip install --upgrade pip &&
  apps/engine/.venv/bin/pip install -r apps/engine/requirements.lock &&
  apps/engine/.venv/bin/pip install --no-deps -e "./apps/engine" &&
  apps/engine/.venv/bin/python -c "import uvicorn, fastapi"'

# The browser Playwright drives. Its own step because it is the big download and
# the one most likely to fail — and a failure here costs the preview its senses,
# not the build: the loop records "nobody looked" and carries on.
step "chromium for the preview" bash -c '
  apps/engine/.venv/bin/playwright install --with-deps chromium'

step "prisma client" bash -c 'cd apps/api && npx prisma generate'

# The language servers behind the typescript-lsp and pyright-lsp plugins
# declared in .claude/settings.json. The plugins do NOT install these; without
# them on PATH the plugins load and report "Executable not found", which is
# config that silently does nothing.
step "language servers" bash -c '
  npm install -g typescript-language-server typescript pyright &&
  command -v typescript-language-server && command -v pyright-langserver' 

printf '\n'
if [ ${#failed[@]} -eq 0 ]; then
  printf '▸ ready — run scripts/dev-up.sh\n'
else
  printf '▸ these did not finish: %s\n' "${failed[*]}"
  printf '  Run scripts/dev-up.sh anyway — it repairs both of the ones that matter\n'
  printf '  and prints the real error if it cannot.\n'
fi
