---
name: agent-assembly
description: "Use when a spec and an observed failure list both exist and the agent must now be written — places every piece in the tier that loads it at the right moment, authors the files, and then hands the finished agent to a FRESH subagent for testing because the author never grades its own work. Reach for this whenever someone says to build, assemble, wire up or finish an agent. It creates new agents only — a change to one that already exists is written as a proposal under docs/ and applied by a human. NOT for deciding what agents should exist (use agent-shape), NOT for observing unaided failure (use agent-baseline), NOT for authoring a standalone skill unattached to an agent (use the library talent writing-skills at /home/user/skills-repo/.claude/skills/writing-skills/)."
---

# Building it, in the right tier

Everything here is placed by **when it is needed**, never by what it is. Read
`references/tiers.md` for the placement test and `references/delegation.md` for
what to hand out and what to keep.

You have no shell. Everything that *runs* — verification, tests — is delegated.
That is not a limitation; it is what keeps the write boundary real.

## 0 · Open the template, and check the bill of materials is closed

**The template is the standard you build to.**
`assets/template/INDEX.md` — one file per part of an agent, each with the
requirement, how to write it, a worked example and a non-example. You do not
invent the shape; you fill it. Read `00-SKELETON.md` before the first line.

**And check the plan is finishable.** `agent-shape` step 7b emits a bill of
materials. **If any row still reads `commission`, stop here.** A gap found now is
a task for the part that can close it — a note goes to `domain-researcher`, a
procedure to the skill-maker, a wall to a proposal. The same gap discovered
mid-assembly is an improvisation, and improvisations are what the review lenses
find later as unsourced claims and promised files that do not exist.

**Artefact:** the bill of materials with no open row, or the list of what you are
waiting on and who has it.

## 0b · Run the checker after each part, not once at the end

**[MEASURED here]** Every strengthening of every gate in this repository was found
by *running* something, never by reading it. The same holds one level up:
conformance found at the end is conformance found after the mistake has been
repeated across the whole file.

So after each part lands — the frontmatter, the body, each skill — run:

```
python3 .claude/validate/agents.py
```

It is cheap, it is deterministic, and a defect it names is yours. In-process
control exists in manufacturing for the same reason: finding a bad batch at
release wastes the batch.

If you hold no shell, hand the command up **at each part** rather than banking
them for the end. A caller running it five times cheaply beats one run that
returns a list.

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

## 4 · Emit the wall as a proposal, and know what you may not touch

You may not write `.claude/hooks/`, and you may not write **any file under
`.claude/` that already exists**. You create; you do not edit. A change to an
existing agent — including a repair you are certain of — is a proposal under
`docs/` that a human applies.

That rule is not caution, it is the one that works. An independent tester found
three ways past a gate that inspected *content*: delete a `hooks:` block, widen a
`tools:` line, or rename a key across two innocent-looking edits. Every one needed
a file that already existed. Creating only removes the class. Write the hook under `docs/` using `assets/hook-proposal.md`,
with its controls: cases that must pass, cases that must be denied, traversal, a
prefix-lookalike, an empty path, malformed input. A human installs it.

**Artefact:** the proposal, with its control table.

## 5 · Verify mechanically — by delegation

You hold no shell, so verification is delegated. Be precise about what that does
and does not buy, because an earlier version of this file was not: **a delegate
runs under its own permissions, so delegation is execution one hop away.** What
the absent shell actually buys is that nothing *this* context writes reaches the
filesystem except through the gate. It is not a claim that no command runs.

**The first five checks below are already implemented.** `.claude/validate/agents.py`
does them, it is the single home of the construction rules per the change matrix in
`docs/decomposition-agent-pipeline.md` §1, and until a P5 absence audit found it, no
step in this loop named it — the checks were restated here in prose while the program
that runs them sat unreferenced. Restating a rule is a second place for it to rot.

So the delegation is one command, and its raw output is the artefact:

```
python3 .claude/validate/agents.py
```

Exit 0 is clean; exit 1 lists failures with a provenance tag ([A] Anthropic's spec,
[B]/[C] the docs, [M] a measured house rule — the key prints under any run with
findings). **A defect it names is yours, not its.** Its own positive controls are
`.claude/validate/selftest.sh`; if you doubt a result, run those first — a checker
that cannot fail proves nothing.

What it covers, so you do not re-check it by hand:

- frontmatter parses **line-anchored** — line 1 exactly `---`, a later line exactly
  `---`. Splitting on `---` reports green on an unterminated file; three talents
  once shipped unloadable.
- no dead cross-references, no invented commands
- the tool surface is `tools:`-explicit, descriptions are within limits and carry no
  angle brackets, names are kebab-case and unreserved, preloads exist and are within
  the house cap, hook commands exist and are executable, matchers are anchored — in
  `.claude/settings.json` as well as in agent frontmatter
- every referenced file exists at the path the skill names

Two things it does **not** cover, and they are still a delegation:
- **every artefact the build CLAIMS to have produced actually exists.** Run it as
  a listing, not a reading of the report. This is not hypothetical: in this repo's
  own ablation, the arm that had these procedures asserted *"the bar is in
  EVALS-migration-reviewer.md, written by a subagent that did not author any of
  this"* — and `git ls-tree` showed no such file. A claimed artefact is the
  cheapest lie to tell and the cheapest to catch

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

### 6b · Calibrate the judge before its verdict counts

A tester that reports "no findings" has told you one of two things and you cannot
tell which: the agent is clean, or the tester is blind.

`.claude/validate/calibration/` settles it. Five specimens, each a plausible,
otherwise-clean agent carrying exactly one planted defect — a fabricated figure,
a superseded citation, a body that contradicts its own `tools:` line, a dead
route, a promised file that does not exist. **Verified inert against the checker:
five specimens through 22 mechanical checks, CLEAN.** Every defect in the set is
invisible to `agents.py`, which is precisely why a reading judge is the only thing
that can catch it.

**Hand the judge the specimen for its class, and nothing else.** Not the manifest
— that holds the answers — and **do not say a defect was planted**. A reviewer
told to find something will find something, and that measures compliance, not
detection.

A judge that misses its own class is not reporting on the agent you pointed it
at. Re-brief it or use a different one; do not record its verdict.

**Artefact:** which specimen the judge was given, and whether it found the planted
defect — before any verdict on the real agent is written down.

## 7 · Report what is true

Never a green number alone. Say which failure classes the suite is blind to, how
many cases were verified against the artefact versus taken on the tester's word,
and what you did not check.

An agent below its bar is **cut, not defended**. Three of four comparable skills
measured elsewhere here did not discriminate; one made the answer worse.

## When this does not apply

- **No baseline was run.** Assembly builds from observed failures. Without them
  you are writing your opinion into a procedure, where it will read as evidence.
- **The change is to an agent that already exists.** You create. Write the change
  as a proposal under `docs/` and let a human apply it.
- **What is wanted is a standalone skill with no agent around it.** That is the
  library talent `writing-skills` at
  `/home/user/skills-repo/.claude/skills/writing-skills/`.
- **The spec calls for a fourth preloaded procedure.** That is the signal you have
  two agents, not a bigger one. Go back to `agent-shape`.
- **You cannot delegate the test.** Then the work is not finished. Stage the agent
  and a tester brief, say plainly that step 6 is unmet, and stop — an untested
  agent shipped as done is the failure this whole procedure exists to prevent.

