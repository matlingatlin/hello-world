# Limits — GENERATED, do not edit

Regenerate with `python3 .claude/validate/agents.py --limits`.

Hand-editing this file reintroduces exactly the drift it exists to prevent:
the checker would keep enforcing its own constants while the template told
the writer something else.

| Limit | Value | Source | Note |
|---|---|---|---|
| description, max characters | **1024** | [A] Anthropic, skills guide | frontmatter enters a system prompt; the cap is Anthropic's |
| compatibility, max characters | **500** | [A] Anthropic, skills guide |  |
| SKILL.md body, max words | **5000** | [A] Anthropic, skills guide | guidance for SKILL.md — NOT a limit on an agent body |
| combined agent descriptions, max tokens | **15000** | [B] subagents docs | shared by every non-built-in agent; Claude Code warns at startup |
| preloaded skills per agent, max | **3** | [M] measured here | 1-3 modules ~+19.0pp, 4+ ~+10.1pp — a quality finding, not a documented cap |

Reserved words in a skill name: claude, anthropic [A]

