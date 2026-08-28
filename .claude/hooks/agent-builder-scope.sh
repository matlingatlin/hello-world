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

# --- privilege keys ---------------------------------------------------------
# The real risk is not modification, it is PRIVILEGE. An agent that can write a
# `hooks:` block into a .claude/ file can attach or remove a wall; one that can
# write `tools:` can widen a surface. Those lines are a human decision, so the
# builder designs them in a proposal and a human installs them. Everything else
# in those files -- bodies, descriptions, references, procedures -- it may write
# and revise freely, which is what repairing an existing agent actually needs.
priv=$(printf '%s' "$payload" | python3 -c '
import json,re,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
ti=d.get("tool_input") or {}
body="\n".join(str(ti.get(k,"")) for k in ("content","new_string","new_source"))
keys=("hooks","tools","allowed-tools","disallowed-tools","disallowedTools","permissionMode","model")
for line in body.split("\n"):
    m=re.match(r"^\s*([A-Za-z-]+)\s*:", line)
    if m and m.group(1) in keys:
        print(m.group(1)); break
' 2>/dev/null)

rel=$(printf '%s' "$payload" | python3 -c '
import json,os,sys
try: d=json.load(sys.stdin)
except Exception: print("__NOPATH__"); sys.exit(0)
ti=d.get("tool_input") or {}
p=ti.get("file_path") or ti.get("notebook_path") or ""
if not p: print("__NOPATH__"); sys.exit(0)
root=os.path.realpath(sys.argv[1])
if not os.path.isabs(p): p=os.path.join(root,p)
p=os.path.normpath(os.path.realpath(os.path.dirname(p))+"/"+os.path.basename(p))
print(os.path.relpath(p,root) if (p==root or p.startswith(root+os.sep)) else "__OUTSIDE__")
' "$root" 2>/dev/null) || deny "could not resolve the target path."

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
    # Privilege keys only mean anything where frontmatter is parsed: an agent
    # definition, or a SKILL.md. A reference file that DESCRIBES `hooks:` in
    # prose is documentation, and blocking it would stop the builder writing
    # about the very mechanism it must reason with.
    fm_file=no
    case "$rel" in
      .claude/agents/*.md) fm_file=yes ;;
      .claude/skills/*/SKILL.md) fm_file=yes ;;
    esac
    if [ "$fm_file" = yes ] && [ -n "$priv" ]; then
      deny "\`$priv:\` is a privilege line -- it decides what an agent may do or which wall is attached. Put it in a proposal under docs/ for a human to install; write the rest of the file freely."
    fi
    exit 0 ;;
esac

deny "agent-builder writes only under docs/, .claude/agents/ and .claude/skills/."
