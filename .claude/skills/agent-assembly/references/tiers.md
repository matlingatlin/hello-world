# The placement test

One question decides every piece of content:

> **Does this need to be in context on every turn?**

No → it moves down a tier. Down is nearly free; up is paid forever.

| Tier | Loads | Cost | Belongs here |
|---|---|---|---|
| 0 · agent body | every invocation | paid always | identity, boundary, the map of functions |
| 1 · `skills:` | full body at start | 5,000 tokens each re-attached at compaction, 25,000 shared | the procedures — at most three |
| 2 · `CLAUDE.md` | every session, **reaches subagents** | small | rules binding every agent in the repo |
| 3 · `references/` | when a step opens it | zero until read | knowledge, tables, pointers to the base |
| 4 · `assets/` | at the emit step | zero until read | templates |
| 5 · hook | executed, never read | zero context | what must be impossible |

## Why tiering, given a 1M-token window

Not scarcity. All 84 library skills together are ~176,000 tokens — 18% of Opus 5's
context. An argument from running out of room would collapse the next time the
window grows. The three real reasons:

1. **Measured quality.** 1–3 preloaded modules ≈ +19.0pp; 4+ ≈ +10.1pp. More
   performed *worse* with the window nowhere near full. Dilution, not capacity.
2. **Silent truncation.** Compaction re-attaches 5,000 tokens per skill against a
   25,000 shared budget, most recent first. A bigger window delays it; it does not
   change what happens, and the loss is not announced.
3. **The system prompt shapes every turn.** Length in tier 0 costs judgement.

## What is NOT a limit

- No documented cap on an agent definition file or its system prompt.
- "Under 500 words for a SKILL.md" is one library's house convention, broken by 68
  of its own 84 talents including the skill that states it, at 6.6× over. Anthropic's
  own guidance says under 500 *lines* and to go longer when needed.

Design against the documented numbers, never against a remembered one.

## The one hard shared budget

**All non-built-in agent descriptions together must stay under 15,000 tokens** or
Claude Code warns at startup. Per agent that is generous; it is shared across the
roster, so it bites as the roster grows rather than when any one agent is written.

## Where rules go, now that `rules/` is ruled out

Measured 2026-08-28 by canary probe: `.claude/rules/` — scoped and unscoped — does
**not** reach a subagent. Only `CLAUDE.md` was injected.

| Rule binds | Put it in |
|---|---|
| every agent in the repo | `CLAUDE.md` |
| this agent, always | the agent body |
| one procedure | the preloaded skill |
| one step | a reference file that step opens |
