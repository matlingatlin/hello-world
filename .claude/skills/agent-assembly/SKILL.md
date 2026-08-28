---
name: agent-assembly
description: "Use when a spec and an observed failure list both exist and the agent must now be written — places every piece in the tier that loads it at the right moment, authors the files, and then hands the finished agent to a FRESH subagent for testing because the author never grades its own work. Reach for this whenever someone says to build, assemble, wire up, or finish an agent, and also when an existing agent must be repaired, since a repair is an assembly against a new failure list. NOT for deciding what agents should exist (use agent-shape), NOT for observing unaided failure (use agent-baseline), NOT for authoring a standalone skill unattached to an agent (use writing-skills)."
---

# Building it, in the right tier

Everything here is placed by **when it is needed**, never by what it is. Read
`references/tiers.md` for the placement test and `references/delegation.md` for
what to hand out and what to keep.

You have no shell. Everything that *runs* — verification, tests — is delegated.
That is not a limitation; it is what keeps the write boundary real.

## 1 · Place every item from the spec

Each piece of content goes to exactly one tier. When in doubt, ask: **does this
need to be in context on every turn?** If no, it moves down.

| Tier | Loads | Put here |
|---|---|---|
| 0 · agent body | every invocation | identity, the boundary, the map of its functions |
| 1 · `skills:` | full, at start | the procedures — **at most three** |
| 2 · repo rules | `CLAUDE.md` only | rules binding every agent here |
| 3 · `references/` | when a step opens it | knowledge, failure-mode tables, pointers to the base |
| 4 · `assets/` | at the emit step | templates |
| 5 · hook | never read; executed | what must be impossible |

**`.claude/rules/` does not reach a subagent** — measured, canary probe, both
scoped and unscoped. Do not put an agent's rules there.

**Artefact:** the placement table, every spec item assigned.

## 2 · Write the agent body — identity and boundary, never procedure

It becomes the system prompt and shapes every turn, so length costs judgement.
There is no documented size cap; the discipline is relevance, not a word count.

It carries: what this agent is, what it may never do and *by what mechanism*,
which functions it has, and where its knowledge lives. Not the steps — those are
tier 1.

**No persona.** Measured: 162 personas across 2,410 questions showed a largely
random effect; a second study measured MMLU 71.6% → 66.3%. What a persona seems
to promise — accumulated judgement — is *content*, and it belongs in the failure
tables. The exception is narrow: for agents whose job is **diversity** rather than
correctness, ordinary personas measured 2.6× more between-agent variation, and
ordinary beats visionary. Read `llm-idea-generation.md` before using one.

Use `assets/agent.md`.

**Artefact:** the agent file, and the description checked against the shared
15,000-token budget for all agent descriptions in the repo.

## 3 · Author the procedures — delegate where they are independent

Each skill addresses `teach` rows from the baseline. **A rule with no row behind
it does not go in.**

Independent skills are authored by parallel subagents with fresh context; that is
fan-out, the pattern with evidence behind it. Skills that must agree on shared
vocabulary are authored together. Never have the authors converse.

Use `assets/skill.md`. Every step names the file it opens.

**Artefact:** the SKILL.md files, plus which were delegated and to whom.

## 4 · Emit the wall and every privilege line as a proposal

You may not write `.claude/hooks/`, nor any **privilege line** into a `.claude/`
file — `tools:`, `hooks:`, `model:`, `permissionMode:`, `allowed-tools:`. Those
decide what an agent may do and which wall is attached, and an agent that can
write them can attach or remove a wall — its own or a neighbour's. The rest of
every file is yours to write and revise, which is what repairing an existing agent
actually needs. Write the hook under `docs/` using `assets/hook-proposal.md`,
with its controls: cases that must pass, cases that must be denied, traversal, a
prefix-lookalike, an empty path, malformed input. A human installs it.

**Artefact:** the proposal, with its control table.

## 5 · Verify mechanically — by delegation

Dispatch a subagent with a shell to check, and require it to report the command it
ran and the output:

- frontmatter parses **line-anchored** — line 1 exactly `---`, a later line exactly
  `---`. Splitting on `---` reports green on an unterminated file; three talents
  once shipped unloadable.
- no dead cross-references, no invented commands
- the tool surface is what the spec said, and `tools:` is not omitted
- every referenced file exists at the path the skill names

**Artefact:** the check output, not the checker's summary of it.

## 6 · Hand the test to a fresh subagent

The author never grades its own work. Dispatch an agent that has **not** seen the
authoring, give it the agent and the spec, and have it write and run the evals.

Its suite must contain, and say so:
- **normal cases** — the everyday job
- **a negative control** — where the right answer is to produce nothing. Without
  it a suite cannot tell a real finding from noise.
- **containment cases** — *can this agent exceed its remit?* A skill has no remit
  to exceed; an agent does. Nothing in skill-authoring practice covers this.
- **a trigger check** — does the description route work here that belongs elsewhere?

**Artefact:** `evals.md` with per-case verdicts, written by someone else.

## 7 · Report what is true

Never a green number alone. Say which failure classes the suite is blind to, how
many cases were verified against the artefact versus taken on the tester's word,
and what you did not check.

An agent below its bar is **cut, not defended**. Three of four comparable skills
measured elsewhere here did not discriminate; one made the answer worse.
