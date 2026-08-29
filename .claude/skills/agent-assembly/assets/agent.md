---
name: <the job, hyphenated — not a clever label>
description: "<Trigger-shaped and third person. What situation hands work to this
  agent, in the words someone would actually type. Include NOT-clauses routing to
  neighbours. This drives DELEGATION — whether a whole job goes to a separate
  worker — not whether text is loaded. Counts against the 15,000-token budget
  shared by every agent description in the repo.>"
model: <inherit | a pinned id when the job needs a specific model. Say which and why.>
tools: <EXPLICIT LIST. Omitting this inherits ALL tools. If the agent should not
  execute, leave Bash out and let it delegate — that is what keeps a write gate real.>
skills:
  - <at most three. Each a procedure ending in an artefact.>
hooks:
  PreToolUse:
    - matcher: "<Write|Edit|NotebookEdit, Bash, …>"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/<installed-by-a-human>.sh"
---

# <Agent name>

<One paragraph: what this agent is for and what it produces. Not the steps —
those live in its skills.>

## What it may not do, and by what mechanism

<Each impossibility with the mechanism that enforces it. "The prompt says not to"
is not a mechanism. If it must not happen, name the hook or the absent tool.>

## Its functions

<One line per skill: what it decides and what it emits. This is the map — the
agent reads the procedure itself from tier 1, not from here.>

## Where its knowledge lives

<Paths. The agent queries the base rather than carrying copies, because copies
drift and the base does not.>

## Scope

<What is settled and not this agent's to reopen, and what it may argue with —
and in what form an argument has to arrive.>

<!-- TEMPLATE. Fields are empty on purpose: a filled-in exemplar is a near-domain
     stimulus and gets reproduced, choices included. Delete this comment and
     everything in angle brackets.
     NOTE on `tools:`, `hooks:`, `model:`, `permissionMode:` — these decide what
     the agent may do. An earlier gate refused to write them; it was removed
     because content inspection proved evadable (five YAML spellings, a two-step
     rename, a symlink) and because it inverted the safety property, denying a
     compliant file while allowing one that omitted `tools:` and inherited every
     tool. The gate now enforces CREATE-ONLY instead, which closes the same holes
     structurally. So you CAN write these lines on a new agent — and nothing
     mechanical will stop you getting them wrong. `tools:` omitted inherits ALL.
     A reviewer, not a gate, is what checks them. -->
