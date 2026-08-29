# Hook proposal — `architect-rebuild-write-gate`

**For:** `architect-rebuild`  **Event:** `PreToolUse`  **Matcher:** `Write`

Written by `agent-builder`, which is refused write access to `.claude/hooks/`.
**A human installs this.** An agent that can write its own wall does not have one.

**Installed and tested, 2026-08-29.** The script below was extracted from this file
programmatically rather than retyped, written to `.claude/hooks/`, and run against all
22 controls: **22 passed, 0 failed**. The harness is
`.claude/validate/architect-rebuild-gate-controls.sh` and it is mutation-tested — a
deny-everything mutant scores 19/22, an allow-everything mutant 3/22, and dropping the
`allowed + os.sep` guard fails case 9 alone. A harness that cannot fail proves nothing,
which is why those three runs are recorded here and not just asserted.

## What must be impossible, and why

1. **Writing source code, or anything outside `docs/`.** `architect-rebuild` decides
   the shape of a system it must not implement. If it can write `apps/`, `packages/`
   or the engine, the separation between deciding and building — which is the only
   reason to have a separate agent at all — is a sentence rather than a fact.
   Cost if it happened: a design agent silently reshaping the system it is meant to
   describe, and an audit that then finds its own edits and reports them as holding.

2. **Overwriting a file that already exists.** This is the one that does the real
   work. `Write` clobbers. `Edit` is already absent from the agent's `tools:`, but
   that buys nothing if `Write` can replace a file wholesale. Denying writes to
   existing paths is what makes the repository's own ADR convention — *"Supersede
   rather than edit: a changed decision gets a new number and the old one is
   marked"* — structural instead of aspirational. It also protects every prior
   findings list from being rewritten by a later pass with a different verdict.
   Cost if it happened: a decision register that can be edited retroactively, which
   is the same as having no register.

3. **Touching its own definition, its skills, hooks or settings.** All of
   `.claude/` is outside `docs/`, so rule 1 already covers it. It is enumerated
   separately anyway, because a gate whose only protection of itself is a side
   effect of another rule is one refactor away from being gone.

Nothing here is stated in the agent's prompt as a substitute. A "must never" in
prose is a request: warnings against a known bias failed in three studies and
backfired in a fourth, and eight anchoring-warning variants differing in content and
timing were all indistinguishable from no warning at all. `PreToolUse` runs before
every permission check, `bypassPermissions` included, and can only tighten.

**What this hook does not do.** It cannot tell whether the file being written is an
artefact `architect-rebuild` itself authored earlier in the session — so the
self-audit boundary in `design-claim-audit` step 0 remains a procedure, not a wall.
That gap is recorded in `docs/agent-spec-architect-rebuild.md` §3 and is the design's
weakest joint. If someone finds a predicate for it, this is where it belongs.

## The script

`.claude/hooks/architect-rebuild-write-gate.sh` — mode `0755`.

```bash
#!/usr/bin/env bash
# PreToolUse gate for the architect-rebuild agent.
# Allows Write only to new files under <repo>/docs/. Denies everything else,
# including any path that cannot be parsed or resolved. Always exits 0 and
# carries its decision in JSON on stdout.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"

payload="$(cat)"

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

# The repo root and the single allowed root, both fully resolved.
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
    # Matcher should prevent this. If the matcher is ever widened, fail closed.
    out("deny", f"this gate only adjudicates Write; refusing {tool!r}.")

ti = ev.get("tool_input")
if not isinstance(ti, dict):
    out("deny", "tool_input missing or not an object.")

path = ti.get("file_path")
if not isinstance(path, str) or path.strip() == "":
    out("deny", "no file_path in the payload.")

# Resolve WITHOUT requiring existence. realpath() on a non-existent leaf
# still resolves every existing component, which is what defeats traversal
# and symlinked parents alike.
if not os.path.isabs(path):
    path = os.path.join(root, path)
try:
    target = os.path.realpath(path)
except OSError as e:
    out("deny", f"could not resolve target path: {e}")

# Prefix-lookalike guard: os.sep terminated comparison, plus the root itself.
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

Two details that are load-bearing and easy to lose in a rewrite:

- **`os.path.realpath` on a non-existent leaf.** It resolves every component that
  does exist, so `docs/../apps/x.ts` collapses to `<root>/apps/x.ts` and is denied,
  and a symlinked `docs/` cannot be used to reach outside. `abspath`/`normpath` alone
  would not follow symlinks and would let a linked directory through.
- **`allowed + os.sep`.** `startswith(allowed)` alone would accept
  `<root>/docsfake/x.md`.

## Controls — all must be run before installing

Run each by feeding the JSON on stdin with `CLAUDE_PROJECT_DIR=/home/user/hello-world`.
`R` = `/home/user/hello-world`.

| # | Input `file_path` (tool_name `Write`) | Expected | Result |
|---|---|---|---|
| 1 | `docs/decisions/0022-example.md` (does not exist) | **allow** |  **pass** |
| 2 | `R/docs/decisions/0022-example.md` — absolute form of the same | **allow** |  **pass** |
| 3 | `docs/a/b/c/new-findings.md` — new nested path, parents absent | **allow** |  **pass** |
| 4 | `docs/ROADMAP.md` — exists | **deny** (create-only) |  **pass** |
| 5 | `docs/decisions/0000-adr-template.md` — exists | **deny** (create-only) |  **pass** |
| 6 | `apps/api/src/main.ts` | **deny** (outside root) |  **pass** |
| 7 | `docs/../apps/api/src/main.ts` — traversal through an allowed root | **deny** |  **pass** |
| 8 | `docs/../../etc/passwd` — traversal out of the repository | **deny** |  **pass** |
| 9 | `docsfake/x.md` — prefix lookalike | **deny** |  **pass** |
| 10 | `docs` — the allowed root itself | **deny** |  **pass** |
| 11 | `/etc/passwd` — absolute, outside the repository | **deny** |  **pass** |
| 12 | `.claude/agents/architect-rebuild.md` — the agent's own definition | **deny** |  **pass** |
| 13 | `.claude/hooks/architect-rebuild-write-gate.sh` — this hook | **deny** |  **pass** |
| 14 | `.claude/settings.json` | **deny** |  **pass** |
| 15 | payload with `tool_input: {}` — no path | **deny** |  **pass** |
| 16 | `file_path: ""` | **deny** |  **pass** |
| 17 | `file_path: 42` — wrong type | **deny** |  **pass** |
| 18 | stdin is `not json` | **deny** |  **pass** |
| 19 | stdin is empty | **deny** |  **pass** |
| 20 | `tool_name: "Bash"` with a command — matcher bypass rehearsal | **deny** |  **pass** |
| 21 | `CLAUDE_PROJECT_DIR` unset, otherwise valid | **deny** |  **pass** |
| 22 | a symlink `docs/out -> /tmp`, writing `docs/out/x.md` | **deny** |  **pass** |

Positive controls are not optional. Cases 1–3 are the only proof this is a gate and
not a wall: a script that denies everything passes all nineteen deny cases.

Case 20 deserves a note. The matcher is `Write`, so a `Bash` call should never reach
this script — the protection against `Bash` is that the tool is **absent from the
agent's `tools:` line**, not this hook. Case 20 exists so that if someone later
widens the matcher to `Write|Edit|Bash` thinking it makes the gate stronger, the
script fails closed instead of allowing a shell through an unhandled branch.

## Installation

1. Write the script to `/home/user/hello-world/.claude/hooks/architect-rebuild-write-gate.sh`. **Done** — extracted from the block above, not retyped.
2. `chmod 755` it. **Done.**
3. Run all 22 controls and fill the result column in this file. **Done** — 22/22, via `.claude/validate/architect-rebuild-gate-controls.sh`.
4. The agent's frontmatter carried `matcher: "Write"`. **Changed to `^Write$`.** A matcher is a
   substring search, so bare `Write` also matches `TodoWrite`; the gate would then fire on a
   call with no `file_path` and deny it. `architect-rebuild` does not hold `TodoWrite` today,
   so this was latent rather than live — but it is the same defect that shipped in two agents
   once already, and `.claude/validate/agents.py` only caught the alternation form. That rule
   is now widened to flag any unanchored matcher, with two positive controls behind it.

```yaml
hooks:
  PreToolUse:
    - matcher: "^Write$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/architect-rebuild-write-gate.sh"
```

5. Confirm `tools: Read, Grep, Glob, Write` in
   `.claude/agents/architect-rebuild.md` is unchanged. **If `Bash`, `Edit` or
   `Agent` has been added to that line, this hook is decorative** — `Bash` writes
   around it, `Edit` mutates around it, and `Agent` delegates around it to a
   subagent running under its own permissions. Re-check the line, not the hook.
