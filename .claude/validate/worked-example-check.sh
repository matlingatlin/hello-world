#!/usr/bin/env bash
# The worked example claims to pass the checker. This proves it, rather than
# asserting it — the last two numbers in that file were typed from a sense of the
# length and both were wrong, which is why nothing in it is trusted unrun.
R="$(cd "$(dirname "$0")/../.." && pwd)"
EX="$R/.claude/skills/agent-assembly/assets/template/05-WORKED-EXAMPLE.md"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT

python3 - "$EX" "$T" <<'PY'
import re, sys, os, pathlib
ex, T = sys.argv[1], sys.argv[2]
m = re.search(r'```markdown\n(.*?)\n```', pathlib.Path(ex).read_text(), re.S)
if not m:
    print("FAIL: no fenced agent in the worked example"); sys.exit(1)
agent = m.group(1)
os.makedirs(f"{T}/.claude/agents"); os.makedirs(f"{T}/.claude/hooks")
os.makedirs(f"{T}/docs/research/evidence")
open(f"{T}/.claude/agents/migration-review.md","w").write(agent + "\n")
for sk in re.findall(r'^  - (\S+)$', agent, re.M):
    os.makedirs(f"{T}/.claude/skills/{sk}", exist_ok=True)
    open(f"{T}/.claude/skills/{sk}/SKILL.md","w").write(
        f"---\nname: {sk}\ndescription: Stub standing in for a real procedure.\n---\n\n"
        f"# {sk}\n\n## When this skill does not apply\n\n- stub\n")
for h in re.findall(r'hooks/([a-z0-9-]+\.sh)', agent):
    p = f"{T}/.claude/hooks/{h}"
    open(p,"w").write("#!/usr/bin/env bash\nexit 0\n"); os.chmod(p, 0o755)
open(f"{T}/docs/research/evidence/migration-review-test-results.md","w").write("# results\n")
open(f"{T}/docs/agent-registry.md","w").write(
    "| Agent | Status | Template |\n|---|---|---|\n| `migration-review` | in use | 1.0.0 |\n")

# and the two numbers the file quotes about itself
d = re.search(r'^description: (.*)$', agent, re.M).group(1)
body = agent.split('---', 2)[2]
doc = pathlib.Path(ex).read_text()
ok = True
for claimed, actual, what in [
    (re.search(r'description is (\d+) characters', doc), len(d), "description characters"),
    (re.search(r'Body: (\d+) words', doc), len(body.split()), "body words"),
]:
    if not claimed:
        print(f"FAIL: the file no longer states its {what}"); ok = False
    elif int(claimed.group(1)) != actual:
        print(f"FAIL: file says {claimed.group(1)} {what}, actual is {actual}"); ok = False
    else:
        print(f"  ok    {what}: {actual}")
sys.exit(0 if ok else 1)
PY
num=$?

echo "  running the checker on it:"
out=$(python3 "$R/.claude/validate/agents.py" "$T" 2>&1)
echo "$out" | sed 's/^/    /'
echo "$out" | grep -q '^CLEAN' || { echo "FAIL: the worked example does not pass the checker"; exit 1; }
[ "$num" -eq 0 ] || exit 1
echo
echo "worked example: passes, and its self-reported numbers are true"
