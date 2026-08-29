#!/usr/bin/env bash
# Controls for architect-rebuild-write-gate.sh. Run from the repo root.
# Cases 1-3 are positive: without them, a deny-everything script scores 19/22.
R="$(cd "$(dirname "$0")/../.." && pwd)"
GATE="$R/.claude/hooks/architect-rebuild-write-gate.sh"
pass=0; fail=0

chk () {  # chk <n> <expected> <stdin-payload> [env-override]
  local n="$1" expect="$2" payload="$3" noproj="${4:-}"
  local got
  if [ -n "$noproj" ]; then
    got="$(printf '%s' "$payload" | env -u CLAUDE_PROJECT_DIR "$GATE" 2>/dev/null)"
  else
    got="$(printf '%s' "$payload" | CLAUDE_PROJECT_DIR="$R" "$GATE" 2>/dev/null)"
  fi
  local dec
  dec="$(printf '%s' "$got" | python3 -c 'import sys,json
try: print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])
except Exception: print("UNPARSEABLE")' 2>/dev/null)"
  if [ "$dec" = "$expect" ]; then
    printf '  ok    %-3s %s\n' "$n" "$expect"; pass=$((pass+1))
  else
    printf '  FAIL  %-3s expected %s got %s\n' "$n" "$expect" "$dec"; fail=$((fail+1))
  fi
}

w () { printf '{"tool_name":"Write","tool_input":{"file_path":%s}}' "$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$1")"; }

echo "positive controls — proof this is a gate, not a wall"
chk 1  allow "$(w 'docs/decisions/0022-example.md')"
chk 2  allow "$(w "$R/docs/decisions/0022-example.md")"
chk 3  allow "$(w 'docs/a/b/c/new-findings.md')"

echo "create-only"
chk 4  deny "$(w 'docs/ROADMAP.md')"
chk 5  deny "$(w 'docs/decisions/0000-adr-template.md')"

echo "outside the writable root"
chk 6  deny "$(w 'apps/api/src/main.ts')"
chk 7  deny "$(w 'docs/../apps/api/src/main.ts')"
chk 8  deny "$(w 'docs/../../etc/passwd')"
chk 9  deny "$(w 'docsfake/x.md')"
chk 10 deny "$(w 'docs')"
chk 11 deny "$(w '/etc/passwd')"

echo "its own toolchain"
chk 12 deny "$(w '.claude/agents/architect-rebuild.md')"
chk 13 deny "$(w '.claude/hooks/architect-rebuild-write-gate.sh')"
chk 14 deny "$(w '.claude/settings.json')"

echo "malformed input — a call whose scope cannot be checked must not proceed"
chk 15 deny '{"tool_name":"Write","tool_input":{}}'
chk 16 deny "$(w '')"
chk 17 deny '{"tool_name":"Write","tool_input":{"file_path":42}}'
chk 18 deny 'not json'
chk 19 deny ''
chk 20 deny '{"tool_name":"Bash","tool_input":{"command":"echo hi > /etc/x"}}'
chk 21 deny "$(w 'docs/decisions/0023-x.md')" noproj

echo "the interpreter the adjudicator is written in"
NOPY="${NOPY:-/tmp/claude-0/-home-user-hello-world/166da4b5-1b2a-5916-b4ac-2e347fa567c1/scratchpad/nopy}"
if [ -x "$NOPY/bash" ]; then
  got="$(printf '%s' "$(w 'apps/api/src/main.ts')" | env PATH="$NOPY" CLAUDE_PROJECT_DIR="$R" "$GATE" 2>/dev/null \
        | python3 -c 'import sys,json
try: print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])
except Exception: print("UNPARSEABLE")')"
  if [ "$got" = deny ]; then printf '  ok    %-3s %s\n' 23 deny; pass=$((pass+1))
  else printf '  FAIL  %-3s expected deny got %s (a hook that emits nothing is not a denial)\n' 23 "$got"; fail=$((fail+1)); fi
else
  printf '  SKIP  23  no bash-without-python3 PATH staged at %s\n' "$NOPY"
fi

echo "symlinked parent"
ln -sfn /tmp "$R/docs/out"
chk 22 deny "$(w 'docs/out/x.md')"
rm -f "$R/docs/out"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
