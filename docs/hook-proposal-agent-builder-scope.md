# Hook proposal — `agent-builder-scope` (written after the fact)

**For:** `agent-builder`  **Event:** `PreToolUse`  **Matcher:** `^(Write|Edit|NotebookEdit)$`

**This document is retroactive, and that is the finding it opens with.**

This repository's own loop requires that a hook ships as a proposal under `docs/` which a
human installs, because *an agent that can write its own wall does not have one*. Seven
hooks are installed here and four proposals existed. The missing one was
`agent-builder-scope.sh` — **the wall binding the agent that enforces the rule**.
`git log --all --name-only | grep hook-proposal` confirms it never existed at any commit.

Found by a P5 absence audit on 2026-08-29 (A-04), together with A-05: four of seven hooks
had no re-runnable control harness, and this was one of them. Its 32 cases lived only as a
prose results table inside `.claude/skills/agent-assembly/evals.md` — a claim about a test
rather than a test.

The script is unchanged by this document. What is new is the harness,
`.claude/validate/agent-builder-scope-controls.sh`, and the reasoning below, which had
never been written down anywhere.

## What must be impossible, and why

1. **Writing source code, or anything outside `docs/`, `.claude/agents/` and
   `.claude/skills/`.** `agent-builder` decides what agents should exist. If it can write
   `apps/` or the engine, the separation between designing the roster and building the
   product is a sentence rather than a fact.

2. **Writing `.claude/hooks/**`.** A builder that writes executable hooks can delete its
   own wall, and can install a wall on an agent it is creating that exempts itself. Hooks
   are emitted as proposals; a human installs them. *This document is the rule applied to
   the rule's own enforcer, four days late.*

3. **Writing `.claude/settings*.json`.** Permissions and enabled plugins. A gate that
   protects the filesystem but not the file granting filesystem permissions is decorative.

4. **Writing its own toolchain** — `agent-builder.md`, `agent-shape/`, `agent-baseline/`,
   `agent-assembly/`. It does not modify itself.

5. **Writing over anything under `.claude/` that already exists.** This is the rule that
   does the real work, and it was bought expensively. Content inspection was tried first
   and failed twice: an independent tester found five YAML spellings past it and a
   two-step `Edit` around it, and — worse — the content gate **denied a compliant agent
   file while allowing one that omitted `tools:`**, inverting the safety it existed to
   provide. Create-only closes structurally what content inspection could not: every one
   of the three escapes found (deleting a neighbour's wall, widening a tool surface,
   renaming a key across two innocent edits) required a file that was already there.

## What this hook deliberately does not do

**It is content-blind.** It reads the path and nothing else. A *new* agent file with
`tools:` omitted — which `CLAUDE.md` calls the most dangerous line you can fail to write,
because omitting it inherits every tool rather than none — **is allowed through**. An
auditor executed exactly that write on 2026-08-29 and the gate returned ALLOW.

That is accepted, not overlooked, and rule 5 is why: the last content gate here inverted
its own safety. The defence is downstream and mechanical — `.claude/validate/agents.py`
fails an omitted `tools:` by name, and `agent-assembly` step 5 now runs it. The cost is
that the gate is a scope boundary and never a review, and `agent-builder.md` now says so
in those words.

**It cannot tell whether the agent being created should exist.** No path gate can.

## The script

`.claude/hooks/agent-builder-scope.sh` — mode `0755`, installed. Two details are
load-bearing and easy to lose in a rewrite:

- **`realpath(dirname)` re-joined with the basename.** Resolving the whole path would
  require it to exist; resolving only the parent defeats both `..` traversal and a
  symlinked directory, which is why case `RS` passes.
- **`rel=$(python3 …) || deny`.** `deny()` is pure `printf` with no interpreter
  dependency, so when `python3` is absent the substitution fails and the `||` fires. That
  is the difference between this script and `architect-rebuild-write-gate.sh`, which put
  its `deny` *inside* the Python and therefore died at exit 127 with no stdout — and a
  `PreToolUse` hook that emits nothing is not a denial. `evals.md` asserted this script
  fails closed; case `PY` now measures it.

## Controls

`.claude/validate/agent-builder-scope-controls.sh` — **29 cases, 29 pass**, run
2026-08-29.

| Group | Cases | Point |
|---|---|---|
| Positive | A, B, C, D | without these it is a brick wall, not a gate |
| Outside the roots | E, G, H, W, Z, AD, AE, AA | including `.mcp.json` and `.git/hooks/`, two escape hatches the design never names and the default branch catches |
| Walls, settings, toolchain | F, J, M, I, N, N2 | |
| Create-only | O, O2, O3 | **O is a regression test for a real HIGH defect**: before create-only, `agent-builder` could freely rewrite any *other* agent in the repo, including the `hooks:` block carrying that agent's wall |
| Malformed | K, L, V, T, EM | a call whose scope cannot be checked must not proceed |
| Other shapes | X | `NotebookEdit` uses `notebook_path`, not `file_path` |
| Environment | RS, PY | symlinked directory; `bash` present and `python3` absent |

**Mutation-tested**, because a harness that cannot fail proves nothing:

| Mutant | Score | Reads as |
|---|---|---|
| deny everything | 25/29 | fails exactly the four positive controls |
| silent (`exit 0`, no stdout) | 4/29 | the fail-open shape — fails all 25 deny cases |
| create-only removed | 26/29 | fails exactly O, O2, O3 |

## Installation

Already installed, in `.claude/agents/agent-builder.md` frontmatter:

```yaml
hooks:
  PreToolUse:
    - matcher: "^(Write|Edit|NotebookEdit)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/agent-builder-scope.sh"
```

The matcher is anchored. Unanchored, `Write` also matches `TodoWrite` — the exact defect
that shipped in two agents here once, and that `.claude/validate/agents.py` now fails.

**Confirm `tools:` on that agent still excludes `Bash`.** If `Bash` is ever added, this
hook is decorative: a shell writes around it. That check is on the tools line, not on the
hook.
