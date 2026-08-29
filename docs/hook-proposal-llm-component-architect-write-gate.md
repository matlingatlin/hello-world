# Hook proposal — `llm-component-architect-write-gate.sh`

**For:** `llm-component-architect`  **Event:** `PreToolUse`  **Matcher:** `^Write$`

**Status: proposed, not installed.** A human installs it under `.claude/hooks/`.
The builder that wrote this agent cannot write executable hooks — an agent that
can write its own hooks can remove its own wall.

---

## Why this exists when a working gate is already referenced

The agent ships pointing at `.claude/hooks/architect-rebuild-write-gate.sh`, which
already implements this exact policy and is installed and executable. That was a
deliberate compromise, and it has a cost worth closing:

1. **The name lies.** The script is named for `architect-rebuild`. A human editing
   it for that agent silently changes a second agent's wall, and nothing in either
   file says so except a paragraph.
2. **`.claude/validate/agents.py:112-115` fails an agent whose `hooks:` command
   does not exist.** So shipping with the *proposed* path in frontmatter would fail
   the checker, and shipping with no `hooks:` block at all would leave the agent
   with no path wall while its body claimed one. Referencing the installed script
   was the only option that is both green and true.

Installing this file and swapping the frontmatter line closes the coupling.

## What must be impossible, and why

| Must be impossible | What it would cost |
|---|---|
| writing anywhere outside `docs/` | the agent's whole value is that its ruling has to survive contact with someone who can refuse it. An architect who can implement its own conclusion never gets that test |
| overwriting a file that already exists | a call table is a dated record. If it can be rewritten, a superseded ruling disappears and nobody can tell the record changed. Create-only makes *supersede, never edit* structural rather than polite |
| writing over `docs/` itself | a directory-shaped write is not a document |
| proceeding when the payload cannot be parsed, or carries no path | a call whose scope cannot be checked is a call that must not proceed |
| proceeding when `python3` is missing | **a `PreToolUse` hook that emits nothing is not a denial — the write proceeds.** A gate in this repo died at exit 127 with no stdout and silently allowed everything it was installed to stop |

`PreToolUse` runs before every permission check, `bypassPermissions` included, and
can only tighten. That is why this is a hook and not a paragraph.

**What it does not cover, stated rather than implied.** A path gate enforces
*where*, never *what*. It cannot tell a ruling read at `file:line` from one
inferred from a function's name, and it cannot tell a fetched price from a
remembered one. And a hook is **conditional in a way an absent tool is not**: hooks
do not load in a non-interactive session, where the workspace is untrusted. In that
mode this gate is not weaker — it is absent, and the agent's only remaining walls
are its four missing tools (`Bash`, `Edit`, `WebSearch`, `Agent`), which hold
everywhere.

## The script

```bash
#!/usr/bin/env bash
# PreToolUse gate for the llm-component-architect agent.
# Allows Write only to NEW files under <repo>/docs/. Denies everything else,
# including any path that cannot be parsed or resolved. Always exits 0 and
# carries its decision in JSON on stdout.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"

payload="$(cat)"

# python3 is the whole adjudicator below. Without it the script would die with no
# stdout, and a PreToolUse hook that emits nothing is not a denial — the write
# proceeds. Fail closed, in shell, before the interpreter is reached.
command -v python3 >/dev/null 2>&1 || {
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"llm-component-architect-write-gate: python3 unavailable; the payload cannot be inspected, so its scope cannot be checked."}}'
  exit 0
}

PROJECT_DIR="$PROJECT_DIR" payload="$payload" python3 - <<'PY'
import json, os, sys

def out(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)

project = os.environ.get("PROJECT_DIR") or ""
if not project:
    out("deny", "CLAUDE_PROJECT_DIR is not set; scope cannot be established.")

try:
    root = os.path.realpath(project)
    allowed = os.path.realpath(os.path.join(root, "docs"))
except OSError as e:
    out("deny", f"could not resolve project root: {e}")

raw = os.environ.get("payload") or ""
try:
    ev = json.loads(raw)
except Exception:
    out("deny", "unparseable hook payload; a call whose scope cannot be checked must not proceed.")

if not isinstance(ev, dict):
    out("deny", "hook payload is not an object.")

tool = ev.get("tool_name")
if tool != "Write":
    # The matcher should prevent this. If the matcher is ever widened, fail closed.
    out("deny", f"this gate only adjudicates Write; refusing {tool!r}.")

ti = ev.get("tool_input")
if not isinstance(ti, dict):
    out("deny", "tool_input missing or not an object.")

path = ti.get("file_path")
if not isinstance(path, str) or path.strip() == "":
    out("deny", "no file_path in the payload.")

# Resolve WITHOUT requiring existence. realpath() on a non-existent leaf still
# resolves every existing component, which defeats traversal and symlinked
# parents alike. realpath() on the whole path would require it to exist.
if not os.path.isabs(path):
    path = os.path.join(root, path)
try:
    target = os.path.realpath(path)
except OSError as e:
    out("deny", f"could not resolve target path: {e}")

# Prefix-lookalike guard: compare with the separator, and handle the root itself.
# startswith(allowed) alone accepts docsfake/.
if target != allowed and not target.startswith(allowed + os.sep):
    out("deny", f"outside the only writable root ({allowed}): {target}")

if target == allowed:
    out("deny", "refusing to write over the docs directory itself.")

# Create-only. lexists, not exists: a dangling symlink is still an existing name.
if os.path.lexists(target):
    out("deny",
        "that file already exists. This agent creates; it does not edit. "
        "Supersede it under a new number, or hand the change to a human.")

out("allow", f"new file under {allowed}")
PY
```

## Controls — all must be run before installing

**Positive controls are not optional.** A script that denies everything scores full
marks on every deny case; only the allow rows prove it is a gate rather than a
wall.

| # | Input (`tool_input.file_path`, `tool_name: Write`) | Expected | Result |
|---|---|---|---|
| 1 | `docs/model-calls/0001-scio-engine.md` (new) | **allow** | |
| 2 | `${CLAUDE_PROJECT_DIR}/docs/model-calls/0001-scio-engine.md` (new, absolute) | **allow** | |
| 3 | `docs/a/deeply/nested/new-file.md` (new, nested) | **allow** | |
| 4 | `docs/COSTS.md` (exists) | deny — create-only | |
| 5 | `docs/agent-registry.md` (exists) | deny — create-only | |
| 6 | `docs` | deny — the directory itself | |
| 7 | `apps/engine/core/sandbox.py` | deny — outside `docs/` | |
| 8 | `docs/../apps/engine/main.py` | deny — traversal through an allowed root | |
| 9 | `docsfake/notes.md` | deny — prefix lookalike | |
| 10 | a symlink at `docs/link` pointing to `/tmp`, then `docs/link/x.md` | deny — symlinked parent resolves outside | |
| 11 | `/etc/passwd` | deny — outside the repository | |
| 12 | `.claude/agents/llm-component-architect.md` | deny — its own definition | |
| 13 | `.claude/hooks/llm-component-architect-write-gate.sh` | deny — the hook itself | |
| 14 | `.claude/settings.json` | deny — settings | |
| 15 | payload `{"tool_name":"Write","tool_input":{}}` | deny — no path | |
| 16 | payload `not json` | deny — malformed | |
| 17 | empty stdin | deny — malformed | |
| 18 | `{"tool_name":"Edit","tool_input":{"file_path":"docs/x.md"}}` | deny — wrong tool, fail closed | |
| 19 | `CLAUDE_PROJECT_DIR` unset | deny — scope cannot be established | |
| 20 | `PATH` stripped of `python3`, case 1 re-run | deny — interpreter absent | |

**Then mutate the script and re-run.** A harness that cannot fail proves nothing.

| Mutant | Must score |
|---|---|
| every branch replaced by `out("deny", ...)` | fails exactly cases 1, 2, 3 |
| body replaced by `exit 0` with no stdout | fails every deny case, 4–20 |
| remove the `os.path.lexists` check | fails exactly 4, 5 |
| remove the `allowed + os.sep` guard | fails exactly 9 |
| remove the `command -v python3` guard | fails exactly 20 |

**Keep the harness as a file, not a table of results in this document.** A recorded
pass is a claim about a test; it goes stale the first time the script changes and
cannot tell you it has. The existing controls in
`.claude/validate/architect-rebuild-gate-controls.sh` cover the same policy and are
the model to copy.

## Installation

1. Write the script above to `.claude/hooks/llm-component-architect-write-gate.sh`.
2. `chmod +x` it. **`.claude/validate/agents.py` fails a hook that is not
   executable**, so this is not optional.
3. Run the controls. Do not install on a table of expected results.
4. In `.claude/agents/llm-component-architect.md`, change the one line:

   ```
   command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/architect-rebuild-write-gate.sh"
   ```
   to
   ```
   command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/llm-component-architect-write-gate.sh"
   ```
5. In that agent's §2, change the two sentences naming the shared hook and its
   coupling; the coupling no longer exists once this is installed, and a body that
   still describes it becomes a currency defect.
6. Re-run `python3 .claude/validate/agents.py`.
