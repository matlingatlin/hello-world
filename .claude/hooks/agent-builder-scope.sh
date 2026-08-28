#!/usr/bin/env bash
# PreToolUse gate for the `agent-builder` subagent.
#
# It may author agents, skills and documents. It may NOT author the things that
# would let it widen its own remit:
#
#   - .claude/hooks/**        a builder that writes executable hooks can delete
#                             this file and remove its own wall
#   - .claude/settings*.json  permissions and enabled plugins
#   - its own toolchain       self-modification. Changes to agent-builder go
#                             through a human, not through agent-builder.
#
# Hooks it designs are emitted as proposals under docs/ for a human to install.
#
# Contract: stdin is the PreToolUse payload. Always exit 0; the decision travels
# in the JSON on stdout. Silence means "no opinion".
set -uo pipefail

payload=$(cat)
root="${CLAUDE_PROJECT_DIR:-$PWD}"

deny() {
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"agent-builder-scope: $1\"}}"
  exit 0
}

rel=$(printf '%s' "$payload" | python3 -c '
import json,os,sys
try: d=json.load(sys.stdin)
except Exception: print("__NOPATH__"); sys.exit(0)
ti=d.get("tool_input") or {}
p=ti.get("file_path") or ti.get("notebook_path") or ""
if not p: print("__NOPATH__"); sys.exit(0)
root=os.path.realpath(sys.argv[1])
if not os.path.isabs(p): p=os.path.join(root,p)
p=os.path.realpath(p)   # resolves the basename too: a symlink named
                        # notes.txt must not become a write to architect.md
print((os.path.relpath(p,root)+"\t"+p) if (p==root or p.startswith(root+os.sep)) else "__OUTSIDE__")
' "$root" 2>/dev/null) || deny "could not resolve the target path."

abs="${rel#*	}"; rel="${rel%%	*}"

case "$rel" in
  __NOPATH__) deny "no file path in the tool call, so its scope cannot be checked." ;;
  __OUTSIDE__|"") deny "the path resolves outside this repository." ;;
esac

# --- denied even inside the allowed roots -----------------------------------
case "$rel" in
  .claude/hooks/*)
    deny "hooks are walls. Write the hook as a proposal under docs/ and let a human install it." ;;
  .claude/settings.json|.claude/settings.local.json|.claude/settings*.json)
    deny "settings carry permissions and enabled plugins. Propose the change under docs/." ;;
  .claude/agents/agent-builder.md|.claude/skills/agent-shape/*|.claude/skills/agent-baseline/*|.claude/skills/agent-assembly/*|.claude/skills/_shared/*)
    deny "this is agent-builder's own toolchain. It does not modify itself; propose the change under docs/." ;;
esac

# --- allowed roots -----------------------------------------------------------
case "$rel" in
  docs/*) exit 0 ;;
  .claude/agents/*|.claude/skills/*)
    # CREATE ONLY. agent-builder makes new agents; it does not edit existing
    # ones. That single rule closes, structurally, what content inspection could
    # not: it cannot delete a neighbour's `hooks:` wall, cannot widen a
    # neighbour's `tools:`, cannot rename a key across two innocent-looking
    # edits, because it never touches a file that is already there. A change to
    # an existing agent is a proposal under docs/ and a human applies it.
    if [ -e "$abs" ]; then
      deny "\`$rel\` already exists. You create agents; you do not edit them. Write the change as a proposal under docs/ and let a human apply it."
    fi
    exit 0 ;;
esac

deny "agent-builder writes only under docs/, .claude/agents/ and .claude/skills/."
