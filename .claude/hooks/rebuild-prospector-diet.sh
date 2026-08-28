#!/usr/bin/env bash
# PreToolUse diet gate for the `rebuild-prospector` subagent.
#
# The prospector proposes what a product in this problem space could be. It must
# do that WITHOUT the existing system's solution vocabulary, because a generator
# seeded with the existing solution measures worse than one given nothing.
#
# A sentence asking it not to look is the single most thoroughly measured
# non-intervention available. This is a wall: PreToolUse runs before every
# permission check, bypassPermissions included, and can only tighten.
#
# The prospector holds no Bash, no Agent, no Grep and no Glob, so Read and Write
# are the whole of its filesystem surface and this gate is complete over it.
#
# Contract: stdin is the PreToolUse payload. Always exit 0; the decision travels
# in JSON on stdout. Deny — never silently allow — when the payload cannot be
# parsed or carries no path: a call whose scope cannot be checked must not run.
set -uo pipefail

payload=$(cat)
root="${CLAUDE_PROJECT_DIR:-$PWD}"

deny() {
  # shell-quote nothing into the JSON; the reason strings below are all literal.
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"rebuild-prospector-diet: $1\"}}"
  exit 0
}

parsed=$(printf '%s' "$payload" | python3 -c '
import json, os, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("__MALFORMED__\t"); sys.exit(0)
tool = d.get("tool_name") or ""
ti = d.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") or ""
if not isinstance(p, str) or not p:
    print("__NOPATH__\t" + tool); sys.exit(0)
root = os.path.realpath(sys.argv[1])
if not os.path.isabs(p):
    p = os.path.join(root, p)
# realpath resolves the basename too: a symlink named brief.md must not become
# a read of docs/next/LAYER-E-BUILD.md.
p = os.path.realpath(p)
if p != root and not p.startswith(root + os.sep):
    print("__OUTSIDE__\t" + tool); sys.exit(0)
print(os.path.relpath(p, root) + "\t" + tool)
' "$root" 2>/dev/null) || deny "could not resolve the target path."

rel=${parsed%%$'\t'*}
tool=${parsed#*$'\t'}

case "$rel" in
  __MALFORMED__) deny "the tool payload could not be parsed, so its scope cannot be checked." ;;
  __NOPATH__)    deny "no file path in the tool call, so its scope cannot be checked." ;;
  __OUTSIDE__)   deny "that path is outside this repository. The prospector reads its brief and nothing else; the sibling repository at /home/user/scio is exactly what it must not see." ;;
  "")            deny "empty path." ;;
esac

case "$tool" in
  Read)
    case "$rel" in
      docs/rebuild/brief/*.md)
        exit 0 ;;
      .claude/skills/architecture-decision/references/far-domain-analogy.md)
        exit 0 ;;
    esac
    deny "the prospector reads only docs/rebuild/brief/*.md and the far-domain analogy reference. It proposes from the problem, not from the existing solution — read anything else and it stops being a generator." ;;
  Write)
    case "$rel" in
      docs/rebuild/candidates/*)
        exit 0 ;;
    esac
    deny "the prospector writes only under docs/rebuild/candidates/. Its output is raw material for an adjudicator that has not seen it." ;;
esac

deny "unexpected tool \`$tool\` for this gate."
