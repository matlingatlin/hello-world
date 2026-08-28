---
name: agent-shape
description: "Use BEFORE writing any agent file, whenever someone wants a new subagent, a specialist, a reviewer, a builder, or says an existing agent should be split or is doing too much. Decides what agents should exist at all — how many, what each may see, what each may do, and where the wall goes — and emits a spec another skill builds from. Reach for this even when the request sounds like a single obvious agent, because the most expensive agent mistakes are made before a line is written. NOT for authoring the files (use agent-assembly), NOT for observing what goes wrong without support (use agent-baseline), NOT for writing a standalone skill with no agent around it (use writing-skills)."
---

# Deciding what agents should exist

The costly mistakes here are made before anything is written: one agent that
should have been two, a tool surface granted by omission, a boundary stated as a
sentence. This procedure ends in a **spec**, not an opinion.

Open `references/knowledge-map.md` now. It says which note answers which question
and where the library already owns a job. You query that base; you do not carry it.

## 0 · Establish nothing already owns this

Search the existing agents and the library for the job, by its *symptoms* as well
as its name. Then say plainly: reuse, extend, or author — and **where you looked**.
"Nothing exists" is evidence only if you can name the search.

**Artefact:** the search, and the verdict.

## 1 · State the job as one sentence and one artefact

*"It reviews a migration and produces a findings list at `file:line` with a
verdict."* If you cannot name the artefact it produces, the job is not defined
yet, and every later step will be guesswork.

**Artefact:** the sentence, and the thing it emits.

## 2 · Decide the context diet — this is the step people skip

What must this agent **see**, and what must it **not** see?

The distinction is not fussiness. Measured: an agent asked to *propose* something
produces narrow, source-bound restatements when the existing solution is in its
prompt — seeding measurably reduced diversity below giving nothing at all. The
same context is *required* for an agent that **judges**: novelty scored 6.14/10
without retrieval and 2.38/10 with it, a 2.6× inflation.

**Generators are starved. Evaluators are saturated.** Read
`llm-idea-generation.md` before deciding this for any agent that proposes.

**Artefact:** two lists — must-see, must-not-see.

## 3 · Split test — one agent, or several?

In this order. The first that fires decides.

1. **Opposite diets → always separate agents.** They share a context window; you
   cannot starve and saturate the same one.
2. **Independent quarry → separate agents.** The measured gain is *between*
   instances, not within one. Differentiated procedures beat undirected work by
   ~20–35%; **undifferentiated buckets measured no better than nothing.**
3. **More than three functions → split.** The three-skill cap is a measured
   quality finding (1–3 modules ≈ +19.0pp, 4+ ≈ +10.1pp), not a budget. A fourth
   function is the signal that you have two agents.
4. **Author and tester are never the same agent.** In this repo's own factory,
   independent testers found 81 defects precisely because the author never wrote
   its own evals.

Sequentially dependent with the *same* diet → one agent, several skills.

**Artefact:** the roster, and which rule decided each split.

## 4 · Name the functions — at most three, each ending in an artefact

A function is a procedure, not a topic. It must end in something checkable: a
number, a `file:line`, a table row, a named module, a verdict.

A step that ends in a consideration does not land. Measured: raising a missing
consideration recovers a fraction of the gap it should, and asking someone to
think harder recovers almost none.

**Artefact:** function → procedure → what it emits.

## 5 · Design the tool surface

**The most dangerous line in an agent file is the one you do not write:
`tools:` omitted inherits ALL tools, not none.**

Grant deliberately. For each tool, say what job needs it. Then ask the harder
question: does this tool make some *other* boundary decorative? An agent with a
path-scoped write gate and `Bash` has no write gate.

If the agent should not execute, it delegates execution. That is not a limitation
— it is how the wall stays real. Read `agent-harness-construction` in the library
for granularity and the recovery contract each tool should carry.

**Artefact:** the tool list, each with its justification, plus one line naming
what the surface makes impossible.

## 6 · Put the wall where prose cannot reach

A "must never" in an agent's prompt is a request. This is the most thoroughly
measured non-intervention available: warnings against a bias failed in three
studies and **backfired in a fourth**; eight anchoring-warning variants, differing
in content and timing, were **all** indistinguishable from no warning.

A `PreToolUse` hook runs before every permission check — `bypassPermissions`
included — and can only tighten. That is a wall.

Two rules that fall out of it:
- **An agent that may write hooks or settings can remove its own wall.** Deny both.
- Emit the hook as a **proposal for a human to install**, not as something the
  builder writes itself.

**Artefact:** what must be impossible, and the mechanism for each. If the
mechanism is "the prompt says not to", it is not impossible.

## 7 · Decide the composition

| Pattern | Verdict |
|---|---|
| Fan-out — parallel, independent, different quarry | **measured good** |
| Producer → independent verifier, different diet, external signal | **measured good** |
| Pipeline — A's artefact is B's input | fine when B needs it; the handoff is a document |
| Round-table, agents conversing | **measured bad** — 12 interventions, 45 conditions, 0 of 62 significant |
| Self-critique with no external signal | **measured bad** — every model, every benchmark, worse |

Ceilings: depth 3, and the `Agent` tool is withheld at the limit from everything
but a fork. Design for two levels — coordinator → workers.

**Artefact:** what is delegated, to how many, and what never converses.

## 8 · Emit the spec

Under `docs/`, carrying every artefact above. Then hand to `agent-baseline` —
**not** to assembly. You do not yet know what the agent needs to fix.

## When this does not apply

- The job is one procedure with no second party and nothing to isolate. That is a
  skill, not an agent.
- An agent already owns it. Say so and stop.
