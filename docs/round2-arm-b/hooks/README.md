# Hook proposal — migration-reviewer write gate

**Status: proposed, not installed.** Building an agent produces hook *proposals*; installing
a hook is a separate, human-approved act, and the field names and exit codes below must be
checked against the current Claude Code hooks documentation before anyone wires it up.

## What changed after the independent test

The tester's first finding was that this package claimed containment it did not have: the
agent held `Write`, and the only thing stopping it from overwriting a migration was a
sentence, because this gate is proposed and not installed. Its second was that the gate's
allow-branch matched `*/docs/reviews/*` as a substring, so
`docs/reviews/../../apps/api/prisma/migrations/0013/migration.sql` was **allowed** (exit 0,
reproduced).

Both are fixed, and the first is fixed by removing the capability rather than by guarding
it: **the agent no longer has `Write` at all.** It returns the review as its final message
and the caller files it. Containment is now entirely a property of the tool list — no
`Write`, no `Bash` — and needs no hook to be true. The gate below now canonicalizes with
`realpath -m` and prefix-matches the resolved path.

## Why this exists

The agent must never edit or apply the migration it is reviewing. Two enforcement points,
both mechanical:

1. **Absent tool.** `migration-reviewer` has no `Bash`. That is what makes "cannot apply a
   migration" true — no `prisma migrate deploy`, no `psql`, no shelling around the gate.
   It costs the agent `git diff`; it reads the files instead, which is enough for a static
   review. If anyone adds `Bash` back, this hook becomes decorative and the containment
   claim is void.
2. **This hook — only if someone re-adds `Write`.** The shipped agent has no `Write`, so the
   gate is currently defence in depth against a future edit to the tool list rather than the
   live enforcement. If anyone does want the agent to file its own report, add `Write` *and*
   install this gate in the same change, never one without the other.

A prose instruction ("do not edit the migration") is in the agent file too, for the model's
benefit — but it is not the enforcement, and it should not be treated as such. That
distinction is exactly what the first test of this package caught the package itself getting
wrong.

## The write surface this gate does not cover

The matcher below names `Write|Edit|MultiEdit|NotebookEdit`. In an environment with MCP
servers attached, tools such as `mcp__github__create_or_update_file`, `push_files` and
`actions_run_trigger` are writes and an action that applies a migration, and **none of them
match**. Whether an explicit `tools:` list also excludes MCP servers is a property of the
installed Claude Code configuration and was not verified here. Before relying on containment
in an environment with MCP write tools, verify that exclusion, and prefer a matcher of `.*`
with an allowlist over an enumeration of write-shaped tool names.

## Proposed settings

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
          { "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/migration-review-write-gate.sh" }
        ]
      }
    ]
  }
}
```

## Reconcile before installing

This repo already has a shared docs-only write gate (commit `e60a5fd`, "make the docs-only
write gate shared, not architect-specific"). It was not read while building this package —
the run was a deliberate ablation with `.claude/` off limits. **Before installing, check
whether the shared gate already covers this case and can simply be pointed at
`docs/reviews/`.** A second, near-duplicate gate script is worse than reusing the one that
exists.
