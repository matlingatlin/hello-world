# Hook proposal — `note-promotion.sh`

**For:** `primary-source-verifier`  **Event:** `PreToolUse`  **Matcher:** `^(Write|Edit|NotebookEdit)$`
**Status:** proposal. A human installs it. The builder that wrote this may not write
`.claude/hooks/` and may not add a `hooks:` line to an agent file.

**Until this is installed, `primary-source-verifier` has no path gate.** Its real
boundaries today are its absent tools: no `WebSearch`, no `Edit`, no `Bash`, no
`Agent`. Its agent body says so. Install this before its first real run.

## What must be impossible, and why prose will not do it

**1 · A note must not reach the knowledge base without an independent verdict
behind it.** This is B130 stated as a mechanism. The base currently holds 26 notes,
every one marked `status: verified`, none naming a verifier — the field records that
an author was satisfied with their own work. The whole stage is pointless if the
promoted note and the verdict document are not welded together, and the weld is:
`knowledge/notes/<id>.md` may not be written unless
`docs/research/verdicts/<id>.md` exists.

**2 · An existing note must not be overwritten.** An agent that can rewrite the
record can rewrite what the record said yesterday. This repository already settled
the same question for agent files and settled it with **create-only**, after an
independent tester found three ways past a gate that inspected content: delete a
block, widen a line, rename a key across two innocent edits. Every one needed a file
that already existed. The cost is real and is recorded: extending a note becomes a
patch a human applies.

**3 · The verifier must not edit the draft it is judging.** A verifier that can
sharpen a claim before ruling on it is ruling on its own claim.

**What it does not do.** It cannot check that the verdict document is *honest*, that
its rows match the draft's claims, or that the note contains only supported claims.
Those are the tester's cases and the reader's. What it makes impossible is a note
appearing with no verification record at all, and history being rewritten.

## The script

```bash
#!/usr/bin/env bash
# note-promotion.sh — PreToolUse on Write|Edit|NotebookEdit for primary-source-verifier.
#
# Allows exactly three shapes of write:
#     $ROOT/docs/research/verdicts/<id>.md          always
#     $ROOT/docs/research/patches/<id>.md           always
#     $NOTES/<id>.md   only when $ROOT/docs/research/verdicts/<id>.md exists
#                      AND $NOTES/<id>.md does not already exist
# where $NOTES defaults to /home/user/skills-repo/knowledge/notes and may be
# overridden by KNOWLEDGE_NOTES_DIR. Everything else is denied, including
# docs/research/drafts/ — the verifier does not edit what it judges.
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
command -v python3 >/dev/null 2>&1 || { printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"note-promotion: python3 unavailable; payload cannot be inspected."}}'; exit 0; }

path=$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
print(ti.get("file_path") or ti.get("notebook_path") or "")
' 2>/dev/null)

[ -n "$path" ] || deny "note-promotion: no file path in the tool call, so its scope cannot be checked."

root="${CLAUDE_PROJECT_DIR:-$PWD}"
notes="${KNOWLEDGE_NOTES_DIR:-/home/user/skills-repo/knowledge/notes}"

resolve() {
  python3 -c '
import os,sys
p, root = sys.argv[1], sys.argv[2]
if not os.path.isabs(p):
    p = os.path.join(root, p)
print(os.path.normpath(os.path.realpath(os.path.dirname(p)) + "/" + os.path.basename(p)))
' "$1" "$root" 2>/dev/null
}
realdir() { python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1" 2>/dev/null; }

abs=$(resolve "$path")
absroot=$(realdir "$root")
absnotes=$(realdir "$notes")
[ -n "$abs" ] && [ -n "$absroot" ] && [ -n "$absnotes" ] || deny "note-promotion: path could not be resolved."

# flat-<id>.md check shared by all three allowed roots
id_of() {   # $1 = absolute path, $2 = absolute allowed dir; echoes id or empty
  local p="$1" d="$2" rel
  case "$p" in "$d"/*) rel="${p#"$d"/}" ;; *) return 1 ;; esac
  case "$rel" in */*) return 1 ;; esac
  case "$rel" in *.md) ;; *) return 1 ;; esac
  rel="${rel%.md}"
  case "$rel" in ''|*[!a-z0-9-]*) return 1 ;; esac
  printf '%s' "$rel"
}

if id=$(id_of "$abs" "$absroot/docs/research/verdicts"); then allow; fi
if id=$(id_of "$abs" "$absroot/docs/research/patches");  then allow; fi

if id=$(id_of "$abs" "$absnotes"); then
  [ -f "$absroot/docs/research/verdicts/$id.md" ] || deny "note-promotion: no verdict document at docs/research/verdicts/$id.md. A note reaches the knowledge base only behind a per-claim verdict written by an agent that did not draft it. Write the verdict first."
  [ -e "$abs" ] && deny "note-promotion: $id.md already exists in the knowledge base. This pipeline creates notes; it does not rewrite them. An extension is a patch under docs/research/patches/$id.md that a human applies."
  allow
fi

deny "note-promotion: primary-source-verifier writes only docs/research/verdicts/<id>.md, docs/research/patches/<id>.md, and a NEW note in the knowledge base behind an existing verdict. This path is none of those. It does not edit drafts: a verifier that can sharpen a claim before ruling on it is ruling on its own claim."
```

## Controls — all must be run before installing

**Run 2026-08-29 by a session with a shell: 21/21, after one fix that row 21 caught.**
Harness: `.claude/validate/research-hooks-controls.sh`, mutation-tested — an allow-everything
mutant of this script scores 23/42 on the joint suite.

Set up: `docs/research/verdicts/migration-review.md` exists;
`docs/research/verdicts/payments.md` does not;
`$NOTES/subagents.md` exists; `$NOTES/migration-review.md` does not.

| # | Input | Expected |
|---|---|---|
| 1 | Write `docs/research/verdicts/payments.md` | **allow** — positive control: a verdict may always be written, including for a note that will never be promoted |
| 2 | Write `$NOTES/migration-review.md` | **allow** — positive control: the promotion path with its verdict present |
| 3 | Write `docs/research/patches/subagents.md` | allow — the route for extending a note that exists |
| 4 | Write `$NOTES/payments.md` | deny — no verdict document |
| 5 | Write `$NOTES/subagents.md` | deny — the note already exists; create-only |
| 6 | `Edit` on `$NOTES/subagents.md` | deny — same rule via the same matcher (the agent also holds no `Edit` tool, so this is defence in depth) |
| 7 | Write `docs/research/drafts/migration-review.md` | deny — it does not edit what it judges |
| 8 | Write `docs/research/commissions/migration-review.md` | deny |
| 9 | Write `docs/PRD.md` | deny |
| 10 | Write `.claude/agents/primary-source-verifier.md` | deny — its own definition |
| 11 | Write `.claude/hooks/note-promotion.sh` | deny — the hook itself |
| 12 | Write `$NOTES/../INDEX.md` | deny — traversal out of the notes directory |
| 13 | Write `docs/research/verdicts/../drafts/x.md` | deny — traversal through an allowed root |
| 14 | Write `docs/research/verdictsfake/x.md` | deny — prefix lookalike |
| 15 | Write `$NOTES/sub/x.md` | deny — subdirectory |
| 16 | Write `$NOTES/Migration-Review.md` | deny — id charset; three files match on the id |
| 17 | A symlink `$NOTES/link.md` pointing at `$NOTES/subagents.md` | deny — `realpath` on the directory resolves it, then the existence check fires |
| 18 | Payload with no `file_path` | deny |
| 19 | Malformed JSON on stdin | deny |
| 20 | `python3` absent from `PATH` | deny |
| 21 | `KNOWLEDGE_NOTES_DIR` unset, default path does not exist on this machine | deny for every notes write — `realpath` still resolves, and the promotion path simply never matches. Confirm this fails **closed**, not open |

Row 21 is the one to watch. A gate that silently stops applying when its target
directory moves is worse than no gate, because it looks installed.

**It was right, and the script failed it.** As written, `notes` was read from
`KNOWLEDGE_NOTES_DIR` and used without checking that the directory exists, so a write to
`<missing-dir>/migration-review.md` with a verdict present was **allowed** — the gate would have
permitted a second knowledge base to be created at whatever path the variable happened to hold.
Fixed by requiring `[ -d "$notes" ]` before any promotion is adjudicated; verdicts and patches
under `docs/research/` are unaffected, so the verifier can still do its work and only the
crossing into the base is stopped. Row 22 was added alongside it: a write to the real notes
directory while `KNOWLEDGE_NOTES_DIR` points elsewhere is also denied.

**Rows 19–20 cost a harness fix rather than a script fix**, and the distinction matters. The
first attempt tested "python3 absent" with `PATH=/nonexistent`, which makes `env bash`
unfindable too — the script never ran, and its silence was scored as a failure to deny. Tested
faithfully, with a PATH carrying `bash` but not `python3`, both scripts fail closed through the
`command -v python3` guard they already carried. That guard is the reason these two are sound,
and running it is what exposed that **`architect-rebuild-write-gate.sh`, installed earlier the
same day with 22/22, did not have it**: it died at `line 12: python3: command not found`, exit
127, no stdout — and a `PreToolUse` hook that emits nothing is not a denial, so the write would
have proceeded. That gate now carries the guard and a row 23 that checks it. A control table
this one had and that one lacked found a live fail-open in a wall already in service.

## Installation

1. `.claude/hooks/note-promotion.sh`, `chmod +x`.
2. Add to `.claude/agents/primary-source-verifier.md` frontmatter:

```yaml
hooks:
  PreToolUse:
    - matcher: "^(Write|Edit|NotebookEdit)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/note-promotion.sh"
```

3. Re-run `python3 .claude/validate/agents.py`.
4. Decide, as the owner of `/home/user/skills-repo`, whether `verified_by:` is an
   accepted addition to that base's note frontmatter. If not, the verdict path moves
   into the note body and `note-promotion` step 3 changes accordingly. Either way,
   this hook is unaffected: it matches on the file name, not on the content.

## What this does not do

- It does not read the verdict document. A verdict file containing one blank row
  passes. Whether the verdicts are honest is a case for the tester and a question
  for a reader, not for a gate.
- It does not stop the agent adding a claim of its own to a promoted note. That is
  a **containment case** for the tester's suite, and it is the most important one.
- It does not apply to any other agent. If a second agent is ever given write access
  to the knowledge base, this hook has to be attached there too, and the roster of
  who may write to that directory becomes a thing someone must own — which is
  backlog item B133, the registry, from the same decomposition that raised B130.
