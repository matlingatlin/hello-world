<!-- TEMPLATE — hook proposal. The builder writes this under docs/; a HUMAN
     installs it under .claude/hooks/. An agent that can write executable hooks
     can remove its own wall. -->

# Hook proposal — <name>

**For:** <agent>  **Event:** <PreToolUse | PostToolUse | …>  **Matcher:** `<…>`

## What must be impossible, and why

<Each impossibility, and what it would cost if it happened. A PreToolUse hook runs
before every permission check — bypassPermissions included — and can only tighten.
That is why it is here and not in the prompt.>

## The script

```bash
<complete and runnable. Read the payload from stdin, exit 0 always, carry the
decision in JSON on stdout. Resolve paths without requiring them to exist.
Deny — never silently allow — when the payload cannot be parsed or carries no path:
a call whose scope cannot be checked is a call that must not proceed.>
```

## Controls — all must be run before installing

| # | Input | Expected | Result |
|---|---|---|---|
| | a legitimate path in each allowed root | allow | |
| | an absolute form of the same | allow | |
| | a path outside the allowed roots | deny | |
| | traversal through an allowed root (`docs/../…`) | deny | |
| | a prefix-lookalike directory (`docsfake/`) | deny | |
| | a path outside the repository | deny | |
| | the agent's own definition | deny | |
| | the hook file itself | deny | |
| | a payload with no file path | deny | |
| | malformed input | deny | |

Positive controls are not optional. A gate that denies everything passes every
deny case; only the allow cases prove it is a gate rather than a wall.

## Installation

<Exact path, and the frontmatter line the agent needs.>
