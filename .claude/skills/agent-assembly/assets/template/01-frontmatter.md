# Frontmatter — every field, and how to decide it

Fifteen fields. Six you will almost always set, nine you almost never should —
but "never considered" and "ruled out" are different states, and the spec must
say which. **Write a line for every field you leave out.**

Provenance: **[DOC]** = in Anthropic's documentation, binding.
**[MEASURED]** = measured in this project, cited. **[HOUSE]** = our convention,
no measurement behind it — follow it, but do not defend it as a fact.

---

## `name` — required

**[DOC]** Lower-case, hyphenated. Must not contain "claude" or "anthropic" —
reserved.

Name it for **the job**, not the role. `primary-source-verifier`, not
`researcher`. `agent-fitness-review`, not `quality-guy`. The test: could a second
agent plausibly claim this name? If yes, the name describes a domain rather than
a job, and the collision is waiting to happen.

**A name that covers fewer jobs than the agent does is the cheapest lie you can
tell.** If you cannot name it without listing two verbs, you have two agents.

---

## `description` — required, and the one that matters most

See `02-description.md`. It is long because this field decides whether the agent
is ever invoked.

---

## `tools` — optional in the schema, **mandatory here**

**[DOC]** Omitting it inherits **every tool available to subagents**. Not none.

This is the most dangerous line you can fail to write, and it fails silently — an
agent meant to be read-only quietly holds `Bash`, `Write` and `Edit`.

**How to choose.** Start from the artefact and add only what producing it needs.
Then ask, for each tool you kept: *what is the worst thing this agent could do
with it if it misunderstood its job?* If that answer is bad and the tool is not
load-bearing, drop it.

Four absences are worth naming because each buys something specific:

| Absent | What it buys |
|---|---|
| `Bash` | nothing executes; a write gate cannot be walked around with `echo >` |
| `Edit` | it can create but not rewrite — the record cannot be edited retroactively |
| `WebSearch` (keeping `WebFetch`) | it can open a named URL but cannot go find a source that agrees. **This is how a verifier stays a verifier**: with search, an unsupported claim gets "confirmed" against something else — corroboration wearing verification's clothes |
| `Agent` | it cannot hand its judgement to a delegate, or reach past its own tool list |

**[DOC]** Two filters narrow the pool before your list is even considered: nine
tools are removed from every subagent *even when listed*, and background runs get
a further reduced built-in set — **whether inherited or listed**. Listing a tool
does not protect it. Forks skip both filters.

---

## `model` — set it deliberately, and say why

**[DOC]** Default `inherit`. Accepts `sonnet` / `opus` / `haiku` / `fable` or a
full model id.

**We have no measurement here.** So the rule is not "use X" — it is: **write one
sentence saying why**, in the spec. `inherit` is a legitimate answer; `inherit`
because the last agent said `inherit` is not.

The three cases where a pin is worth arguing for:

- the job is **mechanical and high-volume** (extraction, classification, a
  sweep over many files) — a smaller model may do it at a fraction of the cost
- the job is **judgement under ambiguity** where being wrong is expensive — pin
  up rather than inherit down
- **reproducibility matters** — an eval baseline that drifts when the caller's
  model changes is not a baseline

Pinning costs you: the agent stops following the caller's model upgrades, and a
pinned id can be deprecated under you. Say which you accepted.

---

## `skills` — at most three

**[DOC]** Preloads the full content of each named skill into the agent's context
at startup. Cannot preload a skill marked `disable-model-invocation: true`.

**[MEASURED]** 1–3 preloaded modules ≈ **+19.0pp**; 4 or more ≈ **+10.1pp**. The
cap is not a context budget — it is a quality finding. More is measurably worse.

**[MEASURED]** On compaction, skills are re-attached at 5,000 tokens each against
a 25,000 shared budget, most recent first, **truncated silently**.

**[HOUSE]** A fourth function is the signal you have two agents, not a bigger
one. That reading of the measurement is ours; the measurement is not.

Each preloaded skill must be a **numbered procedure that ends in an artefact**.
A skill that is a pile of advice belongs in `references/`, read at the step that
needs it, costing nothing until then.

---

## `hooks` — the wall, when a wall is possible

**[DOC]** `PreToolUse` runs **before every permission check**, including
`bypassPermissions`, and can only tighten.

**[MEASURED]** The matcher is a **substring** search. `"Write"` also matches
`TodoWrite`; `"Edit"` also matches `NotebookEdit`. **Always anchor:
`^(Write|Edit|NotebookEdit)$`.**

**[MEASURED]** Hooks do **not** load in a non-interactive session — the workspace
is untrusted there. So a hook is a real mechanism in an interactive session and
**nothing at all** in a scripted one. An absent tool holds in both.

**Consequence for the design:** where the same protection can be had by removing
a tool, remove the tool. Use a hook for what a tool boundary cannot express — a
path scope, a create-only rule, an ordering requirement.

See `04-wall.md`.

---

## The nine you will usually leave unset — and must still decide

| Field | What it does | When it earns its place |
|---|---|---|
| `disallowedTools` | subtractive deny-list | when you inherit broadly on purpose and need to carve out two tools. Prefer an explicit `tools:` allow-list |
| `permissionMode` | the mode the agent runs under | when the agent must run unattended, or must be forced to plan first |
| `maxTurns` | caps the run **[DOC]** — at the limit it returns partial output and is resumable | when a loop is plausible and an unbounded run is expensive |
| `mcpServers` | which MCP servers it can reach | when the job needs one specific server and nothing else |
| `memory` | `user`/`project`/`local`; **[DOC]** preload is first 200 lines or 25 KB | when the agent must accumulate across runs. Rare, and it breaks reproducibility |
| `background` | runs concurrently, **[DOC]** reduced built-in tool set, `Agent` not in it | when the caller should not block. Re-check the tool surface: removal applies whether inherited or listed |
| `effort` | reasoning effort | when the job is either trivially mechanical or genuinely hard, and the default is wrong for it |
| `isolation: worktree` | its own git worktree | when it writes and must not collide with the caller's tree |
| `color` | tab colour | cosmetic |

**Write one line per unset field in the spec.** "Not needed — this agent never
writes" is a decision. Silence is not.
