#!/usr/bin/env bash
#
# Every time the Codespace starts: make the forwarded URLs available to every
# shell, then say what to run. Nothing is started automatically — dev-up.sh is
# one command and starting a stack behind someone's back is how you end up
# debugging a server you did not know was running.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_LINE=". \"$ROOT/scripts/codespace-env.sh\""

# dev-up.sh sources this file itself; this is so an interactive shell agrees
# with it — `echo \$VITE_API_URL` should not depend on who started what.
if ! grep -qF "$SOURCE_LINE" "$HOME/.bashrc" 2>/dev/null; then
  {
    printf '\n# Scio — the forwarded URLs of this Codespace (derived, see the file)\n'
    printf '[ -n "${CODESPACE_NAME:-}" ] && %s\n' "$SOURCE_LINE"
  } >>"$HOME/.bashrc"
fi

# shellcheck source=../scripts/codespace-env.sh
[ -n "${CODESPACE_NAME:-}" ] && . "$ROOT/scripts/codespace-env.sh"

cat <<EOF

  Scio — start the whole stack (free, no key):

      scripts/dev-up.sh

  Then open the app on any device, signed in to GitHub:

      ${APP_PUBLIC_URL:-http://127.0.0.1:5173}

  The api is at ${API_PUBLIC_URL:-http://127.0.0.1:3000} and the browser calls it
  directly, so it has to be reachable too — make that port public once:

      gh codespace ports visibility ${SCIO_API_PORT:-3000}:public -c \$CODESPACE_NAME

  docs/RUNBOOK-CODESPACES.md has the rest.

EOF
