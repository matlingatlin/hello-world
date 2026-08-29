# The agent template

What an agent is made of, one file per part, with the requirement, how to write
it, and what a bad one looks like.

**Open this at the authoring step.** It costs nothing until then.

| File | Part | Read it when |
|---|---|---|
| `00-SKELETON.md` | the file itself | you start writing — copy it |
| `01-frontmatter.md` | all 15 fields | you fill the frontmatter |
| `02-description.md` | the description | last, after the agent is defined |
| `03-body.md` | the five body sections | you write the prose |
| `04-wall.md` | tools and hooks | you decide what must be impossible |
| `05-WORKED-EXAMPLE.md` | one complete agent, filled in | you want to see all of it at once |
| `LIMITS.md` | every enforced number | **generated** — never edit it |

---

## The order to work in

1. **Body §1 first** — name the artefact. An agent whose output you cannot name
   is not specified yet, and every later decision depends on it.
2. **The wall** (`04`) — decide what must be impossible, which fixes `tools:`.
3. **The rest of the frontmatter** (`01`) — including a line for every field you
   leave unset.
4. **The body** (`03`) — five sections, boundary second.
5. **The description** (`02`) — last, because you now know what it does.

---

## Mandatory, and not

**Mandatory:** `name`, `description`, `tools`, the five body sections, and a
stated stopping condition including how it fails.

**Mandatory but not in the file:** the spec that records the decisions, an eval
suite carrying a negative control and a containment case, and a test run by
somebody who did not write the agent.

**Optional:** `hooks` — only where a tool boundary cannot express the constraint.
`skills` — an agent with no preloaded procedure is legitimate if its judgement is
the whole job. The nine rarely-used frontmatter fields, each with a recorded
reason for being unset.

---

## How to read the provenance tags

| Tag | Means |
|---|---|
| **[DOC]** | in Anthropic's documentation. Binding. The validator enforces the mechanical ones |
| **[MEASURED]** | measured, with the study or the run cited. Follow it, and cite it if challenged |
| **[HOUSE]** | our convention. No measurement behind it. Follow it for consistency, but **never defend it as a fact** — and if it gets in the way of a good agent, it loses |

The distinction matters because the failure it prevents has already happened
here: a house rule was emitted by our own checker with the authority of a
specification, and a reader could not tell which it was.

---

## Where the numbers live

**Not in this template.** Character limits, word counts, the preload cap and the
roster budget are enforced by `.claude/validate/agents.py`, which is their single
home.

This template describes *how to write* each part. The checker decides *whether it
conforms*. A number repeated in both is a number that will disagree with itself
eventually — and the checker is the copy that gets run.

So `LIMITS.md` is **generated from the checker**, not written:

```
python3 .claude/validate/agents.py --limits > .claude/skills/agent-assembly/assets/template/LIMITS.md
```

and the checker refuses a template file that hand-copies one of its numbers.

Run it and paste the raw output:

```
python3 .claude/validate/agents.py
```
