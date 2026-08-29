#!/usr/bin/env bash
# Controls for docs-only-write.sh — the gate protecting the most agents and, until
# now, the only one with no harness at all. Three agents depend on it:
# architect, rebuild-adjudicator, agent-fitness-review.
R="$(cd "$(dirname "$0")/../.." && pwd)"
G="$R/.claude/hooks/docs-only-write.sh"
NOPY="${NOPY:-/tmp/claude-0/-home-user-hello-world/166da4b5-1b2a-5916-b4ac-2e347fa567c1/scratchpad/nopy}"
pass=0; fail=0

decide () {
  local payload="$1"; shift
  printf '%s' "$payload" | env CLAUDE_PROJECT_DIR="$R" "$@" "$G" 2>/dev/null | python3 -c '
import sys, json
raw = sys.stdin.read().strip()
if not raw:
    print("allow")          # silence from PreToolUse means allow
else:
    try:
        print(json.loads(raw)["hookSpecificOutput"]["permissionDecision"])
    except Exception:
        print("UNPARSEABLE")'
}
chk () {
  local id="$1" expect="$2" payload="$3"; shift 3
  local got; got="$(decide "$payload" "$@")"
  if [ "$got" = "$expect" ]; then printf '  ok    %-5s %s\n' "$id" "$expect"; pass=$((pass+1))
  else printf '  FAIL  %-5s expected %s got %s\n' "$id" "$expect" "$got"; fail=$((fail+1)); fi
}
w () {
  python3 -c 'import json,sys; print(json.dumps({"tool_name": sys.argv[2], "tool_input": {sys.argv[3]: sys.argv[1]}}))' \
    "$1" "${2:-Write}" "${3:-file_path}"
}

echo "positive controls — without these it is a brick wall, not a gate"
chk A  allow "$(w 'docs/decisions/0099-example.md')"
chk B  allow "$(w "$R/docs/decisions/0099-example.md")"
chk C  allow "$(w 'docs/a/b/c/deep.md')"
chk D  allow "$(w 'docs/existing.md' Edit)"

echo "outside docs/"
chk E  deny "$(w 'apps/api/src/main.ts')"
chk F  deny "$(w '.claude/agents/architect.md')"
chk G  deny "$(w '.claude/hooks/docs-only-write.sh')"
chk H  deny "$(w '.claude/settings.json')"
chk I  deny "$(w 'CLAUDE.md')"
chk J  deny "$(w '/etc/passwd')"
chk K  deny "$(w 'docsfake/x.md')"
chk L  deny "$(w 'docs')"
chk M  deny "$(w '.git/hooks/pre-commit')"

echo "traversal and symlinks"
chk N  deny "$(w 'docs/../.claude/agents/architect.md')"
chk O  deny "$(w 'docs/../../etc/passwd')"
mkdir -p "$R/docs" && ln -sfn "$R/.claude" "$R/docs/symdir"
chk P  deny "$(w 'docs/symdir/agents/architect.md')"
rm -f "$R/docs/symdir"

echo "the release record — an agent must not write its own registry row"
chk RG deny "$(w 'docs/agent-registry.md')"

echo "malformed input"
chk Q  deny '{"tool_name":"Write","tool_input":{}}'
chk RR deny 'not json'
chk S  deny "$(w '')"
chk T  deny '{"tool_name":"Write","tool_input":{"file_path":42}}'
chk U  deny ''

echo "other tool shapes"
chk V  deny "$(w '.claude/hooks/n.ipynb' NotebookEdit notebook_path)"
chk WW allow "$(w 'docs/n.ipynb' NotebookEdit notebook_path)"

echo "the interpreter the adjudicator needs"
if [ -x "$NOPY/bash" ]; then
  chk PY deny "$(w 'apps/api/src/main.ts')" PATH="$NOPY"
  chk PZ deny "$(w 'docs/ok.md')"            PATH="$NOPY"
else
  printf '  SKIP  PY    no bash-without-python3 PATH staged at %s\n' "$NOPY"
fi

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
