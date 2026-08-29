#!/usr/bin/env bash
# Controls for .claude/hooks/rebuild-prospector-diet.sh. Run from anywhere.
#
# Rows 1-22 are the table in docs/rebuild-agents/hook-proposal-prospector-diet.md,
# which shipped with an EMPTY Result column. Rows 23-32 were added by the eval
# suite (docs/evals-rebuild-pair.md) and are not in the proposal.
#
# Rows 1-4 and 23 are POSITIVE controls. Without them a `deny everything` script
# scores 27/32 and looks like a working gate.
R="$(cd "$(dirname "$0")/../.." && pwd)"
GATE="$R/.claude/hooks/rebuild-prospector-diet.sh"
pass=0; fail=0

chk () {  # chk <n> <expected: allow|deny> <stdin-payload> [nocpd|cwd:<dir>]
  local n="$1" expect="$2" payload="$3" mode="${4:-}" got dec
  case "$mode" in
    nocpd) got="$(printf '%s' "$payload" | env -u CLAUDE_PROJECT_DIR "$GATE" 2>/dev/null)" ;;
    cwd:*) got="$(cd "${mode#cwd:}" && printf '%s' "$payload" | env -u CLAUDE_PROJECT_DIR "$GATE" 2>/dev/null)" ;;
    *)     got="$(printf '%s' "$payload" | CLAUDE_PROJECT_DIR="$R" "$GATE" 2>/dev/null)" ;;
  esac
  # The hook signals ALLOW by printing nothing and exiting 0 ("no opinion").
  if [ -z "$got" ]; then dec=allow
  else
    dec="$(printf '%s' "$got" | python3 -c 'import sys,json
try: print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])
except Exception: print("UNPARSEABLE")' 2>/dev/null)"
  fi
  if [ "$dec" = "$expect" ]; then
    printf '  ok    %-3s %-5s %s\n' "$n" "$expect" "${5:-}"; pass=$((pass+1))
  else
    printf '  FAIL  %-3s expected %s got %s  %s\n' "$n" "$expect" "$dec" "${5:-}"; fail=$((fail+1))
  fi
}

j () { python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$1"; }
p () { printf '{"tool_name":"%s","tool_input":{"file_path":%s}}' "$1" "$(j "$2")"; }

echo "positive controls — proof this is a gate, not a wall"
chk 1  allow "$(p Read 'docs/rebuild/brief/2026-08-28-a.md')"
chk 2  allow "$(p Read "$R/docs/rebuild/brief/2026-08-28-a.md")"
chk 3  allow "$(p Read '.claude/skills/architecture-decision/references/far-domain-analogy.md')"
chk 4  allow "$(p Write 'docs/rebuild/candidates/run-01.md')"

echo "the existing system's solution vocabulary"
chk 5  deny "$(p Read '/home/user/scio/docs/next/LAYER-E-BUILD.md')"
chk 6  deny "$(p Read '/home/user/scio/docs/as-built/LAYER-A-INTAKE.md')"
chk 7  deny "$(p Read 'docs/ARCHITECTURE.md')"
chk 8  deny "$(p Read 'docs/decisions/0001-graph-is-standard.md')"
chk 9  deny "$(p Read 'docs/rebuild/candidates/run-01.md')" '' 'its own output: write-allowed, read-denied'
chk 10 deny "$(p Read 'docs/rebuild/brief/../../ARCHITECTURE.md')"
chk 11 deny "$(p Read 'docs/rebuild/briefing/x.md')"
chk 12 deny "$(p Read 'docs/rebuild/brief-old.md')"
chk 13 deny "$(p Read 'docs/rebuild/brief/notes.txt')"

echo "symlink whose basename resolves out of the allowlist"
mkdir -p "$R/docs/rebuild/brief"
ln -sfn /home/user/scio/docs/as-built "$R/docs/rebuild/brief/zz-eval-probe.md"
chk 14 deny "$(p Read 'docs/rebuild/brief/zz-eval-probe.md')"
rm -f "$R/docs/rebuild/brief/zz-eval-probe.md"

echo "writes"
chk 15 deny "$(p Write 'docs/ROADMAP.md')"
chk 16 deny "$(p Write '.claude/agents/rebuild-prospector.md')" '' 'its own definition'
chk 17 deny "$(p Write '.claude/hooks/rebuild-prospector-diet.sh')" '' 'the hook itself'
chk 18 deny "$(p Write '/etc/passwd')"

echo "malformed input — a call whose scope cannot be checked must not proceed"
chk 19 deny '{"tool_name":"Read","tool_input":{}}'
chk 20 deny '{'
chk 21 deny '{"tool_name":"Read","tool_input":{"file_path":null}}'
chk 22 deny '{"tool_name":"Bash","tool_input":{"file_path":"docs/rebuild/brief/a.md"}}' '' 'unexpected tool'

echo "added by the eval suite"
chk 23 allow "$(p Write 'docs/rebuild/candidates/nested/run-01.md')" '' 'positive: nested candidate write'
chk 24 deny "$(p Read '../scio/docs/as-built/LAYER-A-INTAKE.md')" '' 'relative traversal to the sibling repo'
chk 25 deny "$(p Write 'docs/rebuild/candidates/../../ROADMAP.md')" '' 'traversal out of the write root'
chk 26 deny "$(p Write 'docs/rebuild/brief/injected.md')" '' 'writing its own brief'
chk 27 deny "$(p Read 'CLAUDE.md')"
chk 28 deny "$(p Read 'docs/RETHINK-BRIEF.md')"
chk 29 deny "$(p Read '.claude/agents/rebuild-adjudicator.md')" '' 'the other half of the pair'
chk 30 deny '{"tool_name":"Read","tool_input":{"notebook_path":"docs/ARCHITECTURE.md"}}' '' 'path under the alternate key'
chk 31 deny "$(p Read "$R/docs/rebuild/brief/a.md")" cwd:/tmp 'CLAUDE_PROJECT_DIR unset + cwd elsewhere: fails CLOSED'
chk 32 deny "$(p Read '')" '' 'empty path'

echo "the interpreter the gate is written in"
NOPY="${NOPY:-/tmp/claude-0/-home-user-hello-world/166da4b5-1b2a-5916-b4ac-2e347fa567c1/scratchpad/nopy}"
if [ -x "$NOPY/bash" ]; then
  got="$(printf '%s' "$(p Read '/home/user/scio/docs/next/LAYER-E-BUILD.md')" \
        | env PATH="$NOPY" CLAUDE_PROJECT_DIR="$R" "$GATE" 2>/dev/null)"
  dec="$(printf '%s' "$got" | python3 -c 'import sys,json
try: print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])
except Exception: print("UNPARSEABLE" if sys.argv else "")' 2>/dev/null)"
  [ -z "$got" ] && dec=allow
  if [ "$dec" = deny ]; then printf '  ok    %-3s %-5s %s\n' 34 deny 'no python3 on PATH'; pass=$((pass+1))
  else printf '  FAIL  %-3s expected deny got %s (a gate that emits nothing has allowed it)\n' 34 "$dec"; fail=$((fail+1)); fi
else
  printf '  SKIP  34  no bash-without-python3 PATH staged at %s\n' "$NOPY"
fi

echo "documented behaviour, recorded rather than asserted"
chk 33 allow "$(p Read 'docs/rebuild/brief/2026/deep/a.md')" '' 'FINDING: bash * spans /, so brief/ is recursive'

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
