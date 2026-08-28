# Hook proposal — migration-reviewer-scope

> **DO NOT INSTALL AS WRITTEN.** An independent test dispatch found two HIGH
> defects in the fallback branch of the script below, after this document was
> finished. Both are in the pure-shell path that runs when `realpath -m` is
> unavailable — which is the **live** path on macOS, where BSD `realpath` has no
> `-m`, so this is not dead code:
>
> 1. **Non-terminating loop.** Any path with two or more `/./` segments loops
>    forever (the `%`/`#` halves overlap and the string grows). Three inputs were
>    killed at an 8-second timeout.
> 2. **Symlink escape.** The fallback is purely lexical, so with a symlink inside
>    the review root, writes to `/etc/passwd` and to
>    `apps/api/prisma/schema.prisma` return **allow**. The GNU branch denies both.
>
> Also found: a terminal `..` is allowed in the fallback; with `CLAUDE_PROJECT_DIR`
> unset the root follows `$PWD`, which allowed a write under `/tmp/docs/...`; and
> a two-object JSON stream yields `allow`.
>
> The control table below is real and reproduces exactly — the test dispatch re-ran
> all 13 cases and got the documented verdict every time. **It only ever exercises
> the GNU branch.** That is the lesson worth keeping from this document: a control
> table that covers one of two code paths reads exactly like one that covers both.
>
> Repair before installing: bound the loop, make the fallback **deny** when it
> cannot resolve symlinks, and re-run the controls on both branches with symlink,
> `/./` and terminal-`..` rows added. Details in `../EVALS-migration-reviewer.md`
> (H1, H2, H3, A4-X1).


**For:** `migration-reviewer`  **Event:** `PreToolUse`
**Matcher:** `^(Write|Edit|NotebookEdit)$`
**Install at:** `.claude/hooks/migration-reviewer-scope.sh` — **by a human.** An agent
that can write executable hooks can delete its own wall.

## What must be impossible, and why

A `PreToolUse` hook runs before every permission check — `bypassPermissions`
included — and can only tighten. That is why each line below is here and not in the
agent's prompt: warnings against a known bias failed in three studies and backfired
in a fourth, and eight warning variants differing in content and timing were all
indistinguishable from no warning.

| Must be impossible | Cost if it happened |
|---|---|
| Editing the migration under review (`apps/api/prisma/**`) | The reviewer becomes the author of the fix, and then grades its own work. Independent testers found 81 defects in this repo's own library precisely because that separation was kept. |
| Editing any source file or any other doc | A review is a document. A reviewer that edits the system it reviews is an unreviewed change. |
| Editing its own definition, its skills, this hook, or `.claude/settings*.json` | Whatever else it is denied becomes advisory the moment it can rewrite the denial. |
| Escaping the review root by `../`, by an absolute path, or by a prefix lookalike (`migrationsfake/`) | A gate that only checks the string it was handed is not a gate. |

The gate is only real because **`Bash` is absent from the agent's tool list**. A
path-scoped write gate next to `Bash` is decorative — every deny is one `echo >`
away from irrelevant.

## The script

```bash
#!/usr/bin/env bash
# PreToolUse gate for the migration-reviewer agent.
# Writes are permitted ONLY under the review root. Everything else is denied,
# including the migration under review and the agent's own definition.
# Exits 0 always; the decision travels as JSON on stdout.
set -uo pipefail

payload="$(cat)"

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}
allow() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"within the review root"}}\n'
  exit 0
}

command -v jq >/dev/null 2>&1 || deny "gate cannot run: jq is not installed"

path="$(printf '%s' "$payload" | jq -er '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)" \
  || deny "unparseable hook payload: a call whose scope cannot be checked does not proceed"
[ -n "$path" ] || deny "no file path in payload: a call whose scope cannot be checked does not proceed"

project_dir="${CLAUDE_PROJECT_DIR:-$PWD}"
case "$path" in
  /*) abs="$path" ;;
   *) abs="$project_dir/$path" ;;
esac

# Resolve without requiring the file to exist: realpath -m, else a pure-shell fold.
if resolved="$(realpath -m -- "$abs" 2>/dev/null)"; then :; else
  resolved="$abs"
  while [ "$resolved" != "${resolved%/./*}" ]; do resolved="${resolved%/./*}/${resolved#*/./}"; done
  while :; do
    case "$resolved" in
      */../*|*/..) prefix="${resolved%%/../*}"; suffix="${resolved#*/../}"
                   [ "$prefix" = "$resolved" ] && break
                   resolved="${prefix%/*}/$suffix" ;;
      *) break ;;
    esac
  done
fi

root="$(realpath -m -- "$project_dir/docs/reviews/migrations" 2>/dev/null || printf '%s' "$project_dir/docs/reviews/migrations")"

# Trailing separator: "docsfake/" must not match "docs/".
case "$resolved/" in
  "$root"/*) allow ;;
  *) deny "writes are confined to docs/reviews/migrations/; refused: $resolved" ;;
esac
```

## Controls — run 2026-08-28 against the script above

Run with `CLAUDE_PROJECT_DIR=/home/user/hello-world`, the script fed each payload on
stdin, verdict read from `.hookSpecificOutput.permissionDecision`. Results are the
observed output, not an expectation restated.

| # | Input | Expected | Result |
|---|---|---|---|
| 1 | `docs/reviews/migrations/0013.md` (relative) | allow | **allow** |
| 2 | the absolute form of the same path | allow | **allow** |
| 3 | `docs/PRD.md` — allowed-looking, outside the root | deny | **deny** |
| 4 | `apps/api/prisma/migrations/0012_job_spend/migration.sql` — the artefact under review | deny | **deny** |
| 5 | `docs/reviews/migrations/../../../apps/api/prisma/schema.prisma` | deny | **deny** |
| 6 | `docs/reviews/migrationsfake/x.md` — prefix lookalike | deny | **deny** |
| 7 | `/etc/passwd` — outside the repository | deny | **deny** |
| 8 | `.claude/agents/migration-reviewer.md` — its own definition | deny | **deny** |
| 9 | `.claude/hooks/migration-reviewer-scope.sh` — this hook | deny | **deny** |
| 10 | payload with no file path | deny | **deny** |
| 11 | `not json at all` | deny | **deny** |
| 12 | `NotebookEdit` with `notebook_path` inside the root | allow | **allow** |
| 13 | empty string path | deny | **deny** |

Cases 1, 2 and 12 are the positive controls, and they are not optional: a gate that
denied everything would pass all ten deny cases. They are what prove this is a gate
and not a wall.

**Known limit, stated rather than discovered later:** the gate reads
`tool_input.file_path` and `tool_input.notebook_path`. A future tool that carries a
write target under a different key would fall to the no-path branch, which denies —
the safe direction, but it means such a tool is blocked rather than scoped, and the
gate needs a line adding before that tool is granted.

## Installation

1. Save the script to `.claude/hooks/migration-reviewer-scope.sh`, `chmod +x`.
2. Add to `.claude/agents/migration-reviewer.md` frontmatter (a **privilege line** —
   a human writes it):

```yaml
hooks:
  PreToolUse:
    - matcher: "^(Write|Edit|NotebookEdit)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/migration-reviewer-scope.sh"
```

3. Re-run the control table above after installing. A gate that was never exercised
   in place is an assumption.
