# Verdict — x2-subagent-limits

**Draft under verification:** `docs/research/drafts/x2-subagent-limits.md`
**Draft's author:** not named in the draft's header. The draft identifies itself as
the output of a research sweep against
`docs/research/commissions/x2-subagent-limits.md` (which itself carries no
`Commissioned by:` field), and states at §6 that the verifier is "an agent I have no
tool to call and did not author". **Not me.** I hold no tool that writes drafts and
nothing in this session produced one. Step 1 does not fire; the document is verified,
not abstained.
**Verified by:** `primary-source-verifier` · 2026-08-29
**Claims in the draft's table:** 38 · **Rows here:** 38 — they match.

> **Row-count discrepancy, recorded before any fetch.** The draft says at §6 that it
> carries "35 claim rows and 8 not-found rows", and its own §3 count line sums to 35.
> The claim table in §3 actually contains **38** rows: 4 + 3 + 5 + 6 + 4 + 16 across
> Q1–Q6, i.e. C1–C36 with `C14b` and the `C29a`/`C29b` split added. My table has 38
> rows because theirs does. Three rows the draft did not count are C14b, C29b and one
> of the Q6 rows; the count line at `drafts/x2-subagent-limits.md:333` is wrong
> arithmetic, not a missing row. Ruled as row X2 below.

Two further tables follow the claim table and are **not** part of the 38: the draft's
§4 "what could not be found measured" rows (N1–N8) and its §2 patch items (P0–P6).
They are ruled because the patch is the sweep's actual deliverable and because two of
them are corrections to an existing verified note. Their verdicts are counted
separately and do not alter the claim-table counts.

## Sources, as fetched

| Source URL | Attempts | What returned | Depth |
|---|---|---|---|
| `https://code.claude.com/docs/en/sub-agents` | 6 (different sections, all successful; not retries) | Full page content, section by section, verbatim on request. Identity confirmed: Claude Code docs, "Subagents". No version stamp on the page, as the draft says | **full text** |
| `https://code.claude.com/docs/en/errors` | **3 of 3 — cap hit** | Page returned, but truncated before the "Configuration warnings" and "Tool errors" sections in all three attempts. Attempt 1: whole-page prompt — "[Content truncated due to length...]". Attempt 2: anchored URL `#agent-would-be-spawned-with-zero-tools` — same truncation, anchor not honoured. Attempt 3: narrowed to exact-string search for `stay in effect until you fix them`, `refuses to spawn`, `unable to accomplish any work`, `deny rules`, `--validate-config` — **every one returned NOT VISIBLE**. The only thing readable was the error-index table, which lists both messages and links to sections I could not reach | **index/table of contents only — the cited section bodies were never returned.** Treated as unreachable for C14, C14b, C19, P0, P6 |
| `https://platform.claude.com/docs/en/about-claude/models/overview` | 1 | Full page. Identity check: the returned document's own frontmatter gives its canonical url as `https://platform.claude.com/docs/en/models/overview` — a shorter path for the same page, consistent with the draft's note that it arrived via a 302. Same document, "Compare models" table present | **full text** |

I did not fetch `code.claude.com/docs/en/env-vars` or `.../settings`. They are named in
the draft's §1.4 search log but are not in its `sources:` frontmatter and no claim row
cites them; opening them would have been corroboration, not verification, and could not
change a verdict.

## Verdicts — the draft's claim table (38 rows)

Quotes below are what the **source** returned to me, not the draft's rendering of it.
Where the draft's quote and mine differ, the row says so. "verbatim ✓" means I compared
word for word and the draft's quote is exact.

### Q1 — nesting / spawn depth

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| C1 | The default nesting depth is three layers of subagents below the main conversation | SA | § "Let subagents spawn their own subagents" | "By default, a subagent can spawn subagents of its own, up to three layers below the main conversation." — draft's quote verbatim ✓ | Read the section's version Note: "**v2.1.172 through v2.1.216**: subagents could nest by default, up to five layers deep… **v2.1.217 through v2.1.218**: the limit defaulted to one… v2.1.219 raised the default to three." Three is the **current** default; the page documents two earlier ones. Kind of number: documented default, matches the claim | `supported` |
| C2 | At the depth limit the `Agent` tool is withheld from every subagent except a fork | SA | same § | "At the depth limit, Claude Code withholds the `Agent` tool from every subagent except a [fork](#fork-the-current-conversation), so a subagent at the limit does its delegated work itself and returns one summary." — verbatim ✓ | Read the **next sentence**, which the draft stops before: "A fork at the limit keeps `Agent` in its inherited tool list, but the tool returns an error instead of spawning." The exception is about the tool remaining *listed*, not about the fork being able to spawn. The claim as written matches the quoted sentence; the qualifier is recorded because the base note repeats the same partial sentence at `subagents.md:91` | `supported` (with the qualifier above) |
| C3 | The depth limit is set by `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, and `1` turns nesting off | SA | same § | "To change the limit, set [`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`](/docs/en/env-vars) to the number of subagent layers you want below your main conversation." … "Set `1` to turn nesting off." — both fragments verbatim ✓ | Read the intervening `settings.json` example, which caps nesting at two layers and confirms the variable is set under `"env"`. The draft's recorded limit (env-vars page unread) is honest and does not affect this row | `supported` |
| C4 | A fork cannot spawn further forks | SA | § "Fork the current conversation" | "A fork can't spawn further forks." — verbatim ✓, located by full-page string search for "further forks" (it did not appear in the section body returned on the first pass) | Searched the whole page for "further forks": exactly one occurrence, the quoted sentence | `supported` |

### Q2 — concurrency

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| C5 | The default concurrent-subagent limit is 20, and spawning past it fails rather than queues | SA | § "Concurrent subagent limit" | "By default, when 20 subagents are running in a session, spawning another with the Agent tool fails with `Concurrent subagent limit reached`, and the error tells Claude not to retry." — verbatim ✓ | Read the rest of the section for anything that would make 20 not the operative default: "Sessions with [ultracode](/docs/en/model-config#adjust-effort-level) active are exempt: the limit isn't enforced there. Requires Claude Code v2.1.217 or later." Also: an in-session fork "takes a slot while it runs and is never blocked by the limit", and resuming a finished subagent "takes a fresh slot without checking the limit, so resumes can push the running count past it". None of this contradicts the claim; all of it is absent from the draft and from the base note | `supported` (exemptions recorded, see observation O2) |
| C6 | Capacity recovers automatically as running subagents finish | SA | same § | "Spawning succeeds again when the running count drops below the limit." — verbatim ✓ | The resume/fork slot rules above are the only qualifications and they concern acquiring slots, not releasing them | `supported` |
| C7 | The concurrency limit is set by `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, any positive whole number | SA | same § | "To change the limit, set [`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`](/docs/en/env-vars) to any positive whole number." — verbatim ✓ | Same section read in full; no other configuration path stated | `supported` |

### Q3 — context

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| C8 | A subagent runs in its own context window | SA | § overview | "Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions." — verbatim ✓, located by string search for "own context window" | Searched the page for any token or character size attached to a subagent's context window: **NOT PRESENT**. The claim's own limit cell ("no size given") holds | `supported` |
| C9 | A subagent does not see the parent's history, previously invoked skills, or previously read files | SA | § "Subagents start fresh" | "Each subagent starts with a fresh, isolated context window. It doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read." — verbatim ✓ | **This is the row's important finding, and it is against the draft's annotation, not its claim.** The claim is carried exactly. The draft's limit cell says "this quote does not mention CLAUDE.md either way; the base's claim that CLAUDE.md **is** injected rests on its own 2026-08-28 probe, not on this page". I searched the whole page for "CLAUDE.md" and it **is** on this page: "**CLAUDE.md files**: every level of the [CLAUDE.md hierarchy](/docs/en/memory#how-claude-md-files-load) the main conversation loads, including `~/.claude/CLAUDE.md`, project rules, `CLAUDE.local.md`, and managed policy files. The built-in Explore and Plan agents skip this." and "Explore and Plan are the only subagents that omit CLAUDE.md and git status." The claim: `supported`. The annotation: ruled separately at N6 | `supported` |
| C10 | A fork is the exception and inherits the whole parent conversation | SA | § "Fork the current conversation" | "A fork is a subagent that inherits the entire conversation so far instead of starting fresh." and "The exception is a [fork](#fork-the-current-conversation), which inherits the parent conversation instead of starting fresh." — both verbatim ✓, the second from the "starts fresh" section | Read the fork section in full: "a fork sees the same system prompt, tools, model, and message history as the main session" — consistent, and stronger than the claim | `supported` |
| C11 | A fork's first request reuses the parent's prompt cache, making it cheaper than a fresh subagent | SA | § "Fork the current conversation" | "Because a fork's system prompt and tool definitions are identical to the parent, its first request reuses the parent's [prompt cache](/docs/en/prompt-caching#subagents-and-the-cache)." and "This makes forking cheaper than spawning a fresh subagent for tasks that need the same context." — both verbatim ✓ | Searched the whole page for "cheaper": exactly one occurrence, the sentence quoted. **No figure, no benchmark, no baseline anywhere on the page.** The draft's own split — mechanism MEASURED, "cheaper" REPEATED — is the correct reading and I confirm it. The source carries the sentence, so the row is supported; what it does not carry is a number, and the claim does not assert one | `supported` |
| C12 | **POINTER, re-fetch.** Claude Opus 5's context window is 1M tokens | MO | § "Compare models", "Context window" row | Column headers in order: "Claude Fable 5 \| Claude Opus 5 \| Claude Sonnet 5 \| Claude Haiku 4.5". Row: "[Context window] \| 1M tokens \| 1M tokens \| 1M tokens \| 200K tokens". **Opus 5 = 1M tokens** ✓, and the draft's column order is correct | Re-fetched today rather than trusting the draft's cell, as the row asks. Checked the kind of number: this is the model's context window, not a subagent limit, and the draft says so. Checked the footnote: the draft quotes "**Context window:** 1M tokens is roughly 555k words or 2.5M Unicode characters on the current tokenizer" and **stops mid-sentence without an ellipsis**; the source continues "(introduced with Claude Opus 4.7); models before it fit about 750k words in 1M tokens. 200k tokens is roughly 150k words." Truncation, not distortion | `supported` |

### Q4 — tool inheritance

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| C15 | Omitting `tools` inherits every tool available to subagents | SA | frontmatter table, `tools` row | "[Tools](#available-tools) the subagent can use. Inherits every tool available to subagents if omitted." — draft's quote verbatim ✓ | Read the `disallowedTools` and `background` rows and the "Available tools" section for anything that makes the inheritance broader than "available to subagents": nothing does. The word "available" is doing real work — see C16/C17 | `supported` |
| C16 | Inheritance is narrowed by two filters before any definition is considered | SA | § "Available tools" | "Subagents inherit the [built-in tools](/docs/en/tools-reference) and MCP tools available in the main conversation, narrowed by two filters: the first removes a short list of tools from every subagent, and the second reduces the built-in tool set for subagents that run in the [background](#run-subagents-in-foreground-or-background), which is the default." The draft's quote replaces the source's colon with an ellipsis but is otherwise word-for-word ✓ | **The disconfirming read overturned the draft's annotation, not its claim.** The draft's limit cell says "the quote as rendered elides the first filter's membership ('a short list') — the actual list of always-removed tools was not obtained". Requesting the section verbatim returned the enumeration immediately: "The first filter removes these tools, even when listed in the `tools` field: `Agent`, when the subagent is at the depth limit…; `AskUserQuestion`; `EndConversation`…; `EnterPlanMode`; `ExitPlanMode`, unless the subagent's `permissionMode` is `plan`; `ScheduleWakeup`; `TaskOutput`; `WaitForMcpServers`; `Workflow`" — nine entries. Also found, and absent from the draft: "[Forks](#fork-the-current-conversation) skip both filters and receive the main conversation's exact tool pool." The claim itself is carried exactly. The annotation is ruled at N5 | `supported` |
| C17 | A background subagent keeps only a named set of built-ins, and the removal applies even to tools the definition lists | SA | § "Available tools" | "Apart from `Agent` and `ExitPlanMode`, which follow the first filter's conditions wherever the subagent runs, a background subagent keeps every MCP tool but only these built-in tools: `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage`, and `Artifact`. Claude Code removes every other built-in tool from a background subagent, whether inherited or listed in the `tools` field, so the same definition can resolve to different tools in the foreground and the background." — **verbatim ✓, the longest quote in the draft and exact throughout**, including tool order | The draft flags this as the row its proposed agent turns on, so I checked the count and the sentences either side. Count of named built-ins: **19**, matching the draft's cell (Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact). Two adjacent sentences the draft omits and that qualify the list: "The removal reports no error unless it leaves the `tools` list [resolving to nothing](/docs/en/errors#agent-would-be-spawned-with-zero-tools)" and "[`ListAgents`](/docs/en/cross-session-messaging) follows these filters like any built-in tool: a foreground subagent inherits it… and a background subagent doesn't keep it." Neither contradicts the claim | `supported` |
| C18 | If no entry in `tools` resolves to a tool, the subagent usually fails to launch, and the error names the entries | SA | frontmatter table, `tools` row | "If no entry in the list resolves to a tool, the subagent usually [fails to launch](/docs/en/errors#agent-would-be-spawned-with-zero-tools) with an error naming the entries." — verbatim ✓ | The "usually" hedge the draft flags is the source's own word, confirmed. The conditions under which it does not fail are on the Errors page, which I could not read — recorded, and it does not change this row | `supported` |
| C19 | Claude Code refuses to spawn a subagent with no usable tools | ER | § "would be spawned with zero tools — refusing" | **No quote obtained.** The Errors page returned only its error-index table, which contains the row "`would be spawned with zero tools — refusing` \| [Tool errors](#agent-would-be-spawned-with-zero-tools)". The section body never returned in three attempts, including a request for the exact strings "refuses to spawn", "no tools" and "unable to accomplish any work", all of which came back NOT VISIBLE | Attempt 2 used the anchored URL and attempt 3 used exact-string search — both are the disconfirming reads, and both failed to reach the text. I cannot confirm or deny the draft's quote. Note the error message *title* is corroborated by the index row and by the SA page's link to the same anchor, but a title is not the sentence the draft quotes | `source-unreachable` (3 of 3) |
| C20 | `disallowedTools` removes tools from either the inherited set or an explicit `tools` list | SA | frontmatter table, `disallowedTools` row | "Tools to deny, removed from inherited or specified list" — verbatim ✓ | Full frontmatter table read; no other `disallowedTools` semantics stated | `supported` |

### Q5 — preloaded skills

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| C21 | `skills:` injects the **full content** of each listed skill at startup | SA | § "Preload skills into subagents"; frontmatter table | "The full content of each listed skill is injected into the subagent's context at startup." and, from the `skills` row, "The full skill content is injected, not only the description." — both verbatim ✓ | Read the whole section for size accounting attached to the injection: none stated, as the draft's limit cell says | `supported` |
| C22 | `skills:` controls preloading, not access — without it a subagent can still discover and invoke skills through the Skill tool | SA | § "Preload skills into subagents" | "This field controls which skills are preloaded, not which skills the subagent can access: without it, the subagent can still discover and invoke project, user, and plugin skills through the Skill tool during execution." — verbatim ✓ | **Annotation overturned, claim intact.** The draft's limit cell says "this page does not restate the exclusion of `disable-model-invocation: true` skills that `subagents.md:46` asserts; **not checked here**". The section carries it plainly: "You can't preload skills that set [`disable-model-invocation: true`](/docs/en/skills#control-who-invokes-a-skill), since preloading draws from the same set of skills Claude can invoke. This includes the bundled `/verify` skill: only you can run it, so it can't be preloaded either." The base note's `:46` claim is therefore documented, not unchecked. Ruled at X3 | `supported` |
| C23 | To preload skills, use `skills` rather than listing `Skill` in `tools` | SA | frontmatter table, `tools` row | "To preload Skills into context, use the `skills` field rather than listing `Skill` here" — verbatim ✓ | The § "Preload skills into subagents" gives the converse: "To prevent a subagent from invoking skills entirely, omit `Skill` from the [`tools`](#available-tools) list or add it to `disallowedTools`" — consistent | `supported` |
| C24 | There is **no documented numeric cap** on how many skills may be preloaded | SA | § "Preload skills into subagents", frontmatter table | **No quote — the claim is a negative and cannot have one.** Evidence is absence after a directed read: the section returned in full contains no number; the `skills` frontmatter row reads in full "Skills to preload into the subagent's context at startup. The full skill content is injected, not only the description. Subagents can still invoke unlisted project, user, and plugin skills through the Skill tool" — no count, no cap | Ran an explicit adversarial query against the page — "any sentence stating a maximum number of skills that can be preloaded" — which returned "**Not present**". The only failure mode documented for the field is per-skill, not per-count: "If a listed skill is missing or disabled… Claude Code skips it and logs a warning to the debug log" | `supported` (absence after directed search; see note on negative claims below) |

### Q6 — what is checkable in one file

| # | Claim, verbatim from the draft | Cited source | Locator | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|---|
| C13 | Combined descriptions of all non-built-in subagents over 15,000 tokens trigger a startup **warning** | SA | § "Create custom subagents" | "Those descriptions take up context, so keep them short. When the combined descriptions of your subagents, except the built-in ones, exceed 15,000 tokens, Claude Code shows a [warning at startup with the total token count](/docs/en/errors#agent-descriptions-are-over-the-15000-token-limit). Trim the `description` fields of your subagents, and move detail into each subagent's system prompt, which only loads when that subagent runs." — verbatim ✓ | Kind of number checked: **combined across the roster, built-ins excluded**, and the consequence is a *warning*, not a rejection — both as the claim states. The claim's "not checkable from one definition file" cell is a correct inference from the quoted sentence | `supported` |
| C14 | The Errors page describes the same threshold as a limit, and states nothing is rejected | ER | § "Agent descriptions are over the 15.0k-token limit" | **No quote obtained.** The heading text is corroborated by the error-index row "`Agent descriptions are over the 15.0k-token limit` \| [Configuration warnings](#agent-descriptions-are-over-the-15000-token-limit)" — so the *title* exists and does say "limit". The body the draft quotes ("the agent descriptions stay in effect until you fix them", the three remedies) never returned; an exact-string search for "stay in effect until you fix them" and "--validate-config" returned NOT VISIBLE for both | Attempts 2 and 3 were the disconfirming reads (anchored URL, then literal-string search). Neither reached the body. **The half of the claim that says the page calls it a limit is corroborated by the index; the half that says it states nothing is rejected is not verified at all**, and that half is what P6 rests on | `source-unreachable` (3 of 3) |
| C14b | **Disagreement row.** The two pages differ in wording, not in behaviour | SA + ER | as C13, C14 | SA half confirmed verbatim: "shows a [warning at startup with the total token count]". ER half **not obtained** — neither the "stay in effect" sentence nor the "in your Claude Code config file" remedy was visible in three attempts | A disagreement row needs both sides. One side is unread, so the claim that the difference is "wording, not behaviour" cannot be settled — it is exactly the kind of row where an unread half would be filled in by assumption | `source-unreachable` (3 of 3, ER half) |
| C25 | `name` is required and must be lowercase letters and hyphens | SA | frontmatter table, `name` row | "Unique identifier using lowercase letters and hyphens." … "The filename doesn't have to match." — verbatim ✓; the row's Required column reads "Yes" | Full row read, including the sentence between the two fragments: "[Hooks](/docs/en/hooks#subagentstart) receive this value as `agent_type`" | `supported` |
| C26 | A `name` containing `:` causes the file not to load, with an error to the debug log — and this changed in v2.1.218 | SA | frontmatter table, `name` row | "Names can't contain `:`, which is reserved for [plugin-scoped identifiers](/docs/en/plugins) such as `my-plugin:reviewer`. Claude Code doesn't load a file whose name contains one and logs an error to the debug log. Before v2.1.218, such names were accepted" — verbatim ✓ | Version gate direction checked: the source says such names were accepted **before** v2.1.218, i.e. the *rejection* is the new behaviour. The draft's phrasing "this changed in v2.1.218" is consistent with that direction, and its limit cell (a static check needs the target version) follows | `supported` |
| C27 | `description` is required, and its purpose is delegation | SA | frontmatter table, `description` row | "When Claude should delegate to this subagent" — verbatim ✓; Required column "Yes" | The whole row is that one sentence; nothing further to read | `supported` |
| C28 | `model` defaults to `inherit` when omitted | SA | § "Choose a model" / frontmatter table | § "Choose a model": "**Omitted**: defaults to `inherit` and uses the same model as the main conversation" — verbatim ✓. Frontmatter `model` row independently: "…or `inherit`. Defaults to `inherit`" | Two independent locations on the page agree | `supported` |
| C29a | `maxTurns` output at the limit is returned marked partial and can be resumed | SA | frontmatter table, `maxTurns` row | "Maximum number of agentic turns before the subagent stops. When the subagent reaches the limit, Claude Code returns its output marked as partial, and Claude can [resume it](#resume-subagents) to continue. The partial marking requires Claude Code v2.1.246 or later" — verbatim ✓ | Version gate confirmed as stated | `supported` |
| C29b | `maxTurns` has **no documented default and no documented maximum** | SA | frontmatter table | **No quote — negative.** The full `maxTurns` row is quoted at C29a and contains neither a default nor an upper bound | Ran a directed search for a default or upper bound for `maxTurns` **outside** the frontmatter table, including the resume section: "**NOT PRESENT.** The page defines the `maxTurns` field in the frontmatter table but provides no sentence stating a default value or upper bound outside the table" | `supported` (absence after directed search) |
| C30 | `permissionMode` is ignored for plugin subagents | SA | frontmatter table, `permissionMode` row | "…Ignored for [plugin subagents](#choose-the-subagent-scope)" — verbatim ✓, as the row's final clause | Three rows carry this clause; checked that this is one of them and not a copy from a neighbour | `supported` |
| C31 | `mcpServers` is ignored for plugin subagents | SA | frontmatter table, `mcpServers` row | "…Ignored for [plugin subagents](#choose-the-subagent-scope)" — verbatim ✓ | as C30 | `supported` |
| C32 | `hooks` is ignored for plugin subagents | SA | frontmatter table, `hooks` row | "[Lifecycle hooks](#define-hooks-for-subagents) scoped to this subagent. Ignored for [plugin subagents](#choose-the-subagent-scope)" — verbatim ✓ | as C30. The draft's limit cell (whether a file *is* a plugin subagent is a function of location) is confirmed by the scope table at C35, where the plugin `agents/` directory is a location | `supported` |
| C33 | `experimental.cacheTtl` accepts only `5m` or `1h`, is read only from subagent files, and requires v2.1.248+ | SA | frontmatter table, `experimental` row | "Map of experimental options. Set its `cacheTtl` key to `5m` or `1h` to choose the [prompt cache lifetime](/docs/en/prompt-caching#choose-the-ttl-yourself) for this subagent's requests. Claude Code ignores any other value, ignores `1h` while your Claude subscription is using usage credits, and reads the field only from subagent files. Requires Claude Code v2.1.248 or later" — verbatim ✓ | Found a further sentence elsewhere on the page, from the "prompt cache" search: "Write `cacheTtl` inside the `experimental` map, not at the top level of the frontmatter." Consistent, and additional | `supported` |
| C34 | `permissionMode: manual` is an alias for `default` and requires v2.1.200+ | SA | frontmatter table, `permissionMode` row | "[Permission mode](#permission-modes): `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, or `manual` as an alias for `default`. The `manual` alias requires Claude Code v2.1.200 or later." — verbatim ✓ | Enumeration checked member by member against the draft's quote: seven values, same order | `supported` |
| C35 | Subagent definitions resolve by a five-level precedence, managed settings highest, plugin `agents/` lowest | SA | § "Choose the subagent scope", precedence table | Table returned with four columns (Location, Scope, Priority, How to create). Priority column: "Managed settings — 1 (highest); `--agents` CLI flag — 2; `.claude/agents/` — 3; `~/.claude/agents/` — 4; Plugin's `agents/` directory — 5 (lowest)" — the draft's rendering is exact ✓, five rows | **Annotation overturned, claim intact.** The draft's limit cell says the page's table "does not carry the base note's extra claim that 'closest-to-cwd wins among project dirs'" — true of the table, but I searched the page for "cwd", "closest" and "working directory" and the prose carries it: "Project subagents are discovered by walking up from the current working directory, so every `.claude/agents/` between there and the repository root is scanned. As of v2.1.178, when more than one of these nested directories defines the same `name`, Claude Code uses the definition closest to the working directory." Ruled at N7 | `supported` |
| C36 | There is **no documented size limit** on a subagent definition file or its system prompt | SA | whole page | **No quote — negative.** No size cap appears in the frontmatter table, the "Create custom subagents" section, or anywhere the page discusses definition files | Ran two directed adversarial searches: "any sentence stating a maximum size, length, or line/byte limit for a subagent definition file or its system prompt" → "**Not present**"; and "any sentence giving a token or character size for a subagent's context window" → "**NOT PRESENT**". The only size-shaped constraints on the page are the roster-wide 15,000-token description budget (C13) and the `MEMORY.md` 200-line/25 KB cap (see X1) — neither is a cap on the definition file | `supported` (absence after directed search) |

**Note on the four negative rows (C24, C29b, C36, and N1–N3 below).** A claim of the
form "the source does not document X" cannot carry a quote, and `not-in-source` would
be the wrong word for it — that verdict says *the claim* is absent from the source,
whereas here the claim is precisely that *X* is absent. Each of these rows is ruled
`supported` only where I ran a directed search designed to find X, in the vocabulary
most likely to surface it, and it returned nothing. The search terms are recorded in
each row so a later reader can rerun them. Where such a search **did** surface X, the
row is ruled `not-supported` — which is what happened three times below.

## Counts

| Verdict | Rows |
|---|---|
| supported | 35 |
| not-supported | 0 |
| not-in-source | 0 |
| source-unreachable | 3 |
| not-checkable | 0 |
| **total** | **38 — equals the draft's claim table** |

The three `source-unreachable` rows are C14, C14b and C19, all of them the rows that
rest on `code.claude.com/docs/en/errors`.

## Verdicts — the draft's §4 "what could not be found measured" (8 rows, counted separately)

These are the draft's negative findings. They are not in its claim table, but they are
claims about what the sources do and do not say, and the patch and the next stage both
lean on them.

| # | Finding, verbatim from the draft §4 | Source | Quote from the source | Disconfirming read | Verdict |
|---|---|---|---|---|---|
| N1 | "**No cap documented.** The field's description states what is injected, never how many may be" | SA | no quote — negative, evidence as C24 | directed search for a maximum number of preloadable skills → "Not present" | `supported` |
| N2 | "**Neither is stated.** The row documents behaviour at the limit, not the limit's bounds" | SA | no quote — negative, evidence as C29b | directed search outside the frontmatter table → "NOT PRESENT" | `supported` |
| N3 | "**None stated.** So 'this agent body is too long' is a **quality** finding, never a limit finding" | SA | no quote — negative, evidence as C36 | two directed searches, both "Not present" | `supported` |
| N4 | "**Not reached; attempt cap hit at 3.** The defaults of 3 and 20 rest on the Subagents page alone (C1, C5)" | — | This row is a claim about the researcher's own fetch attempts against `env-vars` and `settings`, not about the content of a cited source. I cannot verify another agent's attempt history, and I did not fetch those two pages because no claim row cites them | The substantive half is checkable and holds: across six reads of the Subagents page, the values 3 and 20 appear only there, and I found no second cited source for either | `not-checkable` — what would settle it: a fresh fetch of `code.claude.com/docs/en/env-vars` by a later sweep, which would either supply the corroboration or confirm the gap |
| N5 | "The page says 'a short list of tools' and, as rendered, does not enumerate it. **Membership unknown.** A reviewer agent cannot tell a user which tools its `tools:` list will lose unconditionally" | SA | **The source enumerates it.** § "Available tools": "The first filter removes these tools, even when listed in the `tools` field: `Agent`, when the subagent is at the [depth limit](#let-subagents-spawn-their-own-subagents); in a [fork](#fork-the-current-conversation) the tool stays listed but returns an error instead of spawning · `AskUserQuestion` · `EndConversation`, which can end only the main conversation · `EnterPlanMode` · `ExitPlanMode`, unless the subagent's [`permissionMode`](#permission-modes) is `plan` · `ScheduleWakeup` · `TaskOutput` · `WaitForMcpServers` · `Workflow`" — nine entries, three of them conditional | Disconfirming read run: I asked for the **whole "Available tools" section verbatim** rather than for the sentence the draft quoted, on the theory that the enumeration was a bullet list the draft's summarising fetch had dropped. It was. The list is in the same section, immediately after the sentence the draft did quote | `not-supported` |
| N6 | "**The page's quoted sentence names three exclusions and does not mention CLAUDE.md either way.** The base's positive claim (`subagents.md:70`) comes from its own 2026-08-28 canary probe, not from this documentation. Two different kinds of evidence; do not merge them" | SA | **The page documents it.** "**CLAUDE.md files**: every level of the [CLAUDE.md hierarchy](/docs/en/memory#how-claude-md-files-load) the main conversation loads, including `~/.claude/CLAUDE.md`, project rules, `CLAUDE.local.md`, and managed policy files. The built-in Explore and Plan agents skip this." Also: "Explore and Plan are the only subagents that omit CLAUDE.md and git status." and "The main conversation reads Explore and Plan results with full CLAUDE.md context, so most rules don't need to reach the subagent itself." | Disconfirming read run: full-page search for the literal string "CLAUDE.md" rather than re-reading the "starts fresh" section. Three occurrences, all of them documenting that the hierarchy loads. The narrow half of the finding is true — the *"starts fresh"* sentence is silent on CLAUDE.md — but the conclusion drawn from it, that the base's claim rests only on a local probe, is contradicted by the same page the draft fetched | `not-supported` |
| N7 | "**Not present in the quoted table.** The base asserts it at `subagents.md:21`. Unconfirmed here" | SA | **The page documents it, in prose rather than in the table.** "Project subagents are discovered by walking up from the current working directory, so every `.claude/agents/` between there and the repository root is scanned. As of v2.1.178, when more than one of these nested directories defines the same `name`, Claude Code uses the definition closest to the working directory." | Disconfirming read run: searched a second vocabulary — "cwd", "closest", "working directory" — instead of re-reading the precedence table. The base note's `:21` claim is documented and carries a version gate (v2.1.178) the base note does not record | `not-supported` |
| N8 | "The claim is made by the vendor about its own product with **no figure, no benchmark, no baseline**. **REPEATED.**" | SA | no quote — negative | full-page search for "cheaper": one occurrence, no number attached; full-page search for "prompt cache": three occurrences, none quantified | `supported` |

**§4 counts:** supported 4 · not-supported 3 · not-checkable 1 · total 8.

## Verdicts — the draft's §2 patch items (7 rows, counted separately)

The patch is what a human would apply to `/home/user/skills-repo/knowledge/notes/subagents.md`.
Two of these are corrections to an existing `status: verified` note, which is the
highest-stakes thing in the document.

| # | Patch item | Rests on | Verdict | Basis |
|---|---|---|---|---|
| P0 | add the Errors page to `sources:` and update the fetch date | C14, C19 | `source-unreachable` | The two claims that would justify listing the Errors page are the two I could not verify. **Do not add a source to the frontmatter on the strength of unverified rows.** The fetch-date half is fine and independent |
| P1 | `maxTurns` row: keep "no default or maximum documented", add the documented behaviour at the limit and the v2.1.246 gate | C29a + C29b | `supported` | Both halves verified verbatim above. The replacement text's wording matches the source's, including "marked as partial" and the version gate |
| P2 | **correction.** Replace the background tool list; add "whether inherited or listed in the `tools` field" | C17 | `supported`, **incomplete** | The 19-tool list and the load-bearing clause are both verbatim from the source (C17), and the draft's diagnosis is right: the base note's "background silently drops non-listed built-ins" (`subagents.md:112`) does read as though listing a tool protects it, and the source says it does not. Two things the replacement text omits, both in the same source section: forks "skip both filters and receive the main conversation's exact tool pool", and the first filter's nine named tools are removed "even when listed in the `tools` field" **in the foreground too**. As written, the patch fixes the background half of the misreading and leaves the foreground half unstated. That is an improvement I may not make for them — recorded, not applied |
| P3 | **correction.** `tools` omitted: "inherit ALL" → "inherit every tool available to subagents (already narrowed by two filters)" | C15 + C16 | `supported` | The documented wording "Inherits every tool available to subagents if omitted" is verbatim (C15), and the two filters are verbatim (C16). The correction is right and, given N5, the draft could have made it stronger: the nine always-removed tools are now known and could be named |
| P4 | add `initialPrompt` and `experimental` to the frontmatter field list | C33 + the field table | `supported` | Both fields are present in the source's frontmatter table and are absent from `subagents.md:36-38`. `initialPrompt`, verbatim: "Auto-submitted as the first user turn when this agent runs as the main session agent (via `--agent` or the `agent` setting). [Commands](/docs/en/commands) and [skills](/docs/en/skills) are processed. Prepended to any user-provided prompt". `experimental` as at C33 |
| P5 | "The values at `:90-93` were re-confirmed today and **none changed**" + append a provenance line | C13, C1–C3, C5, C7 | `supported` **in substance, not in process** | I independently re-read all four rows against the source today. `:90` 15,000 tokens ✓ (C13); `:91` depth 3 + env var + Agent withheld ✓ (C1–C3); `:92` concurrent 20 + env var ✓ (C5, C7); `:93` `MEMORY.md` first 200 lines or 25 KB ✓ — "The subagent's system prompt also includes the first 200 lines or 25KB of `MEMORY.md` in the memory directory, whichever comes first, with instructions to curate `MEMORY.md` if it exceeds that limit." So the *values* claim holds. But the draft cannot have re-confirmed `:93`: its own §1.2 says that row "was **not checked by this sweep** and remains unverified". The patch and the scope contract contradict each other over the same line. See X1 |
| P6 | add a row describing the SA/ER wording mismatch | C13 + C14 + C14b | `source-unreachable` | The SA half is verified; the ER half is not, in three attempts. A row asserting that two pages "differ in wording, not in behaviour" cannot be added to a verified note when one of the two pages was never read. This is the item I would hold back hardest |

**Patch counts:** supported 5 · source-unreachable 2 · total 7.

## Verdicts — claims in the draft's body with no row in its claim table

Recorded per the procedure's step 2: a claim in the body with no row of its own is
itself a finding.

| # | Claim, verbatim | Source stated | Verdict | Basis |
|---|---|---|---|---|
| X1 | §1.2, out-of-scope row: "`memory:` persistence and the `MEMORY.md` size limit … Concerns cross-session persistence, **documented on a separate page**. **Consequence to record:** the existing note's row … was **not checked by this sweep** and remains unverified" | none stated | `not-supported` | The `MEMORY.md` limit is **on the Subagents page the sweep read six times**, not on a separate page: "The subagent's system prompt also includes the first 200 lines or 25KB of `MEMORY.md` in the memory directory, whichever comes first…". Disconfirming read: I searched the page for "MEMORY.md", "25 KB" and "200 lines" specifically because the draft asserted they were elsewhere. The scope exclusion rests on a false premise, and it collides with P5's claim to have re-confirmed `:90-93`. **The base note's `:93` row is in fact supported** — by my read today, not by the draft's |
| X2 | §3 count line and §6: "35 claim rows"; "**Verdict counts.** MEASURED: 31 rows … REPEATED: 4" | the draft itself | `not-supported` | Checked at the artefact, `docs/research/drafts/x2-subagent-limits.md:265-331`: Q1 4 rows, Q2 3, Q3 5, Q4 6, Q5 4, Q6 16 = **38**. 31 + 4 = 35 ≠ 38. No row is missing from the table; the arithmetic under it is wrong. This matters because a downstream gate that compares verdict rows to claim rows would compare against a stated 35 and pass a document that had skipped three |
| X3 | C22 limit cell: "this page does not restate the exclusion of `disable-model-invocation: true` skills that `subagents.md:46` asserts; **not checked here**" | SA | `not-supported` | The page states it in the same section the draft quoted from: "You can't preload skills that set [`disable-model-invocation: true`](/docs/en/skills#control-who-invokes-a-skill), since preloading draws from the same set of skills Claude can invoke. This includes the bundled `/verify` skill: only you can run it, so it can't be preloaded either." Disconfirming read: I requested the whole "Preload skills into subagents" section verbatim rather than the sentence the draft cited. The base note's `:46` claim is documented |

**Body-claim counts:** not-supported 3 · total 3.

## Observations for the human who applies the patch

Recorded here, not in any note, because I add no claim of my own to the base. Each is
something I read in a cited source that the draft did not carry.

- **O1 — `subagents.md:91` repeats the draft's partial sentence.** The base note says
  "At the depth limit Claude Code **withholds the `Agent` tool from every subagent
  except a fork**". The source's next sentence: "A fork at the limit keeps `Agent` in
  its inherited tool list, but the tool returns an error instead of spawning." A reader
  of the base note would conclude a fork at the limit can still spawn. It cannot.
- **O2 — the concurrency row has three documented qualifiers the base note omits**
  (`subagents.md:92`): the limit "isn't enforced" in sessions with ultracode active; it
  "Requires Claude Code v2.1.217 or later"; and forks and resumes take slots without
  being blocked by it, so "resumes can push the running count past it".
- **O3 — `subagents.md:99` is wrong on one item.** It lists "total subagents over a
  session's lifetime" under "**Explicitly NOT documented**". The source documents it:
  "There's no limit on the total number of subagents Claude can spawn over a session."
  Documented as *no limit* is not the same as undocumented.
- **O4 — the first filter's nine tools (N5) are the most useful thing this sweep
  found and did not report.** For an agent that reviews a definition file statically,
  "`Agent`, `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode`,
  `ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers`, `Workflow` are removed even when
  listed in `tools`" is exactly a `file:line` check. It is absent from the base note and
  from the patch.
- **O5 — `subagents.md:94` (`cleanupPeriodDays`, default 30) is confirmed** by the same
  page: "Claude Code deletes subagent transcripts after the `cleanupPeriodDays`
  retention period, 30 days by default…". Not a draft claim; recorded because I read it.

## URLs fetched

In order, all three from the draft's `sources:` frontmatter and nothing else:

1. `https://code.claude.com/docs/en/sub-agents` — 6 reads, each targeting different
   sections (nesting/concurrency/fork; available tools + prompt-cache/fork strings;
   frontmatter table; 15k paragraph + intro + starts-fresh + scope table; preload-skills
   section; disconfirming searches for CLAUDE.md, maxTurns bounds, foreground/background,
   context size, MEMORY.md, cleanupPeriodDays). All succeeded.
2. `https://code.claude.com/docs/en/errors` — 3 reads, cap reached, cited sections never
   returned.
3. `https://platform.claude.com/docs/en/about-claude/models/overview` — 1 read,
   succeeded.

## Corroboration — read, but not cited by the draft

**Empty.** I opened no source the draft did not cite. I deliberately did not fetch
`code.claude.com/docs/en/env-vars` or `code.claude.com/docs/en/settings`, which appear
in the draft's §1.4 search log but not in its `sources:` and carry no claim row: reading
them could only have produced corroboration for C1/C3/C5/C7, and corroboration never
changes a verdict. N4 is ruled `not-checkable` for that reason rather than resolved by
going around it.

Repository files read (not sources, and not corroboration — these are the artefacts the
draft makes claims *about*, checked at `file:line` per the procedure's scope):
`/home/user/skills-repo/knowledge/notes/subagents.md`,
`/home/user/hello-world/docs/research/commissions/x2-subagent-limits.md`.

## What this document does not establish

- **Whether the claims are true.** Only whether the cited source carries them. Where a
  source is a vendor documenting its own product — which is every source here — "the
  source carries it" means the vendor asserts it, and the draft's own C11 split is the
  right instinct: `supported` on a vendor page is not a measurement.
- **Whether the three `source-unreachable` rows are right or wrong.** They are unread.
  A later verifier with a working path to the Errors page should rule C14, C14b and C19
  and only then may P0 and P6 be applied.
- **Whether the sweep asked the right questions.** That is `agent-shape`'s judgement
  against the scope contract at §1. I note only that the contract's §1.2 exclusion of
  `MEMORY.md` rests on a false premise (X1), which is a fact about the source and
  therefore mine to rule.
- **Whether the honesty of these rulings can be checked.** Nothing downstream checks
  it. Every row above names the URL it was read from and quotes the line, so a second
  verifier can rerun any of them; the three `not-supported` rows (N5, N6, N7) each name
  the search string that overturned the draft's finding, which is the cheapest thing to
  re-run first.
