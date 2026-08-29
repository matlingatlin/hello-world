# The wall — deciding what must be impossible, and with what

A wall is not a warning. It is the set of things the agent **cannot** do, however
it reasons.

---

## The ladder, strongest first

**1 · An absent tool.** Unconditional. Holds in every session, interactive or
scripted, foreground or background. Cannot be argued around, misparsed, or
skipped because a directory moved.

**2 · A `PreToolUse` hook.** **[DOC]** Runs before every permission check,
`bypassPermissions` included, and can only tighten. Expresses what a tool
boundary cannot: a path scope, a create-only rule, an ordering requirement.

**[MEASURED]** But it is **conditional**: hooks do not load in a non-interactive
session, where the workspace is untrusted. In that mode the hook is not a weaker
wall — it is **absent**. Anything that must hold in a scripted run belongs at
rung 1.

**3 · A sentence in the prompt.** **[MEASURED]** Not a wall. Warnings against a
known bias failed in three studies and backfired in a fourth; eight
anchoring-warning variants were all indistinguishable from no warning.

**Rule: take the highest rung that expresses the constraint.** If removing a tool
gets you the same protection as a hook, remove the tool.

---

## What each absence actually buys

| Absent | Buys | Costs |
|---|---|---|
| `Bash` | nothing executes; a write gate cannot be walked around | it cannot run a checker, so verification must be delegated or handed up |
| `Edit` | creates but cannot rewrite; the record cannot be edited retroactively | corrections become new files, which is usually what you wanted |
| `Write` | reads only | it must return findings in its reply, which the caller then has to place |
| `WebSearch`, keeping `WebFetch` | it can open a URL a document names but cannot go find a source that agrees — **this is what keeps a verifier a verifier** | it cannot research; give it search only if researching is the job |
| `Agent` | cannot delegate its judgement or reach past its own tool list | it cannot dispatch a test; that step must be handed up |

---

## Writing the hook, when you need one

**Anchor the matcher.** **[MEASURED]** The matcher is a substring search:
`"Write"` also matches `TodoWrite`, `"Edit"` also matches `NotebookEdit`. Use
`^(Write|Edit|NotebookEdit)$`.

**Fail closed, in shell, before the interpreter.** If the script's logic is in
Python, guard it:

```bash
command -v python3 >/dev/null 2>&1 || {
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"interpreter unavailable; scope cannot be checked."}}'
  exit 0
}
```

**[MEASURED]** A `PreToolUse` hook that emits nothing is **not** a denial — the
write proceeds. A gate here died at exit 127 with no stdout and silently allowed
everything it was installed to stop.

**Resolve the parent, re-join the basename.** `realpath` on the whole path
requires it to exist; `realpath(dirname)` plus the basename defeats both `..`
traversal and a symlinked directory.

**Compare with the separator.** `startswith(allowed)` accepts `docsfake/`.
Compare against `allowed + os.sep`, and handle the root itself.

**Prefer create-only over content inspection.** Content gates were tried here and
failed twice: five YAML spellings got past one, and — worse — it **denied a
compliant file while allowing one that omitted `tools:`**, inverting the safety it
existed to provide. Denying writes to paths that already exist is structural and
cannot be spelled around.

---

## Controls — the part that makes it real

A wall nobody ran is a claim about a wall.

**Positive controls first.** At least one allow case per legal shape. Without
them, a script that denies everything scores full marks on every deny case.

**Then the deny cases**, at minimum: outside the scope; a prefix lookalike
(`docsfake/`); traversal through an allowed root; a symlinked parent; the hook
itself; the settings file; the agent's own definition; a payload with no path;
malformed JSON; empty stdin; the interpreter absent.

**Then mutate the script and re-run.** A harness that cannot fail proves nothing:

| Mutant | Must score |
|---|---|
| deny everything | fails exactly the positive controls |
| emit nothing (`exit 0`) | fails every deny case |
| remove one guard | fails exactly the case that guard exists for |

Keep the harness as a file, not a table of results in a document. **A recorded
pass is a claim about a test; it goes stale the first time the script changes and
cannot tell you it has.**

---

## Say what the wall does not cover

Every wall has a shape, and the shape implies a boundary that is not there.

A path gate enforces **where**, never **what**. An ordering gate enforces **that a
document exists**, never that it was written honestly. Name the gap in §2 of the
body, in the agent's own words — because the agent is the only thing left
standing where the mechanism stops.
