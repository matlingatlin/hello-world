# Reviewing the agent-builder loop

Commissioned 2026-08-29. The loop is `agent-shape` → `agent-baseline` →
`agent-assembly` → `.claude/validate/agents.py` → an independent test, driven by
`.claude/agents/agent-builder.md`.

**I wrote all four artefacts**, so `design-claim-audit` step 0 fires on me and my own
verdicts would be worth little: a model critiquing its own output with no external
signal measures worse on every model and benchmark tested. Two fresh auditors ran the
procedure instead, on different perspectives, because that skill's own opening finding is
that one reviewer misses the worst thing — two independent reviews of this system
produced 35 findings and the most serious appeared in only one of them.

Neither auditor was told what I had already found. That omission is what makes their
passes a measurement rather than an echo.

What follows is **my own mechanical pass** — commands anyone can re-run — plus what I did
about each finding. The auditors' documents are `docs/audit-agent-builder-loop-p5.md`
(absence) and `docs/audit-agent-builder-loop-p4.md` (claim versus artefact).

## 1 · The finding that reframes the rest

```
$ env | grep SUBAGENT_SPAWN_DEPTH
CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1
```

The documentation for that variable says: *"Set `1` to turn nesting off."*

**So every agent in this environment is a leaf.** No subagent can dispatch another. And
the loop's design rests on dispatching in two places:

| Where | What it says | Can it run here |
|---|---|---|
| `agent-baseline` description | *"dispatches independent subagents to attempt the target job with no support at all"* | **no** |
| `agent-assembly` step 6 | *"Dispatch an agent that has not seen the authoring"* | **no** |
| `agent-builder.md:27` | *"delegation **is** execution, one hop away"* | **false here** |

Four agents have now reported it independently, unprompted, each in its own words —
`agent-builder` twice, the general-purpose tester once, `domain-researcher` once. I read
the first two as a session quirk. They were reporting an environment invariant.

**`agent-assembly` has an honest fallback for it** (*"You cannot delegate the test. Then
the work is not finished. Stage the agent and a tester brief, say plainly that step 6 is
unmet, and stop"*) and that fallback has fired in four consecutive builds, correctly.
**`agent-baseline` has none** — `grep -niE 'cannot dispatch|no Agent|if you cannot'`
returns 0 — which is why both real builds substituted recorded runs for dispatched ones
without the procedure telling them they were allowed to.

`agent-builder.md:27` is the one that has to change regardless. It was written to correct
an *over*-claim of safety — an earlier version said "you have no shell" and a tester
quoted `a boundary is only as narrow as the widest tool` back at it. The correction
overshot into a capability claim that is false in the only environment this agent has
ever run in.

## 2 · Trigger collision, measured

Jaccard overlap on description terms, stopwords removed, across all 7 agents:

| Pair | Overlap | Shared terms |
|---|---|---|
| **`architect` × `architect-rebuild`** | **0.195** | boundary, carving, choosing, datastore, decision, design, layer, parts, seams |
| `domain-researcher` × `primary-source-verifier` | 0.150 | claim, cites, draft, evidence, note, source |
| `rebuild-adjudicator` × `rebuild-prospector` | 0.143 | candidate, candidates, rebuild, system |

The second and third pairs are **deliberate and correct** — those are the two halves of a
separation, and their NOT-clauses route to each other explicitly.

The first is not. Two architect agents compete on the same triggers with no NOT-clause
between them, which is the collision standing open as eval case T5 and never checked.
Recorded; not fixed here, because which one survives is a decision, not a repair.

## 3 · What the absence audit found, and what I did

17 rows: **15 refuted, 1 holds, 1 not checkable**. I re-derived every finding below
before acting on it, because an auditor's word is not evidence either.

| # | Finding | Re-check | Done |
|---|---|---|---|
| A-13 | `settings.json:31` carried `"matcher": "Edit|Write"` — **the exact string `selftest.sh` plants as a defect** — and `agents.py` never scanned settings.json | confirmed, both halves | **fixed**: matcher anchored; the validator now parses `settings.json` and `settings.local.json`, checking matchers, hook existence and executability. Four new controls |
| A-02 | the `assembly → validate` arrow has **no call site** — `grep -rn 'validate/agents.py'` across all four loop artefacts returned **0** | confirmed | **fixed**: step 5 now runs the command and takes its raw output as the artefact, instead of restating five checks the validator already implements |
| A-03 | nothing enforces *"every agent ships with evals"* — it is a sentence in `CLAUDE.md`, against that same file's rule that a must-never is a hook or an absent tool | confirmed | **fixed**: the validator now fails an agent with no eval artefact. It immediately named `rebuild-prospector` and `rebuild-adjudicator`, which is A-01 reproduced mechanically |
| A-14 | **the pipeline's final stage has no part** — `ls .claude/agents/ \| grep -icE 'test\|eval\|grader'` → **0**. Step 6 dispatches to a *property*, not to a file | confirmed | **not fixed** — see §5 |
| A-04 | `agent-builder`'s own wall never had the hook proposal the loop mandates. 7 hooks, 4 proposals, and `git log --all` shows it never existed | confirmed | open |
| A-17 | 3 specs for 7 agents; **`agent-builder` has none** — the agent enforcing "no assembly without a spec" was assembled without one | confirmed | open |
| A-05 | 4 of 7 hooks have no re-runnable harness | confirmed | open |
| A-12 | **12 of 26 knowledge notes are cited zero times** by the loop, including `testing-skills-methodology.md` and `skill-authoring-eval-methodology.md`. Variance is required at the baseline and absent at the eval | confirmed | open |
| A-10 | proctoring, ongoing evaluation, registry, withdrawal → **0** occurrences in `.claude/` | `holds` | B131–B133, already open |

**One caution on my own fix.** The first version of the eval check credited two agents
with a spec because a *different* agent's spec named them once, in a NOT-clause — *"a
count of mentions is not a count of things"*, the exact failure the audit procedure warns
about, committed inside the checker written to enforce it. An artefact now covers an agent
only when its filename says so or it returns to the agent three or more times.

Controls: **23 positive controls pass**, including one asserting a single passing mention
does *not* count as coverage.

## 3b · What the claim audit found

**26 holds, 8 refuted, 5 not checkable.** A review that only accuses is not
calibrated, and 26 of 34 checkable assertions held under a disconfirming read.

Two findings land in the fix I made an hour earlier, in this same review:

| # | Finding | Re-check | Done |
|---|---|---|---|
| F-P4-06 | **`agent-shape` §0b consumes step 1's candidate sentence and runs before step 1** | confirmed: 0b at line 23, step 1 at line 53 | **fixed** — moved after step 1, renumbered **1b** |
| F-P4-07 | `knowledge-map.md` claimed *every* note carries per-claim MEASURED/REPEATED. **Five of the twelve it routes to carry neither** | confirmed by count: `claude-md-and-memory`, `dynamic-workflows`, `hooks`, `mcp`, `skill-anatomy` → 0 | **fixed** — and it was load-bearing, because §1b would have graded its own core references `thin` on their own evidence |

And three that are older:

| # | Finding | Done |
|---|---|---|
| F-P4-02 | `agent-baseline` carried *"software engineering was its weakest domain at +4.5%"* — **v1 of the paper, overtaken by three revisions.** v4 Table 3 reads SE at +11.6 pp, weakest Mathematics & OR at +9.7 pp | **removed, not replaced.** Stale rather than invented — v1 does say +4.5 — but the correction rests on one agent's single fetch and has not been through `primary-source-verifier`. Putting an unverified number where an unverified number was is not a fix |
| F-P4-03 | **the gate is create-only and content-blind**, so a *new* agent with `tools:` omitted passes. The auditor executed that write and got ALLOW | **documented in the body**, not patched. Content inspection was tried here and inverted safety once already. The defence is downstream and mechanical, and step 5 now runs it |
| F-P4-04 | **no artefact recorded that this loop's own ablation returned null** | **fixed** — `agent-builder` now tells itself, with the confounds |

**Where the disconfirming check killed a finding, which is the step working.** The
auditor drafted *"+19.0pp / +10.1pp is fabricated"* after v1's Table 5 gave +18.6 / +5.9,
then fetched v4 Table 8 and got exactly `2–3: +19.0 · ≥4: +10.1`. Recorded as `holds`.
Same for the 6.6× over-length claim: 84 SKILL.md counted, 68 over 500 words,
`writing-skills` at 3,306 words = 6.61×. Exact.

**Both auditors reached the same seam independently.** P5's A-02 and P4's F-P4-01 are the
same finding — the validator is declared the single home of the construction rules, and
the loop restated them and pointed at it nowhere. Two perspectives, no contact, one
convergence. That is the strongest evidence in this document, and it is about the loop's
worst structural habit: `19.0pp` still appears in **7 places**, and three of the four
artefacts still do not name the validator.

## 4 · What the loop got right, stated because a review that only accuses is not calibrated

- **The build order held under pressure.** Both real builds hit the missing `Agent` tool,
  and neither faked a baseline or a test: each staged a brief and said step 6 was unmet.
- **The separation works.** Every defect in this document was found by something that did
  not write the thing it was auditing — including three defects in code I had written the
  same day, and including a defect inside a checker written to catch that class.
- **The walls are real and they are tested.** 46 + 23 control rows, mutation-tested in
  both directions.
- **Delegating the shape decision produced a better tool surface than I did.** The blind
  rebuild of the architect chose 4 tools where I had chosen 9, with a better argument.

## 5 · The one that is not a repair

**A-14 — the loop's final stage has no part, and cannot be built by the loop.**

`agent-assembly` ends by dispatching the test to a fresh subagent. There is no tester
agent; step 6 names a *property* instead. Building one would be `agent-builder`'s job —
and `agent-builder` cannot test what it builds, because nesting is off. **The loop cannot
close its own last stage.** Every test in this session was dispatched by the top-level
session, by hand.

That is a design conclusion, not a defect to patch quietly. The honest options are three:

1. **Name the orchestrator.** The loop's contract becomes: `agent-builder` emits the
   spec, the files and the tester *brief*; the session above it runs the brief. That is
   already what happens; the documents just do not say so, and `agent-baseline` implies
   the opposite.
2. **Raise the depth.** `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=3` restores the design as
   written — untested here, and it changes the blast radius of every agent that holds
   `Agent`.
3. **Build the tester agent anyway**, dispatched by the orchestrator rather than by
   `agent-builder`. It is the missing part either way; option 1 says who calls it.

They are not exclusive, and 1 is owed regardless: a procedure whose mandatory step cannot
execute must say so in the step, not in a fallback further down. → **B138.**

**Option 1 is now partly done.** `agent-baseline` gained **§2b**, the fallback it never
had: ask the session above to dispatch and hand up the verbatim prompt; or use recorded
real runs, which are *stronger* on one axis because nobody constructed them to be a
baseline; or have no baseline and say the content is opinion. And
`agent-builder.md` no longer asserts that delegation is available — it says `Agent` can be
listed and still withheld, names the setting, and tells the agent to look before planning
around it.

What is still owed: the tester agent itself, and a spec for `agent-builder`.

## Coverage

Perspectives run: **P5 · Absence** and **P4 · Claim versus artefact**, one fresh auditor
each, neither having seen the other's work or mine. Not run: **P1 tenancy**, **P2 failure
handling**, **P3 lifecycle**. This is two perspectives and it is not coverage.

Behaviour was not audited at all — 17 of the P5 rows are about mechanisms in the tree.
The only behavioural evidence for the loop is the two builds it has actually produced.
