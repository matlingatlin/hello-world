# Hook proposal — `citation-provenance.sh`

**For:** `architect`  **Event:** `PreToolUse`  **Matcher:** `^(Write|Edit)$`
**Status:** proposal. A human installs it. The builder that wrote this may not
write `.claude/hooks/` or the `hooks:` frontmatter line, by design — an agent
that can attach a wall can remove one.

**This hook is optional and it is the smaller half of the repair.** Install it
only if the tester's runs show the prose rule failing. It is written now because
the alternative to writing it is pretending a paragraph is a control.

## What must be impossible, and why prose will not do it

The 2026-08-28 repair added two rules to the architect that are, as written,
**requests**:

1. *"Any number or study you are about to write into a document comes from the
   reference file, read at the time — not from memory."* This rule exists because
   a recalled figure put a **normative** value into ADR-0021 and into a shipped
   skill as though subjects had produced it.
2. *"`docs/as-built/` is absent; say so and mark conclusions `unverified` rather
   than quoting a `file:line` from a document you could not open."* (B128.)

The measured position on rules of this shape is unambiguous: eight
anchoring-warning variants, differing in content and timing, were **all**
indistinguishable from no warning; a specific warning about a specific bad
feature left the warned group the *most* fixated of three; a lecture explaining
that fixation exists moved 92.10% → 94.29%, p = .71. A sentence in a prompt is
the most thoroughly measured non-intervention in this literature.

What this hook makes impossible is narrow and mechanical: **writing a document
that cites a path which does not exist, or that reproduces one of two known-bad
figures.** It does not check that a citation is *correct* — nothing at this layer
can — only that it is not one of the two the repair has already had to undo, and
that a file being cited is a file that is there.

It is a `PreToolUse` hook because that fires before every permission check,
`bypassPermissions` included, and can only tighten.

## The script

```bash
#!/usr/bin/env bash
# citation-provenance.sh — PreToolUse on Write|Edit for the architect.
# Exit 0 always; the decision travels in JSON on stdout.
set -uo pipefail

deny() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"; exit 0; }
allow() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}\n'; exit 0; }

payload="$(cat)"
command -v jq >/dev/null 2>&1 || deny "citation-provenance: jq not available; cannot inspect payload"

echo "$payload" | jq -e . >/dev/null 2>&1 || deny "citation-provenance: unparseable payload"

root="${CLAUDE_PROJECT_DIR:-$PWD}"
path="$(echo "$payload" | jq -r '.tool_input.file_path // empty')"
[ -n "$path" ] || deny "citation-provenance: no file_path in payload"

# Content is whichever field this tool carries. Absent content is not a citation risk.
content="$(echo "$payload" | jq -r '.tool_input.content // .tool_input.new_string // empty')"
[ -n "$content" ] || allow

# 1 · The two figures this repo has already had to correct.
if printf '%s' "$content" | grep -Eq '\.078[^.]{0,40}\.468|from \.078 to \.468'; then
  deny "citation-provenance: '.078 to .468' is the corrected Fischhoff error. .468 is the NORMATIVE value; subjects answered .140. See .claude/skills/architecture-decision/references/evidence.md and the ADR-0021 erratum."
fi

# 2 · Backtick-quoted repo paths that do not exist.
missing=""
while IFS= read -r cited; do
  case "$cited" in
    ''|http*|*'<'*|*'*'*) continue ;;                 # placeholders, URLs, globs
  esac
  candidate="$root/$cited"
  [ -e "$candidate" ] || [ -e "$cited" ] || missing="$missing $cited"
done < <(printf '%s' "$content" \
  | grep -oE '`(docs|apps|packages|\.claude)/[A-Za-z0-9._/-]+`' \
  | tr -d '`' | sort -u)

[ -z "$missing" ] || deny "citation-provenance: cited path(s) do not exist:$missing. Cite what is there, or say the file is absent in prose rather than in a path reference. (docs/as-built/ is absent — backlog B128.)"

allow
```

Note two deliberate choices. The path check reads **only backtick-quoted paths**,
so prose such as "docs/as-built/ is absent" does not trip it while a citation
`` `docs/as-built/ARCHITECTURE-AS-BUILT.md:44` `` does. And an unparseable
payload or a payload with no path is **denied**, not allowed: a call whose scope
cannot be checked is a call that must not proceed.

## Controls — all must be run before installing

Every row is a command with an observed exit and an observed stdout, not a
judgement. **These have not been run** — the session that wrote this proposal had
no shell.

| # | Input | Expected |
|---|---|---|
| 1 | Write `docs/x.md` containing `` `docs/PRD.md` `` | **allow** — the positive control that proves this is a gate and not a wall |
| 2 | Write `docs/x.md` containing no backticked path at all | allow |
| 3 | Write `docs/x.md` citing `` `apps/api/src/auth/auth.guard.ts` `` | allow |
| 4 | Write `docs/x.md` citing `` `docs/as-built/ARCHITECTURE-AS-BUILT.md` `` | deny |
| 5 | Write `docs/x.md` containing the prose *"docs/as-built/ is absent"* unbackticked | allow |
| 6 | Write `docs/x.md` containing "moved from .078 to .468" | deny |
| 7 | Write `docs/x.md` containing the erratum wording (".468 is the normative value ... they answered .140") | **allow** — the correction must remain writable |
| 8 | Write citing `` `docs/../apps/api/README.md` `` (traversal through an allowed root) | allow if the file exists — this hook is about provenance, **not** write scope; scope is `docs-only-write.sh`'s job and both must be attached |
| 9 | Write citing `` `docsfake/PRD.md` `` (prefix lookalike) | deny — no such path |
| 10 | Payload with `file_path` and no content/new_string | allow |
| 11 | Payload with no `file_path` | deny |
| 12 | Malformed JSON on stdin | deny |
| 13 | `jq` absent from `PATH` | deny |
| 14 | A 200 KB document with 60 cited paths | allow, and record the wall-clock cost; if it is slow, the hook is worse than the defect |

Row 8 is the one to read carefully before installing: **this hook does not
replace `docs-only-write.sh` and does not overlap it.** If it is ever attached
instead of, rather than alongside, the write-scope hook, the wall is gone.

## Installation

1. `.claude/hooks/citation-provenance.sh`, `chmod +x`.
2. Add to `.claude/agents/architect.md` frontmatter, **as a second entry under
   the existing `PreToolUse` matcher, never replacing it**:

```yaml
hooks:
  PreToolUse:
    - matcher: "^(Write|Edit|NotebookEdit)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/docs-only-write.sh"
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/citation-provenance.sh"
```

3. Re-run the nine controls on `docs-only-write.sh` recorded in ADR-0021
   afterwards. Adding a second hook to a matcher is a change to the wall.

## What this does not do

- It cannot tell a correct citation from an incorrect one that points at a file
  which exists. The Fischhoff error would have passed rows 1–14 in its original
  home, because `references/evidence.md` did not exist yet to be cited.
- It does not fire on `Read`, so it cannot make the agent open a reference.
  **Nothing at this layer can.** Whether the agent opens `references/` when a
  step says to is a question for the tester's suite, not for a hook.
