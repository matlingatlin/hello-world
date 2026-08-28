# Hook proposal — migration-reviewer write gate

**Status: proposed, not installed.** Building an agent produces hook *proposals*; installing
a hook is a separate, human-approved act, and the field names and exit codes below must be
checked against the current Claude Code hooks documentation before anyone wires it up.

## Why this exists

The agent must never edit or apply the migration it is reviewing. Two enforcement points,
both mechanical:

1. **Absent tool.** `migration-reviewer` has no `Bash`. That is what makes "cannot apply a
   migration" true — no `prisma migrate deploy`, no `psql`, no shelling around the gate.
   It costs the agent `git diff`; it reads the files instead, which is enough for a static
   review. If anyone adds `Bash` back, this hook becomes decorative and the containment
   claim is void.
2. **This hook.** `Write` is on the agent's tool list because the review has to land
   somewhere. `migration-review-write-gate.sh` narrows that to `docs/reviews/` and denies
   everything else, naming migration and schema paths explicitly so the refusal is legible.

A prose instruction ("do not edit the migration") is in the agent file too, for the model's
benefit — but it is not the enforcement, and it should not be treated as such.

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
