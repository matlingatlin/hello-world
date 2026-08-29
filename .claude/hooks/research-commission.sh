#!/usr/bin/env bash
# research-commission.sh — PreToolUse on Write|Edit|NotebookEdit for domain-researcher.
#
# Allows exactly one shape of write:
#     $ROOT/docs/research/drafts/<id>.md   when $ROOT/docs/research/commissions/<id>.md exists
# Everything else is denied, including the commissions directory itself: an agent
# that writes its own commission has no scope.
#
# Contract: stdin is the PreToolUse JSON payload. Exit 0 always; the decision is
# carried in JSON on stdout. A call whose scope cannot be checked is denied.
set -uo pipefail

deny() {
  python3 -c '
import json,sys
print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse",
  "permissionDecision":"deny","permissionDecisionReason":sys.argv[1]}}))' "$1"
  exit 0
}
allow() {
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
}

payload=$(cat)
command -v python3 >/dev/null 2>&1 || { printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"research-commission: python3 unavailable; payload cannot be inspected."}}'; exit 0; }

path=$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("notebook_path") or "")
' 2>/dev/null)

[ -n "$path" ] || deny "research-commission: no file path in the tool call, so its scope cannot be checked. Malformed or unparseable payloads are denied."

root="${CLAUDE_PROJECT_DIR:-$PWD}"
# Resolve symlinks and .. without requiring the target to exist yet.
abs=$(python3 -c '
import os,sys
p, root = sys.argv[1], sys.argv[2]
if not os.path.isabs(p):
    p = os.path.join(root, p)
print(os.path.normpath(os.path.realpath(os.path.dirname(p)) + "/" + os.path.basename(p)))
' "$path" "$root" 2>/dev/null)
absroot=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$root" 2>/dev/null)

[ -n "$abs" ] && [ -n "$absroot" ] || deny "research-commission: path could not be resolved."

drafts="$absroot/docs/research/drafts"
case "$abs" in
  "$drafts"/*) ;;
  *) deny "research-commission: domain-researcher writes only to docs/research/drafts/<id>.md, where <id> is a commission that exists. This path is outside it. If you need a commission, ask for one; an agent that writes its own commission has no scope." ;;
esac

rel="${abs#"$drafts"/}"
case "$rel" in
  */*) deny "research-commission: drafts are flat files directly under docs/research/drafts/, not in subdirectories." ;;
esac

id="${rel%.md}"
[ "$id.md" = "$rel" ] || deny "research-commission: a draft must be a .md file."
case "$id" in
  ''|*[!a-z0-9-]*) deny "research-commission: the id must be lower-case letters, digits and hyphens — it is also the name of the verdict document and the note." ;;
esac

[ -f "$absroot/docs/research/commissions/$id.md" ] || deny "research-commission: no commission at docs/research/commissions/$id.md. Research is scoped by a candidate sentence written by whoever wants it (docs/decomposition-agent-pipeline.md, section 5). A sweep nobody commissioned has nowhere to land."

allow
