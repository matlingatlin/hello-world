# Hook proposal — `research-commission.sh`

**For:** `domain-researcher`  **Event:** `PreToolUse`  **Matcher:** `^(Write|Edit|NotebookEdit)$`
**Status:** proposal. A human installs it. The builder that wrote this may not write
`.claude/hooks/` and may not add a `hooks:` line to an agent file — an agent that can
attach a wall can remove one.

**Until this is installed, `domain-researcher` has no path gate at all.** Its only
real boundary is its absent tools: no `Bash`, no `Agent`. Its agent body says so in
those words. Install this before its first real run.

## What must be impossible, and why prose will not do it

Two things, and they are the same mechanism seen from two sides.

**1 · An uncommissioned sweep must have nowhere to land.** The recorded failure is
in `docs/decomposition-agent-pipeline.md` §5: research decides what is worth knowing
before anyone knows what the agent will do, so a sweep of "database" comes back for
an agent that only reviews migrations. The chosen resolution is that the **candidate
sentence** scopes the research and a later stage may commission one narrower second
sweep. That resolution is only real if an uncommissioned draft cannot be written.

**2 · Nothing this agent produces may enter the knowledge base.** The whole of B130
is that a note must be checked by someone other than its author before it is
treated as evidence. If the researcher can write into
`/home/user/skills-repo/knowledge/notes/`, the verifier is decoration.

Neither can be a sentence. The measured position on rules of that shape is
unambiguous: eight anchoring-warning variants, differing in content and timing, were
**all** indistinguishable from no warning, and a specific warning about a specific
bad feature left the warned group the most fixated of three. A `PreToolUse` hook
runs before every permission check, `bypassPermissions` included, and can only
tighten.

**What it does not do.** It gates the **path**, not the content. It cannot tell
whether the draft answers the commissioned question or a wider one; content
inspection was tried in this repository and an independent tester walked past it
three ways. What it makes impossible is that an artefact exists with no commission
behind it, and that anything reaches the base from this agent.

## The script

```bash
#!/usr/bin/env bash
# research-commission.sh — PreToolUse on Write|Edit|NotebookEdit for domain-researcher.
#
# Allows exactly one shape of write:
#     $ROOT/docs/research/drafts/<id>.md   when $ROOT/docs/research/commissions/<id>.md exists
# Everything else is denied, including the commissions directory itself: an agent
# that writes its own commission has no scope.
#
# Contract: stdin is the PreToolUse JSON payload. Exit 0 always; the decision is
# carried in JSON on stdout. A call whose scope cannot be checked is denied.
set -uo pipefail

deny() {
  python3 -c '
import json,sys
print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse",
  "permissionDecision":"deny","permissionDecisionReason":sys.argv[1]}}))' "$1"
  exit 0
}
allow() {
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
}

payload=$(cat)
command -v python3 >/dev/null 2>&1 || { printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"research-commission: python3 unavailable; payload cannot be inspected."}}'; exit 0; }

path=$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("notebook_path") or "")
' 2>/dev/null)

[ -n "$path" ] || deny "research-commission: no file path in the tool call, so its scope cannot be checked. Malformed or unparseable payloads are denied."

root="${CLAUDE_PROJECT_DIR:-$PWD}"
# Resolve symlinks and .. without requiring the target to exist yet.
abs=$(python3 -c '
import os,sys
p, root = sys.argv[1], sys.argv[2]
if not os.path.isabs(p):
    p = os.path.join(root, p)
print(os.path.normpath(os.path.realpath(os.path.dirname(p)) + "/" + os.path.basename(p)))
' "$path" "$root" 2>/dev/null)
absroot=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$root" 2>/dev/null)

[ -n "$abs" ] && [ -n "$absroot" ] || deny "research-commission: path could not be resolved."

drafts="$absroot/docs/research/drafts"
case "$abs" in
  "$drafts"/*) ;;
  *) deny "research-commission: domain-researcher writes only to docs/research/drafts/<id>.md, where <id> is a commission that exists. This path is outside it. If you need a commission, ask for one; an agent that writes its own commission has no scope." ;;
esac

rel="${abs#"$drafts"/}"
case "$rel" in
  */*) deny "research-commission: drafts are flat files directly under docs/research/drafts/, not in subdirectories." ;;
esac

id="${rel%.md}"
[ "$id.md" = "$rel" ] || deny "research-commission: a draft must be a .md file."
case "$id" in
  ''|*[!a-z0-9-]*) deny "research-commission: the id must be lower-case letters, digits and hyphens — it is also the name of the verdict document and the note." ;;
esac

[ -f "$absroot/docs/research/commissions/$id.md" ] || deny "research-commission: no commission at docs/research/commissions/$id.md. Research is scoped by a candidate sentence written by whoever wants it (docs/decomposition-agent-pipeline.md, section 5). A sweep nobody commissioned has nowhere to land."

allow
```

## Controls — all must be run before installing

Every row is a command with an observed exit and observed stdout, not a judgement.
**Run 2026-08-29 by a session with a shell: 20/20 pass.** The script was extracted from the
block above programmatically rather than retyped; the harness is
`.claude/validate/research-hooks-controls.sh`, which also carries the note-promotion table, and
it is mutation-tested — a deny-everything mutant of this script scores 39/42 across the joint
suite, failing exactly rows 1, 2 and 20, the three that prove it is a gate rather than a wall.

Set up: `docs/research/commissions/migration-review.md` exists;
`docs/research/commissions/payments.md` does not.

| # | Input | Expected |
|---|---|---|
| 1 | Write `docs/research/drafts/migration-review.md` | **allow** — the positive control. Without it this is a wall, not a gate |
| 2 | Write the absolute form of the same path | allow |
| 3 | Write `docs/research/drafts/payments.md` | deny — no commission |
| 4 | Write `docs/research/commissions/payments.md` | deny — it may not commission itself |
| 5 | Write `docs/research/verdicts/migration-review.md` | deny — the verifier's directory, not this agent's |
| 6 | Write `/home/user/skills-repo/knowledge/notes/migration-review.md` | deny — outside the root entirely |
| 7 | Write `docs/PRD.md` | deny |
| 8 | Write `.claude/agents/domain-researcher.md` | deny — its own definition |
| 9 | Write `.claude/hooks/research-commission.sh` | deny — the hook itself |
| 10 | Write `docs/research/drafts/../../../etc/passwd` | deny — traversal, after realpath resolution |
| 11 | Write `docs/research/drafts/../commissions/payments.md` | deny — traversal through an allowed root |
| 12 | Write `docs/research/draftsfake/migration-review.md` | deny — prefix lookalike |
| 13 | Write `docs/research/drafts/sub/migration-review.md` | deny — subdirectory |
| 14 | Write `docs/research/drafts/Migration-Review.md` | deny — id charset; ids are lower-case because three files match on them |
| 15 | Write `docs/research/drafts/migration-review.txt` | deny — not `.md` |
| 16 | A symlink `docs/research/drafts/link.md` pointing outside the repo | deny — `realpath` on the directory resolves it before the case match |
| 17 | Payload with no `file_path` | deny |
| 18 | Malformed JSON on stdin | deny |
| 19 | `python3` absent from `PATH` | deny |
| 20 | `Edit` (not `Write`) on `docs/research/drafts/migration-review.md` | allow — the matcher covers Edit and the same rule applies |

Row 1 and row 20 are the rows that prove this is a gate. Rows 11, 12 and 16 are the
three ways past a naive prefix check.

## Installation

1. `.claude/hooks/research-commission.sh`, `chmod +x`.
2. Add to `.claude/agents/domain-researcher.md` frontmatter:

```yaml
hooks:
  PreToolUse:
    - matcher: "^(Write|Edit|NotebookEdit)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/research-commission.sh"
```

3. Re-run `python3 .claude/validate/agents.py`: the validator checks that a hook
   named in frontmatter exists and is executable, and that the matcher is anchored.
4. Amend the "What you may not do" section of the agent body to move the commission
   gate from *proposed* to *in force*. That is an edit to an existing agent file and
   is a human's to make.

## What this does not do

- It cannot tell whether the draft stays inside the commissioned scope. Only the
  path is checkable. Scope adherence is a case for the tester's suite.
- It does not stop the agent **reading** widely. That is deliberate: the constraint
  is on what it emits, and a read gate here would block the reuse-first check
  against the existing knowledge base, which is a standing rule of that repository.
- It counts nothing. "At most one narrower second sweep" is a rule about the caller,
  and this hook cannot see the caller.
