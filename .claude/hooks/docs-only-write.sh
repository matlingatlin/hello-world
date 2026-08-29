#!/usr/bin/env bash
# PreToolUse gate for planning subagents (architect, rebuild-brainstorm).
#
# Why this exists as a hook and not as a sentence in the agent prompt:
# a PreToolUse hook runs before every permission check, including
# bypassPermissions, and can only ever tighten. A sentence in the prompt is a
# convention; this is a wall.
#
# What it enforces: the agent may write ADRs, plans and design documents.
# It may not write source code, tests, configuration, or its own definition.
# The decision has to survive contact with an implementer who disagrees, which
# it cannot do if the architect can quietly implement it itself.
#
# Contract: stdin is the PreToolUse JSON payload. Exit 0 always; the decision
# is carried in the JSON on stdout. Silence (no output) means "no opinion".
set -uo pipefail

payload=$(cat)

path=$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") or ""
print(p)
' 2>/dev/null)

# No path in the payload: nothing for this gate to judge. Deny rather than
# wave through, because a Write we cannot resolve is a Write we cannot scope.
if [ -z "$path" ]; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"docs-only-write: no file path in the tool call, so its scope cannot be checked."}}'
  exit 0
fi

root="${CLAUDE_PROJECT_DIR:-$PWD}"
# Resolve without requiring the file to exist yet.
abs=$(python3 -c '
import os,sys
p, root = sys.argv[1], sys.argv[2]
if not os.path.isabs(p):
    p = os.path.join(root, p)
print(os.path.normpath(os.path.realpath(os.path.dirname(p)) + "/" + os.path.basename(p)))
' "$path" "$root" 2>/dev/null)
absroot=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$root" 2>/dev/null)

case "$abs" in
  # The release record. docs/ is otherwise this agent's whole world, and that is why
  # the registry needs naming here: it is the one document under docs/ that decides
  # whether an agent may be used, and an agent that can write its own row can write
  # itself `in use`. Found when the first agent built to the template did exactly
  # that — honestly, as it happens, but the mechanism allowed the other outcome.
  "$absroot"/docs/agent-registry.md)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"docs-only-write: the registry is the release record, and release is a human decision. Report what you produced; a human writes the row."}}'
    exit 0
    ;;
  "$absroot"/docs/*)
    exit 0
    ;;
  *)
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"docs-only-write: this agent writes only under docs/. This path is outside it. Produce the ADR, the decomposition or the review finding as a document; hand the change to an implementer."}}'
    exit 0
    ;;
esac
