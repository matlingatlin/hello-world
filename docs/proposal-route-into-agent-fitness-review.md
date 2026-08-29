# Proposal — give the new reviewer a route in

**A human applies this.** `agent-builder` creates agents; it does not edit existing
files, and every file below already exists. The change is three lines.

## Why

A deliberate split has a NOT-clause in **both** directions; a collision has none. The
measured live defect in this repo is `architect` × `architect-rebuild` at Jaccard
**0.195** on description terms with no NOT-clause either way
(`docs/review-agent-builder-loop.md:56-71`). The recorded general defect is worse: an
entire pipeline stage was built, walled and tested with **nothing routing into it** —
`grep -icE 'research|domain-researcher|sweep|commission'` returned 0 across all four
artefacts of the loop that owned it (`docs/BACKLOG.md:476-482`, B137).

`.claude/agents/agent-fitness-review.md` names its neighbours. None of them names it.
Estimated term overlap with `agent-builder` is ≈0.05 and with `architect` ≈0.06, so this
is not a collision — it is the reverse problem, a part reachable only if a router happens
to read the newest description. Until the three edits below land, the new agent is the
next B137.

## The three edits

**1 · `.claude/agents/agent-builder.md`, the `description:` line.** It currently ends
*"…it does not write source code, install hooks, or grade its own work."* Append:

> Grading a built agent, or judging whether an existing one is still fit to run, goes to
> `agent-fitness-review`.

This is also the missing half of a second finding: `agent-builder`'s description still
contains no reference to `domain-researcher` either (`docs/domain-research-test-results.md:141-160`,
D2). If both are added in one edit, re-run the roster budget check — the 15,000-token
shared description budget is at ~8%, so there is room, but it is a shared budget.

**2 · `.claude/skills/agent-assembly/SKILL.md` step 6.** It currently reads *"Dispatch an
agent that has **not** seen the authoring"* — a property, not a target, which is audit
row A-14 and backlog **B138**. It should name the file, and it should say who dispatches
it, because `agent-builder` cannot: at `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` every
agent is a leaf. Suggested:

> Dispatch `agent-fitness-review`, one lens per dispatch, plus a fresh tester for the
> behavioural suite. **The session above `agent-builder` makes these dispatches**;
> `agent-builder` is a leaf here and emits the brief instead. If you are that leaf, stage
> the brief, say step 6 is unmet, and stop.

**3 · `docs/BACKLOG.md`, B138.** Its structural half reads *"there is no tester agent …
building one is `agent-builder`'s job, which cannot test what it builds."* Half of that is
now closed and the other half is not. Suggested status line:

> **PARTLY ADDRESSED 2026-08-29, PENDING TEST.** `agent-fitness-review` exists with two
> skills, five lenses and a spec — the *static* half of the missing stage, contained by
> absent tools rather than by a proposed wall. The *behavioural* half is unchanged: it
> holds no `Agent`, so it cannot dispatch the agent it reviews, and B138's option 1
> (name the orchestrator) is still owed at edit 2 above. Its own step 6 is unmet —
> `docs/agent-fitness-review-tester-brief.md`.

## What this proposal does not claim

That the new agent works. It has not been tested; see the brief. Routing work to an
untested reviewer is worse than not routing it, so **apply edit 3 first, edits 1 and 2
after the suite has been run and the agent has cleared its bar.** If it does not clear
the bar, the rule this repo binds itself to is *cut, not defended*, and these edits are
withdrawn rather than softened.
