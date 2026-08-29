#!/usr/bin/env bash
# Controls for agent-builder-scope.sh — the wall binding agent-builder.
#
# These cases existed only as PROSE in .claude/skills/agent-assembly/evals.md: a table
# of results nobody could re-run. A P5 absence audit counted four of seven hooks with
# no re-runnable harness, and this was one of them. A recorded pass is not a test; it is
# a claim about a test, and it goes stale the first time the script changes.
R="$(cd "$(dirname "$0")/../.." && pwd)"
G="$R/.claude/hooks/agent-builder-scope.sh"
NOPY="${NOPY:-/tmp/claude-0/-home-user-hello-world/166da4b5-1b2a-5916-b4ac-2e347fa567c1/scratchpad/nopy}"
pass=0; fail=0

# Silence from a PreToolUse hook means ALLOW — that is the contract in the script's own
# header. So an empty stdout is a pass-through, not a crash, and must be scored as allow.
decide () {
  local payload="$1"; shift
  printf '%s' "$payload" | env CLAUDE_PROJECT_DIR="$R" "$@" "$G" 2>/dev/null | python3 -c '
import sys, json
raw = sys.stdin.read().strip()
if not raw:
    print("allow")
else:
    try:
        print(json.loads(raw)["hookSpecificOutput"]["permissionDecision"])
    except Exception:
        print("UNPARSEABLE")'
}

chk () {
  local id="$1" expect="$2" payload="$3"; shift 3
  local got; got="$(decide "$payload" "$@")"
  if [ "$got" = "$expect" ]; then
    printf '  ok    %-5s %s\n' "$id" "$expect"; pass=$((pass+1))
  else
    printf '  FAIL  %-5s expected %s got %s\n' "$id" "$expect" "$got"; fail=$((fail+1))
  fi
}

# w <path> [tool] [key]
w () {
  python3 -c 'import json,sys; print(json.dumps({"tool_name": sys.argv[2], "tool_input": {sys.argv[3]: sys.argv[1]}}))' \
    "$1" "${2:-Write}" "${3:-file_path}"
}

echo "positive controls — without these it is a brick wall, not a gate"
chk A  allow "$(w 'docs/note.md')"
chk B  allow "$(w "$R/docs/note.md")"
chk C  allow "$(w '.claude/agents/brand-new-agent.md')"
chk D  allow "$(w '.claude/skills/brand-new-skill/SKILL.md')"

echo "outside the three roots"
chk E  deny "$(w 'apps/api/src/main.ts')"
chk G  deny "$(w 'docsfake/x.md')"
chk H  deny "$(w '/etc/passwd')"
chk W  deny "$(w '.claude/skillsfake/SKILL.md')"
chk Z  deny "$(w '.mcp.json')"
chk AD deny "$(w 'CLAUDE.md')"
chk AE deny "$(w '.git/hooks/pre-commit')"
chk AA deny "$(w "$HOME/.claude/hooks/x.sh")"

echo "walls, settings, and its own toolchain"
chk F  deny "$(w 'docs/../.claude/hooks/x.sh')"
chk J  deny "$(w '.claude/hooks/agent-builder-scope.sh')"
chk M  deny "$(w '.claude/settings.local.json')"
chk I  deny "$(w '.claude/agents/agent-builder.md')"
chk N  deny "$(w '.claude/skills/agent-shape/SKILL.md')"
chk N2 deny "$(w '.claude/skills/agent-assembly/references/tiers.md')"

echo "create-only — the rule that closed three escapes an independent tester found"
chk O  deny "$(w '.claude/agents/architect.md' Edit)"
chk O2 deny "$(w '.claude/agents/architect.md')"
chk O3 deny "$(w '.claude/skills/system-decomposition/SKILL.md')"

echo "malformed input — a call whose scope cannot be checked must not proceed"
chk K  deny '{"tool_name":"Write","tool_input":{}}'
chk L  deny 'not json'
chk V  deny "$(w '')"
chk T  deny '{"tool_name":"Write","tool_input":{"file_path":42}}'
chk EM deny ''

echo "other tool shapes"
chk X  deny "$(w '.claude/hooks/n.ipynb' NotebookEdit notebook_path)"

echo "symlinked directory, and the interpreter the adjudicator needs"
mkdir -p "$R/docs" && ln -sfn "$R/.claude/hooks" "$R/docs/symdir"
chk RS deny "$(w 'docs/symdir/x.sh')"
rm -f "$R/docs/symdir"
if [ -x "$NOPY/bash" ]; then
  chk PY deny "$(w 'apps/api/src/main.ts')" PATH="$NOPY"
else
  printf '  SKIP  PY    no bash-without-python3 PATH staged at %s\n' "$NOPY"
fi

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
