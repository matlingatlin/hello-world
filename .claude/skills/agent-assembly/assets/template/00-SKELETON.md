---
name: <verb-or-job, hyphenated, lower case>
description: <see 02-description.md — this is the field that decides whether the agent is ever used>
model: <see 01-frontmatter.md>
tools: <EXPLICIT LIST, ALWAYS — omitting inherits every tool available to subagents>
skills:
  - <at most three; each a numbered procedure ending in an artefact>
hooks:
  PreToolUse:
    - matcher: "^(Write|Edit|NotebookEdit)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.sh"
---

# <Name in prose>

<ONE paragraph. What this agent is for, and the single artefact it produces.
Not the steps — those are in its skills, which load in full alongside this file.
No persona, no "you are an expert": measured negative for correctness work.>

## What you produce

<The artefact, by path and shape. `docs/decisions/NNNN-*.md`. A findings table
with one row per unit. A verdict document with per-claim rulings.

An agent whose output you cannot name is not specified yet — go back to shaping.>

## What you may not do, and by what mechanism

<One row per impossibility. Every row names the MECHANISM, never the intention.

  - You hold no `Bash`. Nothing here executes.
  - `.claude/hooks/<name>.sh` denies every write outside `docs/`.

A row whose mechanism is "the prompt says not to" is not a row — it is a wish.
Delete it or convert it to an absent tool or a hook.

Then, separately and honestly: what the mechanisms do NOT cover. Name the gap
rather than letting the list imply completeness.>

## Your functions

<The map only — one line per preloaded skill, each naming what it decides and
what it emits. The procedures live in the skills.

| Skill | Decides | Emits |

At most three. A fourth function is the signal you have two agents.>

## Where your knowledge lives

<Pointers, never copies. `/home/user/skills-repo/knowledge/notes/<note>.md`,
and what each settles. A value that moves on its own is read live, never
transcribed — copies drift, the base does not.>

## When you are done, and when you stop short

<The stopping condition, positively stated: what must exist for the job to be
finished.

And the refusals: the conditions under which the right answer is to produce
nothing and say why. An agent with no stated way to fail will always find a way
to succeed.>
