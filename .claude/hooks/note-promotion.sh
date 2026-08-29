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
# A gate whose target directory has moved is worse than no gate: it looks installed
# while permitting a second knowledge base to be created somewhere else. If the notes
# directory is not there, no promotion is adjudicable, so none is allowed.
[ -d "$notes" ] || deny "note-promotion: the knowledge base directory ($notes) does not exist. Promotion cannot be adjudicated against a base that is not there; set KNOWLEDGE_NOTES_DIR or restore it. Verdicts and patches under docs/research/ are unaffected."

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
  # A file that merely exists is not a verdict. An independent tester unlocked a real
  # promotion with a 28-byte file whose whole content was a heading, because this check
  # was [ -f ] alone. Requiring a ruling token stops an empty stub and a stray fixture.
  # It stops nothing that is trying: a fabricated verdict satisfies it. The gate enforces
  # the SEQUENCE, never the honesty of the ruling — see the spec's weakest-joint section.
  grep -qE '\b(supported|not-supported|not-in-source|source-unreachable|not-checkable)\b' \
    "$absroot/docs/research/verdicts/$id.md" 2>/dev/null \
    || deny "note-promotion: docs/research/verdicts/$id.md carries no ruling. A verdict document rules every claim supported, not-supported, not-in-source, source-unreachable or not-checkable; a file that only names the id is a placeholder, not a verdict."
  [ -e "$abs" ] && deny "note-promotion: $id.md already exists in the knowledge base. This pipeline creates notes; it does not rewrite them. An extension is a patch under docs/research/patches/$id.md that a human applies."
  allow
fi

deny "note-promotion: primary-source-verifier writes only docs/research/verdicts/<id>.md, docs/research/patches/<id>.md, and a NEW note in the knowledge base behind an existing verdict. This path is none of those. It does not edit drafts: a verifier that can sharpen a claim before ruling on it is ruling on its own claim."
