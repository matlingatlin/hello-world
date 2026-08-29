# Hook proposal — `agent-review-readonly-bash`

**For:** `agent-fitness-review`  **Event:** `PreToolUse`  **Matcher:** `^Bash$`

**Status: proposed, and not required by the agent as shipped.** `agent-fitness-review`
holds no `Bash` today, so nothing here is load-bearing yet. This document exists so that
the upgrade cannot happen unwalled: **install this hook and add the matcher line in the
same change that adds `Bash` to `tools:`, or do not add `Bash` at all.**

A human installs it. An agent that can write executable hooks can delete its own wall.

## Why anyone would grant `Bash` at all

The spec's baseline row R11: the two strongest reviews this repository has produced both
held a shell and used it heavily, and the shell found what reading did not — a 28-byte
fixture holding the shared knowledge base open, and three successive strengthenings of
one gate, of which the record says *"every one came from running a case, none from reading
the script"* (`docs/research/evidence/c4-x1-run.md:119`). A read-only reviewer is a
strictly weaker instrument and its accounting block has to say so.

## What must be impossible, and why

A `PreToolUse` hook runs before every permission check — `bypassPermissions` included —
and can only tighten. *(`unevidenced`: this ordering is documented rather than measured;
`hooks.md` in the knowledge base carries no per-claim verdict token. Verify it against
the current docs before relying on it.)* That is why this is a hook and not a sentence.

| Must be impossible | What it would cost |
|---|---|
| writing, moving or deleting any file | the reviewer becomes a repairer, and the agent it reviewed is no longer the agent that was reviewed. `docs-only-write.sh` gates `Write`; a shell walks straight past it, which is why *"an agent with a path-scoped write gate and `Bash` has no write gate"* |
| running any program not on the allowlist | an arbitrary interpreter (`python3 -c`, `node -e`, `sh -c`) is a write primitive with extra steps |
| chaining, piping, substituting or redirecting | one allowlisted command plus `;` or `$( )` is an arbitrary command. The allowlist has to be on the **whole** string, not on its first word |
| any network call | `curl`, `wget`, `nc`, `ssh`, `git push`, `git fetch` — a reviewer that reaches the network can exfiltrate everything it was given to read |
| any mutating `git` subcommand | `commit`, `checkout`, `reset`, `clean`, `restore`, `push` all change the tree the reviewer is reporting on |

Deny-by-default: anything not matched exactly is denied, and a payload that cannot be
parsed is denied rather than waved through.

## The script

Install at `.claude/hooks/agent-review-readonly-bash.sh`, mode `0755`.

```bash
#!/usr/bin/env bash
# PreToolUse gate for agent-fitness-review's shell.
#
# Why this is a hook and not a sentence: a PreToolUse hook runs before every
# permission check, including bypassPermissions, and can only tighten.
#
# What it enforces: the reviewer may run the repository's own read-only checkers
# and read-only git. Nothing else. The allowlist is matched against the WHOLE
# command string, because an allowlist on the first word is not an allowlist.
#
# Contract: stdin is the PreToolUse JSON payload. Exit 0 always; the decision is
# carried in the JSON on stdout. Silence (no output) means "no opinion".
set -uo pipefail

payload=$(cat)

deny() {
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"agent-review-readonly-bash: $1\"}}"
  exit 0
}

cmd=$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("__NOCMD__"); raise SystemExit(0)
ti = d.get("tool_input") or {}
c = ti.get("command")
print(c if isinstance(c, str) and c.strip() else "__NOCMD__")
' 2>/dev/null)

# An unparseable payload, a missing command, or a python that did not run at all.
if [ -z "$cmd" ] || [ "$cmd" = "__NOCMD__" ]; then
  deny "no command in the tool call, so its scope cannot be checked."
fi

# Any shell metacharacter turns one allowlisted command into an arbitrary one.
case "$cmd" in
  *';'*|*'&'*|*'|'*|*'>'*|*'<'*|*'\`'*|*'$('*|*'${'*|*$'\n'*|*$'\r'*|*'!'*)
    deny "shell metacharacters are refused: one allowlisted command plus a chain is an arbitrary command. Run one plain command per call."
    ;;
esac

# Normalise runs of whitespace so " git   log " and "git log" compare equal.
norm=$(printf '%s' "$cmd" | tr -s '[:space:]' ' ' | sed -e 's/^ //' -e 's/ $//')

case "$norm" in
  "python3 .claude/validate/agents.py"|"python3 .claude/validate/agents.py .")
    exit 0 ;;
  "bash .claude/validate/selftest.sh")
    exit 0 ;;
  "bash .claude/validate/"*-controls.sh)
    # Repository-owned control harnesses. They stage and tear down their own
    # fixtures, which is a write — permitted deliberately, and only for paths
    # with no separator after the fixed prefix.
    case "${norm#bash .claude/validate/}" in
      */*) deny "control harnesses run only from .claude/validate/ itself, with no path separator." ;;
      *)   exit 0 ;;
    esac ;;
  "git log"|"git log "*|"git show "*|"git ls-tree "*|"git status"|"git status "*|\
  "git diff"|"git diff "*|"git blame "*|"git rev-parse "*|"git branch"|"git branch "*)
    exit 0 ;;
  *)
    deny "not on the read-only allowlist. Permitted: python3 .claude/validate/agents.py; bash .claude/validate/selftest.sh; bash .claude/validate/*-controls.sh; read-only git (log, show, ls-tree, status, diff, blame, rev-parse, branch). A finding is a row in your document, never a change to the tree."
    ;;
esac
```

## Controls — all must be run before installing

Payload shape: `{"tool_name":"Bash","tool_input":{"command":"…"}}` on stdin, with
`CLAUDE_PROJECT_DIR` set to the repo root.

| # | Input `command` | Expected | Result |
|---|---|---|---|
| 1 | `python3 .claude/validate/agents.py` | allow | |
| 2 | `python3 .claude/validate/agents.py .` | allow | |
| 3 | `bash .claude/validate/selftest.sh` | allow | |
| 4 | `bash .claude/validate/research-hooks-controls.sh` | allow | |
| 5 | `git log --oneline -5` | allow | |
| 6 | `git ls-tree -r --name-only HEAD` | allow | |
| 7 | `git   status   --porcelain` (repeated whitespace) | allow | |
| 8 | `echo hi > docs/x.md` | deny — redirect | |
| 9 | `python3 .claude/validate/agents.py; rm -rf docs` | deny — chain | |
| 10 | `python3 .claude/validate/agents.py && git push` | deny — chain | |
| 11 | `python3 -c "open('/etc/x','w')"` | deny — not allowlisted | |
| 12 | `bash .claude/validate/../hooks/agent-builder-scope.sh` | deny — separator after the prefix | |
| 13 | `bash .claude/validate/x/y-controls.sh` | deny — separator after the prefix | |
| 14 | `git commit -am x` | deny — mutating git | |
| 15 | `git checkout -- .` | deny — mutating git | |
| 16 | `git push origin main` | deny — mutating git | |
| 17 | `curl https://example.com` | deny — network | |
| 18 | `cat $(ls docs)` | deny — command substitution | |
| 19 | `` git log `whoami` `` | deny — backtick | |
| 20 | `git log\nrm -rf docs` (embedded newline) | deny — newline | |
| 21 | `PYTHON3=x python3 .claude/validate/agents.py` (env prefix) | deny — not an exact match | |
| 22 | payload with `tool_input.command` absent | deny | |
| 23 | payload with `command: ""` | deny | |
| 24 | malformed JSON on stdin | deny | |
| 25 | empty stdin | deny | |

Rows 1–7 are the positive controls and they are not optional: a gate that denies
everything passes every deny case. Rows 12 and 13 exist because the one wildcard in the
allowlist is the only place a traversal can enter.

Then write `.claude/validate/agent-review-readonly-bash-controls.sh` on the pattern of
`.claude/validate/research-hooks-controls.sh`, so these 25 rows are re-runnable. Four of
this repo's seven installed hooks have controls that were run once by hand and cannot be
re-run; do not make it five.

## Installation

1. `install -m 0755 <script> .claude/hooks/agent-review-readonly-bash.sh`
2. Run the 25 controls. Do not proceed on any red row.
3. **In the same edit**, add `Bash` to `tools:` in `.claude/agents/agent-fitness-review.md`
   and add to its `hooks.PreToolUse`:

```yaml
    - matcher: "^Bash$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/agent-review-readonly-bash.sh"
```

4. Run `python3 .claude/validate/agents.py`. The matcher must be anchored and the hook
   must exist and be executable, or the run fails and names it.
5. Amend the agent body: the bullet reading *"You cannot execute anything. `Bash` is
   absent"* becomes a statement of what the allowlist permits and what it still cannot
   see. A body that describes a wall state which has since changed is a recorded defect
   class in this repo (`docs/domain-research-test-results.md:63-85`).

## What this hook still cannot do

It is a **command-shape gate**. It cannot tell whether the reviewer read the output it
quotes, whether a verdict was reached honestly, or whether the allowlisted checker was
run against the right tree. Every wall in this repository is a path or string gate and
every failure anyone actually cares about is content and speech. Installing this hook
buys containment of the shell, and nothing about the quality of a review.
