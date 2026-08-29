# Patch — x2-subagent-limits → `subagents.md`

**Target note:** `/home/user/skills-repo/knowledge/notes/subagents.md` (exists; `status: verified`)
**Verdict document:** `/home/user/hello-world/docs/research/verdicts/x2-subagent-limits.md`
**Draft:** `/home/user/hello-world/docs/research/drafts/x2-subagent-limits.md`
**Produced by:** `primary-source-verifier` · 2026-08-29 · **a human applies this; nothing here was written to the base**

## Gate checks (note-promotion §1)

| Check | Result |
|---|---|
| Verdict document exists, row count equals draft's claim count | `docs/research/verdicts/x2-subagent-limits.md` · **38 rows = 38 claims** ✓ (the draft's own count line says 35; it is wrong — verdict row X2) |
| Target note does not already exist | **It does** — `/home/user/skills-repo/knowledge/notes/subagents.md`. So this is an extension, and §5's patch, **not** a write. No file was written to `/home/user/skills-repo/` |
| I did not draft it | ✓ The draft names no author but states at §6 that the verifier "did not author" it; I hold no tool that writes drafts and produced none in this session |

## What crossed, by verdict (note-promotion §2)

35 of 38 claim rows `supported`; 3 `source-unreachable`; 0 `not-supported`, 0
`not-in-source`, 0 `not-checkable`. **No claim in the draft's table was contradicted by
its source.** The three failures are all the same failure: the Errors page never
returned its cited sections.

Every non-`supported` row crosses **marked**, below, rather than being deleted.

## Apply — patch items cleared for application

### P1 — `subagents.md:95`, `maxTurns` row · CLEARED

Replace line 95:

```markdown
| `maxTurns` | **no default and no maximum documented.** Behaviour at the limit is documented: output is returned "marked as partial", and the subagent can be resumed. Partial marking requires Claude Code **v2.1.246+** |
```

Source, verbatim (SA, frontmatter table, `maxTurns` row): "Maximum number of agentic
turns before the subagent stops. When the subagent reaches the limit, Claude Code
returns its output marked as partial, and Claude can resume it to continue. The partial
marking requires Claude Code v2.1.246 or later". Verdict rows C29a `supported`,
C29b `supported`.

### P3 — `subagents.md:34-35` and `:111`, `tools` omitted · CLEARED, and strengthened by N5

Replace the `tools` parenthetical at `:34-35`:

```markdown
`tools` (allowlist; **omitted = inherit every tool available to subagents** — already
narrowed by two filters, not literally every tool)
```

Source, verbatim: "Inherits every tool available to subagents if omitted" (C15) and
"…narrowed by two filters: the first removes a short list of tools from every subagent,
and the second reduces the built-in tool set for subagents that run in the background,
which is the default" (C16). The practical warning at `:111` stays as the draft says.

**Available to the human and absent from the draft:** the source *does* enumerate the
first filter's membership, which the draft recorded as unknown (verdict row N5,
`not-supported`). If you want the correction to be complete, the enumeration is:
`Agent` (at the depth limit), `AskUserQuestion`, `EndConversation`, `EnterPlanMode`,
`ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`, `TaskOutput`,
`WaitForMcpServers`, `Workflow` — "removes these tools, even when listed in the `tools`
field". Forks "skip both filters and receive the main conversation's exact tool pool".
**I have not written that into the patch text**: it is not a draft claim with a verdict
row of its own, and adding it here would be authorship. It is recorded as observation
O4 in the verdict document so the next sweep can claim it properly.

### P4 — `subagents.md:36-38`, frontmatter field list · CLEARED

Add `initialPrompt` and `experimental` to the optional-field list. Source, verbatim:
`initialPrompt` — "Auto-submitted as the first user turn when this agent runs as the
main session agent (via `--agent` or the `agent` setting). Commands and skills are
processed. Prepended to any user-provided prompt". `experimental` — "Set its `cacheTtl`
key to `5m` or `1h`… ignores any other value, ignores `1h` while your Claude
subscription is using usage credits, and reads the field only from subagent files.
Requires Claude Code v2.1.248 or later" (C33).

### P5 — `subagents.md:86-104`, provenance line · CLEARED with a correction to the patch itself

Append under the limit table:

```markdown
Each row above is quoted with its locator and fetch date in the claim table of
`docs/research/drafts/x2-subagent-limits.md` (fetched 2026-08-29).
```

**Correction to P5's own justification.** P5 says the values at `:90-93` "were
re-confirmed today"; the draft's §1.2 says `:93` (the `MEMORY.md` row) was *not* checked
by the sweep and "remains unverified". Both cannot be true. The resolution is in the
verdict document: **I re-read all four rows against the source myself, and all four
hold**, including `:93` — "The subagent's system prompt also includes the first 200
lines or 25KB of `MEMORY.md` in the memory directory, whichever comes first". The
provenance line above is therefore accurate for `:90-92` only, because those are the
rows the draft's claim table actually quotes. `:93` is confirmed by the verdict document
(row X1), not by the draft.

### P2 — `subagents.md:52-53`, background tool list · CLEARED, one correction, one gap

Replace the "Foreground vs background" paragraph's second sentence:

```markdown
Background keeps every MCP tool but only these built-ins: `Read`, `Grep`, `Glob`,
`Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`,
`TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`,
`TaskStop`, `SendMessage`, `Artifact`. Every other built-in is removed **whether
inherited or listed in the `tools` field** — so the same definition resolves to a
different tool set in the foreground and the background.
```

**This is one of the two corrections to an existing verified note, and it holds.** The
draft's quote at C17 is the longest in its table and is word-for-word exact against the
source, tool order included; the retained list is 19 names, as claimed. The diagnosis is
also right: `subagents.md:112` currently says background "silently drops non-listed
built-ins", which reads as though listing a tool protects it, and the source says
"whether inherited or listed in the `tools` field".

**Gap, recorded not applied.** The replacement fixes the background half of the
misreading and leaves the foreground half unstated — the first filter's nine tools are
removed in the foreground too, and forks skip both filters. Same source section, same
paragraph. Applying P2 as written is an improvement over the current text and is safe;
it is just not the whole correction.

## Hold — patch items that must not be applied yet

### P0 — add the Errors page to `sources:` · HOLD

The two claims that would justify listing `https://code.claude.com/docs/en/errors` in
the note's frontmatter are C14 and C19, and both are `source-unreachable`. The base's
contract is that every claim's source appears in frontmatter; the converse also holds —
do not add a source that no verified claim rests on.

The fetch-date half of P0 is independent and fine: `subagents.md:5` may go from
`fetched: 2026-08-27` to `fetched: 2026-08-29`, since the Subagents page was re-read in
full today.

### P6 — new row on the SA/ER wording mismatch · HOLD

Rests on C13 (`supported`), C14 (`source-unreachable`) and C14b
(`source-unreachable`). A row asserting that two pages "differ in wording, not in
behaviour" cannot enter a verified note when one of the two pages was never read. The
Errors page's *heading* — "Agent descriptions are over the 15.0k-token limit" — is
corroborated by its error-index table, so the wording mismatch is probably real; the
"nothing is rejected" half, which is the load-bearing half, is unverified.

**What would settle it:** one successful fetch of the two sections
`#agent-descriptions-are-over-the-15000-token-limit` and
`#agent-would-be-spawned-with-zero-tools`. Three attempts from here all returned the
page truncated before them.

## Marked — claims that did not survive, retained rather than deleted

Per note-promotion §2, these cross as a record that the question was asked, not as
claims. **They belong in the verdict document, not in `subagents.md`** — this section
exists so the next sweep does not spend the same effort.

| Claim | Verdict | Record |
|---|---|---|
| C14 — "The Errors page describes the same threshold as a limit, and states nothing is rejected" | `source-unreachable` | `https://code.claude.com/docs/en/errors`, 3 of 3 attempts, page truncated before the "Configuration warnings" section every time; literal-string search for "stay in effect until you fix them" returned NOT VISIBLE |
| C14b — "the two pages differ in wording, not in behaviour" | `source-unreachable` | same URL, same 3 attempts. SA half verified verbatim; ER half never read |
| C19 — "Claude Code refuses to spawn a subagent with no usable tools" | `source-unreachable` | same URL, same 3 attempts, including an anchored fetch of `#agent-would-be-spawned-with-zero-tools`. Only the error-index row was ever visible |
| N5 — "the actual list of always-removed tools was not obtained. **Membership unknown**" | `not-supported` | The source enumerates nine tools in the same section. Disconfirming read: requested the whole "Available tools" section verbatim instead of the one sentence |
| N6 — "the page … does not mention CLAUDE.md either way"; the base's `:70` claim "comes from its own canary probe, not from this documentation" | `not-supported` | The page documents it three times, including "**CLAUDE.md files**: every level of the CLAUDE.md hierarchy the main conversation loads…". Disconfirming read: full-page search for the literal string "CLAUDE.md". **`subagents.md:70` and `:29-30` are documented, not probe-only** |
| N7 — "'closest-to-cwd wins among project dirs' … **Not present** … Unconfirmed here" | `not-supported` | Documented in prose: "…Claude Code uses the definition closest to the working directory", with a version gate of v2.1.178. Disconfirming read: searched "cwd", "closest", "working directory". **`subagents.md:21` is confirmed** |
| N4 — "Not reached; attempt cap hit at 3" (env-vars / settings) | `not-checkable` | A claim about another agent's fetch history. What would settle it: a fresh fetch of `code.claude.com/docs/en/env-vars` |
| X1 — §1.2: the `MEMORY.md` limit is "documented on a separate page" and `subagents.md:93` "remains unverified" | `not-supported` | It is on the Subagents page the sweep read six times. The row holds |
| X2 — "35 claim rows" | `not-supported` | 38, counted at `drafts/x2-subagent-limits.md:265-331` |
| X3 — C22's cell: the page "does not restate the exclusion of `disable-model-invocation: true` skills" | `not-supported` | It does, in the section the draft quoted from. **`subagents.md:46` is confirmed** |

Three of those `not-supported` rows (N6, N7, X3) each **confirm** a line in
`subagents.md` that the draft reported as unconfirmed. No edit to those lines is needed;
the record is here so nobody re-opens them.

## `sources:` entries

| Entry | Action |
|---|---|
| `https://code.claude.com/docs/en/sub-agents` | keep; update `fetched: 2026-08-27` → `fetched: 2026-08-29` |
| `https://code.claude.com/docs/en/errors` | **do not add** — see P0 |
| `https://platform.claude.com/docs/en/about-claude/models/overview` | **do not add.** C12 is `supported`, but the note's use of it (`:101`, "Against Opus 5's 1M-token context") is a pointer to a value that moves. If it is added, add it as a pointer with its fetch date, and note that the draft itself says not to carry the number forward |

`verified_by:` is **not** proposed for `subagents.md`. That frontmatter key is this
pipeline's addition for notes it writes; this note was not written by the pipeline and
the patch is partial, so stamping it would over-claim. The provenance line from P5 does
the same job inside the body.

## Back-link patch table (note-promotion §4)

No new note enters the graph, so no new neighbours. I re-checked all nine of the
draft's rows at `file:line`; the draft's table is **correct in every row**.

| Neighbour named by `subagents.md:8` | Exists | Names `subagents` back | Line to replace |
|---|---|---|---|
| `skill-anatomy` | yes | **no** — `skill-anatomy.md:11` | Replace `skill-anatomy.md:11` with: `related: ["[[skill-authoring-best-practices]]", "[[agent-design-template]]", "[[agent-builder-prior-art]]", "[[subagents]]"]` |
| `dynamic-workflows` | yes | yes (`:8`) | — |
| `hooks` | yes | yes (`:10`) | — |
| `claude-code-extension-layer` | yes | yes (`:8`) | — |
| `agent-design-template` | yes | yes (`:15`) | — |
| `agent-builder-prior-art` | yes | yes (`:18`) | — |
| `api-agent-loop` | yes | yes (`:12`) | — |
| `effective-agents-anthropic` | yes | yes (`:9`) | — |
| `managed-agents-architecture` | yes | yes (`:9`) | — |

**Dangling link, confirmed and unrelated to this patch.**
`claude-code-extension-layer.md:8` names `[[plugins]]`; there is no `plugins.md` in
`/home/user/skills-repo/knowledge/notes/`. The note is `plugins-and-marketplaces`.
Replacement line for `claude-code-extension-layer.md:8`:
`related: ["[[skill-anatomy]]", "[[claude-md-and-memory]]", "[[subagents]]", "[[hooks]]", "[[mcp]]", "[[plugins-and-marketplaces]]", "[[dynamic-workflows]]"]`

## Closing report (note-promotion §6)

- **Claims that crossed:** 35 of 38, as 5 of 7 applicable patch items (P1–P5).
- **Non-`supported`:** 3 `source-unreachable` in the claim table (C14, C14b, C19); plus,
  outside it, 6 `not-supported` and 1 `not-checkable` among the draft's own §4 findings
  and body claims.
- **Sources dropped:** one — `https://code.claude.com/docs/en/errors` is not added to
  the note's frontmatter, because no verified claim rests on it.
- **Back-links owed:** 2 — `skill-anatomy.md:11` (this patch's), and
  `claude-code-extension-layer.md:8` (pre-existing dangling link).
- **What this stage cannot see:** whether the sweep asked the right questions. The scope
  contract at draft §1 is `agent-shape`'s to judge, and it has one defect I can name
  because it is a fact about a source rather than about scope: the §1.2 exclusion of
  `MEMORY.md` is justified by "documented on a separate page", and it is not — it is on
  the page the sweep read. Whether excluding it was still the right call is not mine.
