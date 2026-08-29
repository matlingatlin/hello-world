---
title: Documented limits on Claude Code subagents — what a definition file can be checked against
sources:
  - url: https://code.claude.com/docs/en/sub-agents
    note: Anthropic, Claude Code documentation, "Subagents" (undated page; no version stamp shown)
    fetched: 2026-08-29
  - url: https://code.claude.com/docs/en/errors
    note: Anthropic, Claude Code documentation, "Errors" (undated page)
    fetched: 2026-08-29
  - url: https://platform.claude.com/docs/en/about-claude/models/overview
    note: Anthropic, Claude Docs, "Models overview", Compare models table (reached via 302 from docs.claude.com/en/docs/about-claude/models/overview)
    fetched: 2026-08-29
status: unverified
tags: [claude-code, subagents, limits, agent-review, measured-vs-repeated]
related: ["[[subagents]]", "[[agent-design-template]]", "[[skill-anatomy]]"]
---

# Draft x2-subagent-limits

This is a **draft**, not a note. It carries, in order: the scope contract, the
proposed change to the base (a patch — see the extend verdict), the full claim
table the verifier rules against, what could not be found measured, and the
back-link table. `status: unverified`. Nobody has checked it.

**Standing caveat on every quote below.** Quotes were obtained through `WebFetch`,
which converts a page to markdown and extracts through a model. I did not see raw
page source. The verifier must re-fetch each URL and confirm each quote verbatim,
not read my rendering of it.

---

# 1 · Scope contract

**`<id>`:** `x2-subagent-limits`
**Commission:** `/home/user/hello-world/docs/research/commissions/x2-subagent-limits.md`

**Candidate sentence, verbatim:**

> it reviews a Claude Code subagent definition and produces a findings list at
> file:line with a verdict.

**Caller:** **not stated.** The commission carries no `Commissioned by:` field, no
`Sweep:` field, and no "What the later stage will have to decide" section, all of
which the template at
`/home/user/hello-world/.claude/skills/research-commission-scoping/assets/commission.md`
requires. It does carry a candidate sentence naming an artefact, which is the part
that bounds me, so I proceeded. The missing fields are recorded here rather than
reconstructed: I did not invent a caller and I did not infer whether this is a
first or a second sweep. **Treated as a first sweep** — if it was in fact a
re-commission, this sweep re-covered ground and someone should say so.

## 1.1 Question list

The candidate sentence's artefact is *a findings list at file:line with a verdict*,
produced from **a definition file read statically**. That is what the questions are
cut to: a documented constraint that cannot be evaluated by looking at one file is
not directly usable by this agent, and saying which ones those are is itself an
answer.

| # | Question | What a good answer lets the later stage decide |
|---|---|---|
| Q1 | What is the documented nesting/spawn depth for subagents, what happens at the limit, and how is it configured? | Whether the reviewer can flag a definition that delegates, and whether "this agent spawns agents" is a finding or only a note |
| Q2 | What is the documented concurrency limit, its failure mode, and its configuration? | Whether concurrency is checkable from a definition file at all, or is a session-level property the reviewer must decline to rule on |
| Q3 | What is documented about a subagent's context — isolation, what it does and does not inherit, and any size? | Whether "this body is too long" can be a finding with a limit behind it, or only a quality opinion |
| Q4 | What does the `tools` field do when present and when omitted, and what silently narrows it? | The highest-value check the reviewer can make: whether an omitted or over-broad `tools:` is a defect, and whether a listed tool can be dropped anyway |
| Q5 | What does `skills:` preload, what does it not control, and is there a documented cap on how many? | Whether a "≤3 preloaded skills" rule is a documented limit or a quality judgement — these are different findings with different verdicts |
| Q6 | Which documented constraints bear on a **single definition file read statically** — required fields, name rules, version gates — and which are only observable at runtime? | The reviewer's actual check list, and the boundary of its remit: what it must report as unverifiable rather than pass |

## 1.2 Out of scope, with reasons

| Area | Why the candidate sentence does not need it |
|---|---|
| `memory:` persistence and the `MEMORY.md` size limit | Concerns cross-session persistence, documented on a separate page. **Consequence to record:** the existing note's row *"`MEMORY.md` in the subagent system prompt \| first 200 lines or 25 KB"* (`subagents.md:93`) was **not checked by this sweep** and remains unverified. Do not read this draft as confirming it |
| `.claude/rules/` reachability into a subagent | Already MEASURED and owned by `subagents.md:63-84` with a probe behind it. Re-running it would produce a rival result on a settled question |
| Hooks, MCP server config, plugin packaging internals | Neighbouring features. A definition file may name them, but their internals are not a limit on the subagent |
| `isolation`, `color`, `effort`, `background` field semantics | Field semantics that bear on none of the five limit areas. If the reviewer is later asked to lint every field, that is a second commission |
| Prompt-caching economics and per-model pricing | Cost, not a limit, and it moves on its own |
| The SkillsBench "1–3 modules ≈ +19.0pp, 4+ ≈ +10.1pp" figure behind this repo's three-skill rule | A **quality** finding, cited at `agent-design-template.md:35` and `:190` and repeated in `/home/user/hello-world/CLAUDE.md`. It is not a documented limit, so Q5 does not reach it. **It is also unverified against its primary source and nothing in this sweep verified it.** Flagged, not acted on |
| Academic literature (PubMed, arXiv, Semantic Scholar) | The question is what a vendor documents about its own system. The vendor's documentation *is* the primary source here; a paper about subagents would be secondary to it. Recorded as a deliberate departure from `literature-review` §2's default database set, not an omission |
| Whether the candidate sentence is the right agent | Out of my hands by construction. See the finding below |

**One finding that would widen the commission, recorded and not acted on.** Q4 and
Q6 turned up a structural problem for the proposed agent: *the same definition file
resolves to different tools in the foreground and the background* (claim C17), and
the 15,000-token description budget is **shared across the whole roster** (C13), so
neither is decidable from one file. An agent that emits `file:line` findings with a
verdict will, on these two, have to emit "unverifiable from this file alone". That
may mean the agent needs the roster as an input, not just the file. **That is
`agent-shape`'s call, not mine.** It gets one narrower second sweep; I have not
taken it.

## 1.3 Extend or author

**Verdict: `extend /home/user/skills-repo/knowledge/notes/subagents.md`.**

That note already owns this topic. `INDEX.md:15` advertises it by name for exactly
these values — *"**documented limits** (15,000-token shared description budget,
depth 3, 20 concurrent — and what is explicitly undocumented)"* — and
`subagents.md:86-104` carries the limit table. Authoring a rival would produce the
outcome `/home/user/skills-repo/CLAUDE.md` forbids.

**Cost of `extend`, stated so the caller knows what they asked for:** an existing
note cannot be rewritten by anything downstream in this pipeline. This arrives as
**a patch a human applies** (section 2). Nothing lands in the base automatically.

**Why the sweep still had value given the note exists.** The note's limit rows carry
no per-claim locator and no quote — it cites one URL and asserts on the order of
forty facts, which `references/base-format.md:66-71` already names as this base's
first structural defect. A verifier cannot rule row by row against it. This sweep
attaches quote, locator and fetch date to each row, and in doing so found four
places where the note is now stale or imprecise (patch items P1–P4).

**Queries run against the base, before any web search:**

| # | Where | Query | Result |
|---|---|---|---|
| B1 | `/home/user/skills-repo/knowledge/` | read `INDEX.md` in full | `[[subagents]]` advertised at `:15` as owning the documented limits |
| B2 | `knowledge/notes/` | `SPAWN_DEPTH\|CONCURRENT_SUBAGENTS\|15,000\|15000` | 3 files: `subagents.md`, `agent-design-template.md`, `agent-builder-prior-art.md` |
| B3 | `knowledge/notes/` | `nesting\|concurrent\|inherit ALL\|inherits every tool\|preload` (-i) | 5 files: the three above plus `architecture-evidence.md`, `claude-code-extension-layer.md` |
| B4 | `knowledge/notes/subagents.md` | read in full | Owns it. Limit table at `:86-104` |
| B5 | `knowledge/notes/agent-design-template.md` | `nesting\|concurrent\|15,000\|depth\|preload\|related:\|subagents` (-i) | Cites the limits but **defers**: *"See [[subagents]] for the full limit table"* (`:50`, and again `:111`). Not a rival — it is a consumer |
| B6 | `knowledge/notes/` | `related:` across all notes | Used for the back-link table (section 5) |

## 1.4 Search log

Protocol: `/home/user/skills-repo/.claude/skills/literature-review/SKILL.md` §2–5.
Date range: current documentation only, since the object is present behaviour.
Language: English. Publication type: **official vendor technical documentation**
(§2's "official technical docs" branch) — see the out-of-scope row on academic
databases. Inclusion: the page states a limit, a default, a field's semantics, or a
failure mode of Claude Code subagents. Exclusion: recorded per row below.

| Source | Date | Query / URL | Attempts | Result | Export |
|---|---|---|---|---|---|
| Claude Code docs — Subagents | 2026-08-29 | `https://code.claude.com/docs/en/sub-agents` — limits, env vars, description budget, `tools`/`skills`, background/foreground, precedence | 1 of ~3 | Reached. **Primary.** Source of C1–C12, C15–C28 | quotes in claim table |
| Claude Code docs — Subagents | 2026-08-29 | same URL — frontmatter field table, context-window wording, fork, size caps | 2 of ~3 | Reached. Same canonical URL, **deduplicated to one source** | quotes in claim table |
| Claude Code docs — Errors | 2026-08-29 | `https://code.claude.com/docs/en/errors` — the 15k description error and the zero-tools error | 1 of ~3 | Reached. **Primary.** Source of C14, C19 | quotes in claim table |
| Claude Code docs — Env vars | 2026-08-29 | `https://code.claude.com/docs/en/env-vars` — `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | 1 of ~3 | **Not reached** — page content truncated before the table rows | — |
| Claude Code docs — Env vars | 2026-08-29 | same URL, narrowed to literal strings `SPAWN_DEPTH`, `CONCURRENT_SUBAGENTS` | 2 of ~3 | **Not reached** — truncated again. Tool reported both strings absent from visible content | — |
| Claude Code docs — Settings | 2026-08-29 | `https://code.claude.com/docs/en/settings` — same two variables | 3 of ~3 | **Not reached.** 55.8 KB returned; grep for `SPAWN_DEPTH\|CONCURRENT_SUBAGENTS` over the saved output: **no matches**. Attempt cap hit; stopping rather than looping | saved tool output, grepped |
| Claude Docs — Models overview | 2026-08-29 | `docs.claude.com/en/docs/about-claude/models/overview` → 302 → `platform.claude.com/docs/en/about-claude/models/overview` | 1 of ~3 (plus the redirect hop) | Reached. **Primary** for the live model value C12 | Compare models table |

**Deduplication.** DOI / PMID / arXiv ID do not apply to vendor documentation; the
key used was the **canonical URL**. One duplicate removed: the Subagents page was
fetched twice with different prompts and counts as one source.

**Screening and exclusion reasons.** No secondary accounts (blog posts, third-party
summaries) were admitted: for a vendor's own documented behaviour the vendor page is
primary, and a summary of it is the exact "secondary account that cites a source you
did not open" shape this base has already been burned by. Nothing was excluded at
title or abstract stage, because the search was targeted at named pages rather than
a result list — recorded so the verifier does not mistake a short log for a thorough
one. The env-vars/settings pages were **excluded as unavailable full text**, not as
irrelevant, and the consequence is carried in section 4.

---

# 2 · The patch to `subagents.md` (the extend verdict's deliverable)

Against `/home/user/skills-repo/knowledge/notes/subagents.md` as read 2026-08-29.
**A human applies this.** Nothing in this pipeline may rewrite that file.

### P0 — frontmatter: add the fetch date and the second source

The note's `sources:` lists one URL with `fetched: 2026-08-27`. Two claims in the
patch rest on the Errors page, which is not listed. Per the base's own contract
(`base-format.md:31`) every claim's source appears in frontmatter.

Replace lines 3–5 with:

```yaml
sources:
  - url: https://code.claude.com/docs/en/sub-agents
    note: Anthropic, Claude Code documentation, "Subagents"
    fetched: 2026-08-29
  - url: https://code.claude.com/docs/en/errors
    note: Anthropic, Claude Code documentation, "Errors"
    fetched: 2026-08-29
```

Leave `status: verified` alone — **I am not the agent that sets it**, and changing
an existing note's status is not this sweep's business.

### P1 — `maxTurns` row is stale (`subagents.md:95`)

Current: `| `maxTurns` | field exists; **no default or maximum documented** |`

The "no default or maximum documented" half still holds (C29b, a not-found row).
The "field exists" half is now under-stated — the behaviour at the limit **is**
documented. Replace with:

```markdown
| `maxTurns` | **no default and no maximum documented.** Behaviour at the limit is
documented: output is returned "marked as partial", and the subagent can be
resumed. Partial marking requires Claude Code **v2.1.246+** |
```

### P2 — the background tool list is out of date and understates the rule (`subagents.md:52-53`)

Current text lists `Read/Grep/Glob/Bash/Edit/Write/WebFetch/WebSearch/Skill/SendMessage/…`.
The documented list is longer, and the important half is missing. Replace the
"Foreground vs background" paragraph's second sentence with:

```markdown
Background keeps every MCP tool but only these built-ins: `Read`, `Grep`, `Glob`,
`Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`,
`TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`,
`TaskStop`, `SendMessage`, `Artifact`. Every other built-in is removed **whether
inherited or listed in the `tools` field** — so the same definition resolves to a
different tool set in the foreground and the background.
```

The clause *"whether inherited or listed in the `tools` field"* is the load-bearing
addition: the current note says background "silently drops non-listed built-ins"
(`:112`), which reads as though listing a tool protects it. It does not.

### P3 — `tools` omitted: "inherit ALL" is imprecise (`subagents.md:34-35`, `:111`)

The documented wording is *"Inherits every tool available to subagents if omitted"*
— and "available to subagents" is already narrowed by two filters before the
definition is read. Suggest: `**omitted = inherit every tool available to
subagents** (already narrowed by two filters — not literally every tool)`. The
practical warning at `:111` stays correct and stays.

### P4 — two frontmatter fields are missing from the list (`subagents.md:36-38`)

Add `initialPrompt` and `experimental` (its `cacheTtl` key, `5m` or `1h`, read only
from subagent files, requires v2.1.248+).

### P5 — attach locators to the limit table (`subagents.md:86-104`)

The values at `:90-93` were re-confirmed today and **none changed**. What they lack
is provenance. Suggest appending a line under the table:

```markdown
Each row above is quoted with its locator and fetch date in the claim table of
`docs/research/drafts/x2-subagent-limits.md` (fetched 2026-08-29).
```

### P6 — one row to add: the two docs pages describe the 15k threshold differently

```markdown
The Subagents page calls 15,000 tokens a **warning** threshold; the Errors page
titles the same thing a **limit** and says the descriptions "stay in effect until
you fix them" — i.e. it is a warning either way, nothing is rejected. The Errors
page also tells you to shorten descriptions "in your Claude Code config file",
while the Subagents page locates them in the subagent definitions. Wording
mismatch, same behaviour.
```

---

# 3 · Claim table

House rule, the base's own (`ideation-and-idea-selection.md:29-31`): every row
carries **MEASURED** (a study with numbers exists and was read — here, a
documentation page stating behaviour, quoted, with its fetch date, per
`verdict-rules.md:31`) or **REPEATED** (widely asserted, no measurement found).

Sources are abbreviated: **SA** = `https://code.claude.com/docs/en/sub-agents`,
**ER** = `https://code.claude.com/docs/en/errors`, **MO** =
`https://platform.claude.com/docs/en/about-claude/models/overview`. All fetched
2026-08-29. Empty cells are left empty on purpose.

## Q1 — nesting / spawn depth

| # | Claim | Src | Locator | Quote | What is stated | Kind of number | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|
| C1 | The default nesting depth is three layers of subagents below the main conversation | SA | § "Let subagents spawn their own subagents" | "By default, a subagent can spawn subagents of its own, up to three layers below the main conversation." | a configurable default, not a hard cap | **documented default** | page carries no version stamp; value is settable per-session | **MEASURED** (documented behaviour) |
| C2 | At the depth limit the `Agent` tool is withheld from every subagent except a fork | SA | § "Let subagents spawn their own subagents" | "At the depth limit, Claude Code withholds the `Agent` tool from every subagent except a [fork](#fork-the-current-conversation), so a subagent at the limit does its delegated work itself and returns one summary." | enforcement mechanism | — | | **MEASURED** |
| C3 | The depth limit is set by `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, and `1` turns nesting off | SA | § "Let subagents spawn their own subagents" | "To change the limit, set [`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`](/docs/en/env-vars) to the number of subagent layers you want below your main conversation." … "Set `1` to turn nesting off." | configuration | — | **the env-vars reference page could not be read (3 attempts). This rests on the Subagents page alone; no corroboration of the variable's own documented default** | **MEASURED** |
| C4 | A fork cannot spawn further forks | SA | § "Fork the current conversation" | "A fork can't spawn further forks." | — | — | says nothing about a fork spawning a non-fork subagent | **MEASURED** |

## Q2 — concurrency

| # | Claim | Src | Locator | Quote | What is stated | Kind of number | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|
| C5 | The default concurrent-subagent limit is 20, and spawning past it fails rather than queues | SA | § "Concurrent subagent limit" | "By default, when 20 subagents are running in a session, spawning another with the Agent tool fails with `Concurrent subagent limit reached`, and the error tells Claude not to retry." | **20 running in a session** | **documented default** | scoped to "in a session" | **MEASURED** |
| C6 | Capacity recovers automatically as running subagents finish | SA | § "Concurrent subagent limit" | "Spawning succeeds again when the running count drops below the limit." | — | — | | **MEASURED** |
| C7 | The concurrency limit is set by `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, any positive whole number | SA | § "Concurrent subagent limit" | "To change the limit, set [`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`](/docs/en/env-vars) to any positive whole number." | configuration | — | env-vars page unread — same gap as C3 | **MEASURED** |

## Q3 — context

| # | Claim | Src | Locator | Quote | What is stated | Kind of number | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|
| C8 | A subagent runs in its own context window | SA | § intro / "Subagents" overview | "Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions." | isolation, qualitative | — | no size given anywhere in the sentence | **MEASURED** |
| C9 | A subagent does not see the parent's history, previously invoked skills, or previously read files | SA | § "Subagents start fresh" (wording as rendered) | "Each subagent starts with a fresh, isolated context window. It doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read." | three named exclusions | — | this quote does not mention CLAUDE.md either way; the base's claim that CLAUDE.md **is** injected rests on its own 2026-08-28 probe (`subagents.md:70`), not on this page | **MEASURED** |
| C10 | A fork is the exception and inherits the whole parent conversation | SA | § "Fork the current conversation" | "A fork is a subagent that inherits the entire conversation so far instead of starting fresh." and "The exception is a [fork](#fork-the-current-conversation), which inherits the parent conversation instead of starting fresh." | — | — | | **MEASURED** |
| C11 | A fork's first request reuses the parent's prompt cache, making it cheaper than a fresh subagent | SA | § "Fork the current conversation" | "Because a fork's system prompt and tool definitions are identical to the parent, its first request reuses the parent's [prompt cache](/docs/en/prompt-caching#subagents-and-the-cache). This makes forking cheaper than spawning a fresh subagent for tasks that need the same context." | a **cost** claim by the vendor about its own product, with no figure | no number | no measurement, no percentage, no benchmark | **MEASURED** as documented behaviour; the "cheaper" comparison itself is **REPEATED** — vendor assertion, unquantified |
| C12 | **POINTER, re-fetch.** Claude Opus 5's context window is 1M tokens | MO | § "Compare models", "Context window" row, "Claude Opus 5" column | row as rendered: "\| [Context window] \| 1M tokens \| 1M tokens \| 1M tokens \| 200K tokens \|" — columns in order Fable 5, **Opus 5**, Sonnet 5, Haiku 4.5. Footnote: "**Context window:** 1M tokens is roughly 555k words or 2.5M Unicode characters on the current tokenizer" | model capacity, not a subagent limit | **a value that moves on its own** | **Do not carry this number forward.** It is recorded as a pointer to `https://platform.claude.com/docs/en/about-claude/models/overview`, fetched 2026-08-29. The verifier re-fetches rather than trusting the cell. The value read from a table column is also the most fragile quote in this table | **MEASURED**, pointer |

## Q4 — tool inheritance

| # | Claim | Src | Locator | Quote | What is stated | Kind of number | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|
| C15 | Omitting `tools` inherits every tool available to subagents | SA | § "Supported frontmatter fields", `tools` row | "Tools the subagent can use. Inherits every tool available to subagents if omitted." | default-on inheritance | — | "available to subagents" is pre-narrowed — see C16. **"Inherits ALL" is therefore imprecise** | **MEASURED** |
| C16 | Inheritance is narrowed by two filters before any definition is considered | SA | § "Available tools" | "Subagents inherit the [built-in tools](/docs/en/tools-reference) and MCP tools available in the main conversation, narrowed by two filters… the first removes a short list of tools from every subagent, and the second reduces the built-in tool set for subagents that run in the [background](#run-subagents-in-foreground-or-background), which is the default." | — | — | the quote as rendered elides the first filter's membership ("a short list") — **the actual list of always-removed tools was not obtained** | **MEASURED** |
| C17 | A background subagent keeps only a named set of built-ins, and the removal applies even to tools the definition lists | SA | § "Available tools" | "Apart from `Agent` and `ExitPlanMode`, which follow the first filter's conditions wherever the subagent runs, a background subagent keeps every MCP tool but only these built-in tools: `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage`, and `Artifact`. Claude Code removes every other built-in tool from a background subagent, whether inherited or listed in the `tools` field, so the same definition can resolve to different tools in the foreground and the background." | 19 named built-ins retained | a **count of names in one quoted list**; one unit = one tool identifier as written | **This is the row that constrains the proposed agent most.** A `tools:` line cannot be ruled on from the file alone without knowing where the subagent runs | **MEASURED** |
| C18 | If no entry in `tools` resolves to a tool, the subagent usually fails to launch, and the error names the entries | SA | § "Supported frontmatter fields", `tools` row | "If no entry in the list resolves to a tool, the subagent usually [fails to launch](/docs/en/errors#agent-would-be-spawned-with-zero-tools) with an error naming the entries." | — | — | "usually" is the doc's own hedge; the conditions under which it does not fail are not stated | **MEASURED** |
| C19 | Claude Code refuses to spawn a subagent with no usable tools | ER | § "would be spawned with zero tools — refusing" | "Claude Code refuses to spawn a subagent with no tools, because it would be unable to accomplish any work." Causes listed: "All tools are blocked by Read deny rules in your permission settings", "Your subagent configuration denies access to all available tools", "The tools the subagent needs have been removed or are no longer available" | — | — | two of the three causes are **environmental**, not in the file — so a typo'd tool name is only *sometimes* the cause the reviewer can see | **MEASURED** |
| C20 | `disallowedTools` removes tools from either the inherited set or an explicit `tools` list | SA | § "Supported frontmatter fields", `disallowedTools` row | "Tools to deny, removed from inherited or specified list" | — | — | | **MEASURED** |

## Q5 — preloaded skills

| # | Claim | Src | Locator | Quote | What is stated | Kind of number | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|
| C21 | `skills:` injects the **full content** of each listed skill at startup | SA | § "Preload skills into subagents" | "The full content of each listed skill is injected into the subagent's context at startup." and § "Supported frontmatter fields": "The full skill content is injected, not only the description." | — | — | no size accounting given for the injection | **MEASURED** |
| C22 | `skills:` controls preloading, not access — without it a subagent can still discover and invoke skills through the Skill tool | SA | § "Preload skills into subagents" | "This field controls which skills are preloaded, not which skills the subagent can access: without it, the subagent can still discover and invoke project, user, and plugin skills through the Skill tool during execution." | — | — | this page does not restate the exclusion of `disable-model-invocation: true` skills that `subagents.md:46` asserts; **not checked here** | **MEASURED** |
| C23 | To preload skills, use `skills` rather than listing `Skill` in `tools` | SA | § "Supported frontmatter fields", `tools` row | "To preload Skills into context, use the `skills` field rather than listing `Skill` here" | — | — | | **MEASURED** |
| C24 | There is **no documented numeric cap** on how many skills may be preloaded | SA | searched: § "Preload skills into subagents", § "Supported frontmatter fields" | *no quote — this is a negative* | — | — | A negative cannot carry a quote. Recorded as searched-and-absent, not as established. **The repo's "at most three preloaded skills" rule is therefore not a documented limit** — it is a quality claim, sourced at `agent-design-template.md:35` to SkillsBench, which this sweep did not open | **REPEATED** — see section 4 |

## Q6 — what is checkable in one file

| # | Claim | Src | Locator | Quote | What is stated | Kind of number | Limits | Verdict |
|---|---|---|---|---|---|---|---|---|
| C13 | Combined descriptions of all non-built-in subagents over 15,000 tokens trigger a startup **warning** | SA | § "Create custom subagents" | "Those descriptions take up context, so keep them short. When the combined descriptions of your subagents, except the built-in ones, exceed 15,000 tokens, Claude Code shows a [warning at startup with the total token count](/docs/en/errors#agent-descriptions-are-over-the-15000-token-limit). Trim the `description` fields of your subagents, and move detail into each subagent's system prompt, which only loads when that subagent runs." | **15,000 tokens, combined across the roster, excluding built-ins** | **documented threshold** — a warning, not a rejection | **Not checkable from one definition file.** It is a roster-wide sum | **MEASURED** |
| C14 | The Errors page describes the same threshold as a limit, and states nothing is rejected | ER | § "Agent descriptions are over the 15.0k-token limit" | "Your agent descriptions collectively exceed Claude's context limit for agent metadata. Claude Code displays this warning when you start a session, and the agent descriptions stay in effect until you fix them." Remedies: "Shorten the agent descriptions in your Claude Code config file", "Remove agents you aren't using from your config", "Check the config file's syntax with `claude --validate-config`" | — | same threshold, stated as "15.0k" | | **MEASURED** |
| C14b | **Disagreement row.** The two pages differ in wording, not in behaviour | SA + ER | as C13, C14 | SA: "shows a warning at startup"; ER: titled "over the 15.0k-token limit" but "the agent descriptions stay in effect until you fix them" | Both describe a warning that changes nothing at runtime. ER additionally locates descriptions in "your Claude Code config file", where SA locates them in subagent definition files | — | Kept as its own row rather than smoothed. A reviewer agent must not report this as a hard failure | **MEASURED** ×2, disagreement recorded |
| C25 | `name` is required and must be lowercase letters and hyphens | SA | § "Supported frontmatter fields", `name` row | "Unique identifier using lowercase letters and hyphens." … "The filename doesn't have to match." | required field | — | | **MEASURED** |
| C26 | A `name` containing `:` causes the file not to load, with an error to the debug log — and this changed in v2.1.218 | SA | § "Supported frontmatter fields", `name` row | "Names can't contain `:`, which is reserved for [plugin-scoped identifiers](/docs/en/plugins) such as `my-plugin:reviewer`. Claude Code doesn't load a file whose name contains one and logs an error to the debug log. Before v2.1.218, such names were accepted" | silent-ish failure mode | version gate **v2.1.218** | verdict depends on the reader's installed version — **a static check needs the target version as an input** | **MEASURED** |
| C27 | `description` is required, and its purpose is delegation | SA | § "Supported frontmatter fields", `description` row | "When Claude should delegate to this subagent" | required field | — | | **MEASURED** |
| C28 | `model` defaults to `inherit` when omitted | SA | § "Choose a model" / frontmatter table | "**Omitted**: defaults to `inherit` and uses the same model as the main conversation" | — | — | | **MEASURED** |
| C29a | `maxTurns` output at the limit is returned marked partial and can be resumed | SA | § "Supported frontmatter fields", `maxTurns` row | "Maximum number of agentic turns before the subagent stops. When the subagent reaches the limit, Claude Code returns its output marked as partial, and Claude can [resume it](#resume-subagents) to continue. The partial marking requires Claude Code v2.1.246 or later" | — | version gate **v2.1.246** | | **MEASURED** |
| C29b | `maxTurns` has **no documented default and no documented maximum** | SA | searched: frontmatter table, § "Supported frontmatter fields" | *no quote — negative* | — | — | absence, not a stated absence | **REPEATED** — see section 4 |
| C30 | `permissionMode` is ignored for plugin subagents | SA | frontmatter table, `permissionMode` row | "Ignored for [plugin subagents](#choose-the-subagent-scope)" | — | — | | **MEASURED** |
| C31 | `mcpServers` is ignored for plugin subagents | SA | frontmatter table, `mcpServers` row | "Ignored for [plugin subagents](#choose-the-subagent-scope)" | — | — | | **MEASURED** |
| C32 | `hooks` is ignored for plugin subagents | SA | frontmatter table, `hooks` row | "Ignored for [plugin subagents](#choose-the-subagent-scope)" | — | — | whether a file *is* a plugin subagent is a function of its location, not its content | **MEASURED** |
| C33 | `experimental.cacheTtl` accepts only `5m` or `1h`, is read only from subagent files, and requires v2.1.248+ | SA | frontmatter table, `experimental` row | "Set its `cacheTtl` key to `5m` or `1h` to choose the [prompt cache lifetime](/docs/en/prompt-caching#choose-the-ttl-yourself) for this subagent's requests. Claude Code ignores any other value, ignores `1h` while your Claude subscription is using usage credits, and reads the field only from subagent files. Requires Claude Code v2.1.248 or later" | — | version gate **v2.1.248** | | **MEASURED** |
| C34 | `permissionMode: manual` is an alias for `default` and requires v2.1.200+ | SA | frontmatter table, `permissionMode` row | "`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, or `manual` as an alias for `default`. The `manual` alias requires Claude Code v2.1.200 or later" | enumerated value set — statically checkable | version gate **v2.1.200** | | **MEASURED** |
| C35 | Subagent definitions resolve by a five-level precedence, managed settings highest, plugin `agents/` lowest | SA | § "Choose the subagent scope", precedence table | table as rendered: "Managed settings — 1 (highest); `--agents` CLI flag — 2; `.claude/agents/` — 3; `~/.claude/agents/` — 4; Plugin's `agents/` directory — 5 (lowest)" | 5 levels | a count of rows in one quoted table; one unit = one location | this page's table does **not** carry the base note's extra claim that "closest-to-cwd wins among project dirs" (`subagents.md:21`) — **not confirmed here** | **MEASURED** |
| C36 | There is **no documented size limit** on a subagent definition file or its system prompt | SA | searched: whole page, incl. § "Create custom subagents", frontmatter table | *no quote — negative* | — | — | absence. The only size-shaped constraint on the page is the roster-wide description budget (C13) | **REPEATED** — see section 4 |

**Verdict counts.** MEASURED: 31 rows (C1–C3, C4, C5–C7, C8–C11, C12, C13, C14, C14b, C15–C23, C25–C28, C29a, C30–C35 — C11 split, its cost comparison counted as REPEATED). REPEATED: 4 (C11's "cheaper" half, C24, C29b, C36). Rows resting on an unreached source: 0 — but C3 and C7 lack the corroboration the env-vars page would have given.

---

# 4 · What could not be found measured

Each row: the question, what was searched, and the finding. This is the section
`agent-shape` should read hardest — a rule with nothing here behind it is an
opinion.

| Question | What was searched | Finding |
|---|---|---|
| Is there a documented cap on the number of preloaded `skills:`? (Q5) | SA § "Preload skills into subagents" and the full frontmatter field table, read in two separate fetches | **No cap documented.** The field's description states what is injected, never how many may be. The "at most three preloaded skills" rule in `/home/user/hello-world/CLAUDE.md` is therefore **not a documented limit**, and an agent that reports a fourth skill as a violation of a *limit* would be misreporting it. Its actual basis is a quality figure at `agent-design-template.md:35`, unverified by this sweep |
| Does `maxTurns` have a documented default or maximum? (Q6) | SA frontmatter table, `maxTurns` row; § "Supported frontmatter fields" | **Neither is stated.** The row documents behaviour at the limit, not the limit's bounds. Agrees with the existing note's `:95`, and adds the behaviour it was missing |
| Is there a documented maximum size for a definition file or a system prompt? (Q3, Q6) | SA whole page across two fetches, targeted at size caps | **None stated.** So "this agent body is too long" is a **quality** finding, never a limit finding. The existing note already says this well (`subagents.md:101-104`: "do not dress it as a limit") and this sweep found nothing to overturn it |
| What are the documented **defaults of the two environment variables themselves**? (Q1, Q2) | `code.claude.com/docs/en/env-vars` twice (truncated both times; targeted string search on the second) and `code.claude.com/docs/en/settings` once, whose 55.8 KB response was grepped for `SPAWN_DEPTH\|CONCURRENT_SUBAGENTS` — **no matches** | **Not reached; attempt cap hit at 3.** The defaults of 3 and 20 rest on the Subagents page alone (C1, C5). That page is primary and states them plainly, so this is a corroboration gap, not a hole — recorded so nobody later claims two sources where there is one |
| Which tools does the **first** filter always remove from every subagent? (Q4) | SA § "Available tools" | The page says "a short list of tools" and, as rendered, does not enumerate it. **Membership unknown.** A reviewer agent cannot tell a user which tools its `tools:` list will lose unconditionally |
| Does a subagent inherit the CLAUDE.md hierarchy? (Q3) | SA § on what a subagent starts with | **The page's quoted sentence names three exclusions and does not mention CLAUDE.md either way.** The base's positive claim (`subagents.md:70`) comes from its own 2026-08-28 canary probe, not from this documentation. Two different kinds of evidence; do not merge them |
| Is "closest-to-cwd wins among project dirs" documented? (Q6) | SA § "Choose the subagent scope" precedence table | **Not present in the quoted table.** The base asserts it at `subagents.md:21`. Unconfirmed here |
| Is forking actually cheaper, by how much? (Q3) | SA § "Fork the current conversation" | The claim is made by the vendor about its own product with **no figure, no benchmark, no baseline**. **REPEATED.** Prompt-cache reuse is a documented mechanism; "cheaper" is an unquantified consequence |

**And, distinguishable from the above:** the out-of-scope list at §1.2 is where we
*did not look*, with reasons. Nothing in it should be read as "searched and empty".
The two that matter most for the next stage: the `MEMORY.md` 200-lines/25 KB row in
the existing note, and the SkillsBench quality figure. **Both are unverified and
neither was touched by this sweep.**

---

# 5 · Back-link table

The extend verdict means no new note enters the graph, so no new neighbours are
proposed. What the graph check did turn up is one pre-existing one-sided link on the
note being patched.

| Neighbour named by `subagents.md:8` | Exists? | Names `subagents` back? | Line a human would add |
|---|---|---|---|
| `skill-anatomy` | yes | **no** — `skill-anatomy.md:11` names `skill-authoring-best-practices`, `agent-design-template`, `agent-builder-prior-art` | `related: ["[[skill-authoring-best-practices]]", "[[agent-design-template]]", "[[agent-builder-prior-art]]", "[[subagents]]"]` at `skill-anatomy.md:11` |
| `dynamic-workflows` | yes | yes (`:8`) | — |
| `hooks` | yes | yes (`:10`) | — |
| `claude-code-extension-layer` | yes | yes (`:8`) | — |
| `agent-design-template` | yes | yes (`:15`) | — |
| `agent-builder-prior-art` | yes | yes (`:18`) | — |
| `api-agent-loop` | yes | yes (`:12`) | — |
| `effective-agents-anthropic` | yes | yes (`:9`) | — |
| `managed-agents-architecture` | yes | yes (`:9`) | — |

Nine neighbours, eight reciprocal, one not. I cannot edit `skill-anatomy.md`; the
line above is what a human adds. Unrelated to this patch and noted only because the
same query surfaced it: `claude-code-extension-layer.md:8` still names `[[plugins]]`,
which resolves to nothing — the note is `plugins-and-marketplaces`.

---

# 6 · Status

`status: unverified`. **Nothing in this draft is evidence yet.**

Next: **`primary-source-verifier`**, an agent I have no tool to call and did not
author. It re-fetches all three URLs and rules row by row against section 3 — 35
claim rows and 8 not-found rows — and it, not I, writes any `verified_by:` record.
Particular attention is invited at C12 (a value read from a table column, and one
that moves on its own), C17 (the longest quote, and the one the proposed agent's
remit turns on), and every row whose quote came through `WebFetch` rather than raw
page source, which is all of them.

Then `agent-shape`, which owns the §1.2 finding about whether one definition file is
a sufficient input for the proposed agent at all.
