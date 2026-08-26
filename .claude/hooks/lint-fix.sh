#!/usr/bin/env bash
#
# Apply the safe lint fixes to the file that was just edited.
#
# Runs on PostToolUse for Edit|Write. Claude Code passes the tool call as JSON on
# stdin; the path we want is `tool_input.file_path`.
#
# Three rules this follows deliberately:
#
#   It never fails the edit. A linter that is missing, or that chokes on a file
#   mid-write, must not turn a good edit into a red turn — so every path exits 0
#   and says nothing on success. This is a convenience; the edit is the work.
#
#   It touches one file, not the tree.
#
#   It does NOT reformat, and that is the whole reason this is called lint-fix
#   and not format. Measured on 2026-08-26: 59 of the engine's 125 Python files
#   and 48 TypeScript files disagree with `ruff format` / `prettier` as the repo
#   stands. Formatting on edit would rewrite an untouched file every time
#   somebody changed one line in it, and bury the real diff in noise. Formatting
#   this repo is a decision and a commit of its own, never a side effect of a
#   hook. `ruff check --fix` is different: it removes an unused import or an
#   unsorted one, which is a fix, not a restyle — and the repo already conforms.
#
# TypeScript gets nothing here on purpose: there is no eslint config in this
# repo (`pnpm -r lint` is `tsc --noEmit`), so there are no safe autofixes to
# apply. When an eslint config lands, add it here.
set -uo pipefail

payload="$(cat)"

file="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(data.get("tool_input", {}).get("file_path", ""))
' 2>/dev/null)"

[ -n "$file" ] || exit 0
[ -f "$file" ] || exit 0

root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

case "$file" in
  *.py)
    # The engine's own venv, not whatever ruff happens to be on PATH — a
    # different version fixes differently and the diff churns.
    ruff="$root/apps/engine/.venv/bin/ruff"
    [ -x "$ruff" ] || ruff="$(command -v ruff 2>/dev/null)"
    [ -n "$ruff" ] && [ -x "$ruff" ] || exit 0
    "$ruff" check --fix "$file" >/dev/null 2>&1
    ;;
esac

exit 0
