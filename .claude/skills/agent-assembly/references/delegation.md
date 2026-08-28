# What to delegate, and what never to

A subagent inherits **none** of your context — not the conversation, not memory,
not previously invoked skills, not prior tool results. It gets its system prompt,
the task message, the `CLAUDE.md` hierarchy, a git status snapshot, its `skills:`
content, and the sibling roster.

That is the mechanism, not a limitation. **The handoff is forced to be a
document**, which is what makes independent review possible at all — this repo's
own factory found 81 defects because the author never wrote its own evals. It also
gives you, free, the one thing the ideation evidence demands: a generator and an
evaluator that *cannot* leak into each other.

## The patterns

| Pattern | Verdict |
|---|---|
| **Fan-out** — parallel, independent, different quarry each | **measured good.** The gap is between instances |
| **Producer → independent verifier**, different diet, external signal | **measured good** |
| **Pipeline** — A's artefact is B's input | fine when B genuinely needs it |
| **Round-table / debate** | **measured bad.** 12 interventions, 45 conditions, 0 of 62 significant |
| **Self-critique, no external signal** | **measured bad.** Every model, every benchmark, worse |

## Delegate

- **The baseline.** You cannot observe your own.
- **Independent authoring.** One subagent per skill when they do not share vocabulary.
- **Anything that runs.** Verification, tests, shell checks.
- **The test.** Always. Author ≠ tester is not a preference.

## Do not delegate

- The **spec**. Splitting the decision across agents that cannot see each other
  produces a roster that does not cohere.
- **Choosing** among options. The model ranks its own output at 22–40% agreement
  with experts where expert-expert is 60%, and forced pairwise comparison inflates
  win rates 27.2% → 49.1% purely by breaking ties. Selection is a human step.

## Ceilings

Depth **3**; at the limit the `Agent` tool is withheld from every subagent except
a fork. **Design for two levels** — coordinator → workers. 20 concurrent.
Background subagents silently receive a reduced built-in tool set. Workflow-spawned
agents always run in `acceptEdits` with file edits auto-approved regardless of
session mode — so walls must be hooks, never permissions.

## Writing a dispatch

Because the subagent starts blank, the prompt must carry: the artefact wanted,
the paths it needs, what "done" means, and **what not to assume**. A dispatch that
says "continue what we discussed" reaches an agent that was not there.
