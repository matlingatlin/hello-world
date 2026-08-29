#!/usr/bin/env bash
# POSITIVE CONTROLS for the validator.
# A checker that is quiet proves nothing: absence of a result is indistinguishable
# from a correct negative. Each case below plants ONE defect in a throwaway repo
# and asserts the validator names it. If a case stops firing, the check it guards
# has silently died.
set -uo pipefail
V="$(cd "$(dirname "$0")" && pwd)/agents.py"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0

mk() { # mk <name> ; builds a minimal clean repo in $T/<name>
  local d="$T/$1"; mkdir -p "$d/.claude/agents" "$d/.claude/skills/good-skill"
  printf -- '---\nname: good-agent\ndescription: A clean agent.\ntools: Read\n---\nBody.\n' > "$d/.claude/agents/good-agent.md"
  printf -- '---\nname: good-skill\ndescription: A clean skill.\n---\n\n# S\n\n## When this skill does not apply\n\n- never\n' > "$d/.claude/skills/good-skill/SKILL.md"
  echo "$d"
}
expect() { # expect <label> <catch|clean> <substring> <dir>
  local out; out=$(python3 "$V" "$4" 2>&1)
  if [ "$2" = catch ]; then
    if grep -qi -- "$3" <<<"$out"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  MISSED  $1"; fi
  else
    if grep -q "^CLEAN" <<<"$out"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  NOISY   $1: $(grep -m1 FAIL <<<"$out")"; fi
  fi
}

d=$(mk clean);                                                        expect "clean repo stays clean" clean "" "$d"
d=$(mk t1);  sed -i '/^tools:/d' "$d/.claude/agents/good-agent.md";   expect "tools: omitted" catch "INHERITS EVERY TOOL" "$d"
d=$(mk t2);  sed -i "s/^description: .*/description: has <angle> brackets/" "$d/.claude/agents/good-agent.md"
                                                                       expect "angle brackets in description" catch "forbidden in frontmatter" "$d"
d=$(mk t3);  python3 -c "
import sys;p=sys.argv[1];t=open(p).read();open(p,'w').write(t.replace('description: A clean agent.','description: '+'x'*1100))" "$d/.claude/agents/good-agent.md"
                                                                       expect "description over 1024" catch "over the 1024 limit" "$d"
d=$(mk t4);  printf -- 'name: x\ndescription: y\n' > "$d/.claude/skills/good-skill/SKILL.md"
                                                                       expect "unterminated frontmatter" catch "line 1 is not exactly" "$d"
d=$(mk t5);  printf -- '---\nname: x\ndescription: y\n' > "$d/.claude/skills/good-skill/SKILL.md"
                                                                       expect "frontmatter never closed" catch "never closed" "$d"
d=$(mk t6);  touch "$d/.claude/skills/good-skill/README.md";           expect "README inside a skill" catch "README.md inside a skill folder" "$d"
d=$(mk t7);  printf -- 'skills:\n  - a\n  - b\n  - c\n  - d\n' >> /dev/null
             python3 -c "
import sys;p=sys.argv[1];t=open(p).read()
open(p,'w').write(t.replace('tools: Read','tools: Read\nskills:\n  - good-skill\n  - good-skill\n  - good-skill\n  - good-skill'))" "$d/.claude/agents/good-agent.md"
                                                                       expect "more than 3 preloaded skills" catch "over the cap" "$d"
d=$(mk t8);  python3 -c "
import sys;p=sys.argv[1];t=open(p).read()
open(p,'w').write(t.replace('tools: Read','tools: Read\nskills:\n  - ghost-skill'))" "$d/.claude/agents/good-agent.md"
                                                                       expect "preloads a nonexistent skill" catch "does not exist in this repo" "$d"
d=$(mk t9);  sed -i 's|# S|# S\n\nSee `references/gone.md`.|' "$d/.claude/skills/good-skill/SKILL.md"
                                                                       expect "dead reference file" catch "dead reference" "$d"
d=$(mk t10); python3 -c "
import sys;p=sys.argv[1];t=open(p).read()
open(p,'w').write(t.replace('tools: Read','tools: Read\nhooks:\n  PreToolUse:\n    - matcher: \"Write|Edit\"\n      hooks:\n        - type: command\n          command: \"/nonexistent.sh\"'))" "$d/.claude/agents/good-agent.md"
                                                                       expect "unanchored matcher" catch "unanchored" "$d"
             expect "missing hook script" catch "hook command not found" "$d"
d=$(mk t11); sed -i 's/^## When this skill does not apply/## Notes/' "$d/.claude/skills/good-skill/SKILL.md"
                                                                       expect "no decline section (warns)" catch "no decline section" "$d"
d=$(mk t12); python3 -c "
import sys;p=sys.argv[1];t=open(p).read()
open(p,'w').write(t.replace('# S','# S\n\nNot for that (use ghost-thing).'))" "$d/.claude/skills/good-skill/SKILL.md"
                                                                       expect "NOT-clause routes nowhere" catch "exists neither as a skill nor an agent" "$d"

echo; echo "positive controls: pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
