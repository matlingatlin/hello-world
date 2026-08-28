#!/usr/bin/env bash
# PreToolUse gate for the migration-reviewer agent.
#
# The agent's remit is "review, never edit". A sentence in the agent file does not
# enforce that (CLAUDE.md: a "must never" is a hook or an absent tool). This is the
# hook half. The other half is the absence of Bash from the agent's `tools:` — with
# Bash present, this gate is decorative, because `bash -c 'cat > file'` is a write.
#
# Allows: writes under docs/reviews/ only.
# Denies: everything else, and migration/schema paths explicitly, with a reason.
#
# Contract: PreToolUse hook. Reads the tool call as JSON on stdin. Exit 0 = allow,
# exit 2 = block and return stderr to the model. Verify the field names and the
# blocking exit code against the current Claude Code hooks documentation before
# installing — this is a proposal, not an installed hook.
set -uo pipefail

payload="$(cat)"

path="$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("")
    sys.exit(0)
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("path") or "")
')"

# No path in the payload: nothing to gate on. Fail closed on write-shaped tools.
if [ -z "$path" ]; then
  echo "migration-reviewer: write blocked — no file path in the tool call to check." >&2
  exit 2
fi

# Canonicalize before matching. A substring match on "*/docs/reviews/*" accepts
# docs/reviews/../../apps/api/prisma/migrations/0013/migration.sql — verified: it
# returned exit 0 in testing. Resolve the path, then prefix-match the resolved form.
root="${CLAUDE_PROJECT_DIR:-$PWD}"
case "$path" in /*) abs="$path" ;; *) abs="$root/$path" ;; esac
resolved="$(realpath -m "$abs" 2>/dev/null || printf '%s' "$abs")"
allowed="$(realpath -m "$root/docs/reviews" 2>/dev/null || printf '%s' "$root/docs/reviews")"

case "$resolved" in
  "$allowed"/*)
    exit 0
    ;;
  *prisma/migrations/*|*schema.prisma)
    echo "migration-reviewer: refusing to modify $path. This agent reviews migrations and \
does not edit them. Put the corrected SQL in the report's Change field; the author applies it." >&2
    exit 2
    ;;
  *)
    echo "migration-reviewer: refusing to write $path. This agent may write only its review \
under docs/reviews/." >&2
    exit 2
    ;;
esac
