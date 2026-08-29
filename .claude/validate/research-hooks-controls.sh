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

# Fixtures are staged here and torn down on exit. They are NOT committed, and the id is
# deliberately not one real work would use: a fixture named `migration-review` — the id
# the tester brief gives N1 — sat in the tree once and pre-authorised a real promotion
# into the knowledge base. A control fixture that satisfies a live gate is not a fixture.
FID=zzz-hook-control
mkdir -p "$R/docs/research/commissions" "$R/docs/research/drafts" \
         "$R/docs/research/verdicts" "$R/docs/research/patches"
printf '# commission fixture — %s\n' "$FID" > "$R/docs/research/commissions/$FID.md"
printf '# verdict fixture — %s\n\n| claim | verdict |\n|---|---|\n| fixture | not-checkable |\n' "$FID" \
  > "$R/docs/research/verdicts/$FID.md"
cleanup () { rm -f "$R/docs/research/commissions/$FID.md" "$R/docs/research/verdicts/$FID.md" \
                   "$R/docs/research/drafts/link.md" "$NOTES/link.md"; }
trap cleanup EXIT

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
chk "$G1" 1  allow "$(p Write "docs/research/drafts/$FID.md")"
chk "$G1" 2  allow "$(p Write "$R/docs/research/drafts/$FID.md")"
chk "$G1" 3  deny  "$(p Write 'docs/research/drafts/payments.md')"
chk "$G1" 4  deny  "$(p Write 'docs/research/commissions/payments.md')"
chk "$G1" 5  deny  "$(p Write "docs/research/verdicts/$FID.md")"
chk "$G1" 6  deny  "$(p Write "$NOTES/$FID.md")"
chk "$G1" 7  deny  "$(p Write 'docs/PRD.md')"
chk "$G1" 8  deny  "$(p Write '.claude/agents/domain-researcher.md')"
chk "$G1" 9  deny  "$(p Write '.claude/hooks/research-commission.sh')"
chk "$G1" 10 deny  "$(p Write 'docs/research/drafts/../../../etc/passwd')"
chk "$G1" 11 deny  "$(p Write 'docs/research/drafts/../commissions/payments.md')"
chk "$G1" 12 deny  "$(p Write "docs/research/draftsfake/$FID.md")"
chk "$G1" 13 deny  "$(p Write "docs/research/drafts/sub/$FID.md")"
chk "$G1" 14 deny  "$(p Write 'docs/research/drafts/Migration-Review.md')"
chk "$G1" 15 deny  "$(p Write "docs/research/drafts/$FID.txt")"
ln -sfn /tmp "$R/docs/research/drafts-link" 2>/dev/null
mkdir -p "$R/docs/research/drafts" && ln -sfn /etc/passwd "$R/docs/research/drafts/link.md"
chk "$G1" 16 deny  "$(p Write 'docs/research/drafts/link.md')"
rm -f "$R/docs/research/drafts/link.md" "$R/docs/research/drafts-link"
chk "$G1" 17 deny  '{"tool_name":"Write","tool_input":{}}'
chk "$G1" 18 deny  'not json'
chk "$G1" 19 deny  "$(p Write "docs/research/drafts/$FID.md")" PATH="$NOPY"
chk "$G1" 20 allow "$(p Edit  "docs/research/drafts/$FID.md")"

G2="$R/.claude/hooks/note-promotion.sh"
echo
echo "note-promotion.sh — primary-source-verifier"
chk "$G2" 1  allow "$(p Write 'docs/research/verdicts/payments.md')"
chk "$G2" 2  allow "$(p Write "$NOTES/$FID.md")"
chk "$G2" 3  allow "$(p Write 'docs/research/patches/subagents.md')"
chk "$G2" 4  deny  "$(p Write "$NOTES/payments.md")"
chk "$G2" 5  deny  "$(p Write "$NOTES/subagents.md")"
chk "$G2" 6  deny  "$(p Edit  "$NOTES/subagents.md")"
chk "$G2" 7  deny  "$(p Write "docs/research/drafts/$FID.md")"
chk "$G2" 8  deny  "$(p Write "docs/research/commissions/$FID.md")"
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
chk "$G2" 20 deny  "$(p Write "$NOTES/$FID.md")" PATH="$NOPY"
chk "$G2" 21 deny  "$(p Write "/nonexistent/notes/$FID.md")" KNOWLEDGE_NOTES_DIR=/nonexistent/notes
chk "$G2" 22 deny  "$(p Write "$NOTES/$FID.md")" KNOWLEDGE_NOTES_DIR=/nonexistent/notes

# 23 — the defect an independent tester found on 2026-08-29: the gate tested the
# verdict's EXISTENCE, so a 28-byte file containing only a heading opened a real write
# into the knowledge base. A verdict with no ruling in it is a placeholder.
printf '# verdict: %s\n' "$FID" > "$R/docs/research/verdicts/$FID.md"
chk "$G2" 23 deny  "$(p Write "$NOTES/$FID.md")"
# and the same file, once it carries one ruling, opens again — proving 23 tests the
# ruling and not merely the rewrite
printf '# verdict: %s\n\n| c | not-checkable |\n' "$FID" > "$R/docs/research/verdicts/$FID.md"
chk "$G2" 24 allow "$(p Write "$NOTES/$FID.md")"

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
