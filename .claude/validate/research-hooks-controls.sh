#!/usr/bin/env bash
# Controls for research-commission.sh and note-promotion.sh, from the tables in
# docs/hook-proposal-research-commission.md and docs/hook-proposal-note-promotion.md.
# Positive controls first: a script that denies everything passes every deny row.
R="$(cd "$(dirname "$0")/../.." && pwd)"
NOTES="${KNOWLEDGE_NOTES_DIR:-/home/user/skills-repo/knowledge/notes}"
# A PATH carrying bash but not python3. Emptying PATH instead would make
# `env bash` unfindable and the script would never run — testing nothing.
NOPY="/tmp/claude-0/-home-user-hello-world/166da4b5-1b2a-5916-b4ac-2e347fa567c1/scratchpad/nopy"
pass=0; fail=0

decide () { # decide <gate> <payload> [env assignments...]
  local gate="$1" payload="$2"; shift 2
  printf '%s' "$payload" | env CLAUDE_PROJECT_DIR="$R" "$@" "$gate" 2>/dev/null | python3 -c 'import sys,json
try: print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecision"])
except Exception: print("UNPARSEABLE")' 2>/dev/null
}
chk () { # chk <gate> <n> <expected> <payload> [env...]
  local gate="$1" n="$2" expect="$3" payload="$4"; shift 4
  local got; got="$(decide "$gate" "$payload" "$@")"
  if [ "$got" = "$expect" ]; then printf '  ok    %-4s %s\n' "$n" "$expect"; pass=$((pass+1))
  else printf '  FAIL  %-4s expected %s got %s\n' "$n" "$expect" "$got"; fail=$((fail+1)); fi
}
p () { python3 -c 'import json,sys;print(json.dumps({"tool_name":sys.argv[1],"tool_input":{"file_path":sys.argv[2]}}))' "$1" "$2"; }

G1="$R/.claude/hooks/research-commission.sh"
echo "research-commission.sh — domain-researcher"
chk "$G1" 1  allow "$(p Write 'docs/research/drafts/migration-review.md')"
chk "$G1" 2  allow "$(p Write "$R/docs/research/drafts/migration-review.md")"
chk "$G1" 3  deny  "$(p Write 'docs/research/drafts/payments.md')"
chk "$G1" 4  deny  "$(p Write 'docs/research/commissions/payments.md')"
chk "$G1" 5  deny  "$(p Write 'docs/research/verdicts/migration-review.md')"
chk "$G1" 6  deny  "$(p Write "$NOTES/migration-review.md")"
chk "$G1" 7  deny  "$(p Write 'docs/PRD.md')"
chk "$G1" 8  deny  "$(p Write '.claude/agents/domain-researcher.md')"
chk "$G1" 9  deny  "$(p Write '.claude/hooks/research-commission.sh')"
chk "$G1" 10 deny  "$(p Write 'docs/research/drafts/../../../etc/passwd')"
chk "$G1" 11 deny  "$(p Write 'docs/research/drafts/../commissions/payments.md')"
chk "$G1" 12 deny  "$(p Write 'docs/research/draftsfake/migration-review.md')"
chk "$G1" 13 deny  "$(p Write 'docs/research/drafts/sub/migration-review.md')"
chk "$G1" 14 deny  "$(p Write 'docs/research/drafts/Migration-Review.md')"
chk "$G1" 15 deny  "$(p Write 'docs/research/drafts/migration-review.txt')"
ln -sfn /tmp "$R/docs/research/drafts-link" 2>/dev/null
mkdir -p "$R/docs/research/drafts" && ln -sfn /etc/passwd "$R/docs/research/drafts/link.md"
chk "$G1" 16 deny  "$(p Write 'docs/research/drafts/link.md')"
rm -f "$R/docs/research/drafts/link.md" "$R/docs/research/drafts-link"
chk "$G1" 17 deny  '{"tool_name":"Write","tool_input":{}}'
chk "$G1" 18 deny  'not json'
chk "$G1" 19 deny  "$(p Write 'docs/research/drafts/migration-review.md')" PATH="$NOPY"
chk "$G1" 20 allow "$(p Edit  'docs/research/drafts/migration-review.md')"

G2="$R/.claude/hooks/note-promotion.sh"
echo
echo "note-promotion.sh — primary-source-verifier"
chk "$G2" 1  allow "$(p Write 'docs/research/verdicts/payments.md')"
chk "$G2" 2  allow "$(p Write "$NOTES/migration-review.md")"
chk "$G2" 3  allow "$(p Write 'docs/research/patches/subagents.md')"
chk "$G2" 4  deny  "$(p Write "$NOTES/payments.md")"
chk "$G2" 5  deny  "$(p Write "$NOTES/subagents.md")"
chk "$G2" 6  deny  "$(p Edit  "$NOTES/subagents.md")"
chk "$G2" 7  deny  "$(p Write 'docs/research/drafts/migration-review.md')"
chk "$G2" 8  deny  "$(p Write 'docs/research/commissions/migration-review.md')"
chk "$G2" 9  deny  "$(p Write 'docs/PRD.md')"
chk "$G2" 10 deny  "$(p Write '.claude/agents/primary-source-verifier.md')"
chk "$G2" 11 deny  "$(p Write '.claude/hooks/note-promotion.sh')"
chk "$G2" 12 deny  "$(p Write "$NOTES/../INDEX.md")"
chk "$G2" 13 deny  "$(p Write 'docs/research/verdicts/../drafts/x.md')"
chk "$G2" 14 deny  "$(p Write 'docs/research/verdictsfake/x.md')"
chk "$G2" 15 deny  "$(p Write "$NOTES/sub/x.md")"
chk "$G2" 16 deny  "$(p Write "$NOTES/Migration-Review.md")"
ln -sfn "$NOTES/subagents.md" "$NOTES/link.md" 2>/dev/null
chk "$G2" 17 deny  "$(p Write "$NOTES/link.md")"
rm -f "$NOTES/link.md"
chk "$G2" 18 deny  '{"tool_name":"Write","tool_input":{}}'
chk "$G2" 19 deny  'not json'
chk "$G2" 20 deny  "$(p Write "$NOTES/migration-review.md")" PATH="$NOPY"
chk "$G2" 21 deny  "$(p Write "/nonexistent/notes/migration-review.md")" KNOWLEDGE_NOTES_DIR=/nonexistent/notes
chk "$G2" 22 deny  "$(p Write "$NOTES/migration-review.md")" KNOWLEDGE_NOTES_DIR=/nonexistent/notes

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
