#!/usr/bin/env bash
# PreToolUse gate for the architect-rebuild agent.
# Allows Write only to new files under <repo>/docs/. Denies everything else,
# including any path that cannot be parsed or resolved. Always exits 0 and
# carries its decision in JSON on stdout.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"

payload="$(cat)"

# python3 is the whole adjudicator below. Without it the script would die on line 1
# of the heredoc with no stdout, and a PreToolUse hook that emits nothing is not a
# denial — the write proceeds. Fail closed, in shell, before that can happen.
command -v python3 >/dev/null 2>&1 || {
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"architect-rebuild-write-gate: python3 unavailable; the payload cannot be inspected, so its scope cannot be checked."}}'
  exit 0
}

PROJECT_DIR="$PROJECT_DIR" payload="$payload" python3 - <<'PY'
import json, os, sys

def out(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)

project = os.environ.get("PROJECT_DIR") or ""
if not project:
    out("deny", "CLAUDE_PROJECT_DIR is not set; scope cannot be established.")

# The repo root and the single allowed root, both fully resolved.
try:
    root = os.path.realpath(project)
    allowed = os.path.realpath(os.path.join(root, "docs"))
except OSError as e:
    out("deny", f"could not resolve project root: {e}")

raw = os.environ.get("payload") or ""
try:
    ev = json.loads(raw)
except Exception:
    out("deny", "unparseable hook payload; a call whose scope cannot be checked must not proceed.")

if not isinstance(ev, dict):
    out("deny", "hook payload is not an object.")

tool = ev.get("tool_name")
if tool != "Write":
    # Matcher should prevent this. If the matcher is ever widened, fail closed.
    out("deny", f"this gate only adjudicates Write; refusing {tool!r}.")

ti = ev.get("tool_input")
if not isinstance(ti, dict):
    out("deny", "tool_input missing or not an object.")

path = ti.get("file_path")
if not isinstance(path, str) or path.strip() == "":
    out("deny", "no file_path in the payload.")

# Resolve WITHOUT requiring existence. realpath() on a non-existent leaf
# still resolves every existing component, which is what defeats traversal
# and symlinked parents alike.
if not os.path.isabs(path):
    path = os.path.join(root, path)
try:
    target = os.path.realpath(path)
except OSError as e:
    out("deny", f"could not resolve target path: {e}")

# Prefix-lookalike guard: os.sep terminated comparison, plus the root itself.
if target != allowed and not target.startswith(allowed + os.sep):
    out("deny", f"outside the only writable root ({allowed}): {target}")

if target == allowed:
    out("deny", "refusing to write over the docs directory itself.")

# Create-only. lexists, not exists: a dangling symlink is still an existing name.
if os.path.lexists(target):
    out("deny",
        "that file already exists. This agent creates; it does not edit. "
        "Supersede it under a new number, or hand the change to a human.")

out("allow", f"new file under {allowed}")
PY
