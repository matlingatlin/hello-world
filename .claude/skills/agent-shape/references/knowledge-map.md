# Knowledge map — what to open, and when

You do not carry this knowledge. You **query** it. Copies drift; the base does not.

Base: `/home/user/skills-repo/knowledge/notes/`. Every note carries per-claim
**MEASURED** (a study with numbers) or **REPEATED** (asserted, no measurement).
Never cite a REPEATED claim as though it were measured.

| Open this | When | It settles |
|---|---|---|
| `agent-design-template.md` | **always, first** | the six loading tiers; where rules/templates/knowledge go; composition patterns with verdicts; two-agents-or-two-skills |
| `subagents.md` | before writing any agent frontmatter | what actually loads into a subagent; the documented limits and what is explicitly *undocumented*; that `.claude/rules/` does **not** reach a subagent |
| `skill-anatomy.md` | before writing a SKILL.md | frontmatter fields, which survive upload, the compaction re-attach budget |
| `hooks.md` | when the boundary must be a wall | which event fires when, and that PreToolUse precedes every permission check |
| `claude-md-and-memory.md` | when placing repo-wide rules | load order, the 200-line target, path-scoped rules |
| `dynamic-workflows.md` | only past ~a handful of agents | the script-holds-the-plan tier; caps; `acceptEdits` for spawned agents |
| `mcp.md` | when the agent needs live facts rather than text | transports, scope, tool search, security |
| `llm-idea-generation.md` | when the agent generates rather than checks | starve the generator / saturate the evaluator; the model cannot rank its own output; personas help diversity and hurt correctness |
| `design-fixation-and-anchoring.md` | when the agent reads an existing system before proposing | that examples get copied, warnings fail, and framing content as "ideas" vs "requirements" moved originality 2.67 → 3.43 |
| `requirements-discovery.md` | when the agent reviews or hunts for what is missing | differentiated perspectives beat undirected review ~35%; **generic checklists buy nothing** |
| `ideation-and-idea-selection.md` | when the agent must choose among options | selection is the broken step, not generation |
| `architecture-evidence.md` | when the agent makes design decisions | the measured failure modes; what is measured about architecture and what is only repeated |

## The library

`/home/user/skills-repo/.claude/skills/` — 84 talents. Hand work over rather than
rebuilding it. The ones that bear on building agents:

| Talent | Owns |
|---|---|
| `writing-skills` (library, `/home/user/skills-repo/.claude/skills/writing-skills/`) | authoring a SKILL.md: structure, trigger-shaped description, RED-GREEN |
| `agent-harness-construction` | the tool/action surface itself — granularity, observation shape, recovery contract |
| `agent-surface-security-audit` | reviewing a configuration surface before adopting it |
| `agent-blast-radius-guard` | bounding what an autonomous run may destroy |
| `agent-fault-injection` | what an agent does when its *tools* fail |
| `eval-harness` | a repeatable baseline-vs-with harness |
| `skill-scout` | checking whether something already exists — run before authoring |

**Reuse-first is a gate, not a courtesy.** Before authoring anything, establish that
nothing already owns the job, and record where you looked. "I found nothing" is
only evidence if you can say where you searched.

## Two values that move on their own

Read these live; never copy the number into a skill:

- **Model limits** (context window, max output) — `platform.claude.com/docs/en/models/…`
- **Subagent limits** (the 15,000-token shared description budget, depth, concurrency)
  — `code.claude.com/docs/en/sub-agents`

A value that moves must be recorded as a pointer to its live source, never as a
number in a procedure.
