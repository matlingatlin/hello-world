# The lenses — declare exactly one per pass

Opened by step 1 of `agent-review-pass`.

These are **not** buckets to sort findings into. A set of categories swept in one pass
is the checklist condition, measured no better than reviewing with no procedure at all.
What beat ad hoc review by ~35% was different readers running **different procedures
hunting different fault classes**, one each, in separate passes.

Each lens below carries the recorded run that motivated it. If a lens has no such row,
it is not here — the five are a clustering of twelve observed failures, not a taxonomy
someone thought of.

---

## L1 · Grounding

**Hunts:** a rule, number or claim inside the agent that nothing observed put there.

**Procedure.** Enumerate every *directive* in the agent body and its preloaded skills —
every "always", "never", threshold, effect size and named failure mode. For each, find
what put it there: a row in the agent's spec or baseline table, a knowledge note, a
recorded run, or nothing. Then check the direction of the citation: does the cited
document actually contain the row, or does it contain a *restatement* of the same claim?
A number that appears in several places with no single home is a copy, and copies rot
independently.

**Forces:** one row per directive — `directive · file:line · what put it there · one of
grounded / restated / speculation / unevidenced`.

**Why this one exists:** on this repo's own loop, one construction rule was restated in
seven places while the program that implements it was named in one; the loop's four
artefacts named it zero times. Two audits reached that seam independently, from opposite
perspectives (`docs/audit-agent-builder-loop-p5.md:149-202`;
`docs/audit-agent-builder-loop-p4.md:67-105`). And a procedure's own rule is that a rule
with no observed row behind it is an opinion wearing a table's clothes.

---

## L2 · Currency

**Hunts:** something that was true when it was written.

**Procedure.** Three sweeps, in this order.

1. **Values that move.** Model limits, subagent limits, published effect sizes, prices,
   version-pinned figures. For each, find whether the agent carries the *number* or a
   *pointer to its live source*. Where it carries a number, fetch the source the
   artefact names and compare version for version. Do not substitute a different source.
2. **The evidence status of what it cites.** For every knowledge note the agent depends
   on, open the note: does it carry per-claim verdict tokens, does it name a verifier
   (`verified_by`), or does it self-attest? A note that says `status: verified` and names
   nobody is unverified.
3. **State-of-the-world sentences.** Any sentence in the agent that describes how the
   world *currently* is — "the hook is not installed", "this suite has not been re-run",
   a count of anything. Check each against the tree today.

**Forces:** one row per moving value — `claim · asserted at file:line · source fetched ·
current value · fresh / stale / unverifiable`.

**Why this one exists:** a SkillsBench per-domain figure was copied into a procedure and
overtaken by three revisions of the paper, then propagated into two further documents
(`docs/audit-agent-builder-loop-p4.md:158-223`). Separately, two agent bodies told their
agents *"neither hook is installed … prose is not a wall"* while both hooks were
installed and passing 42 of 42 controls — so the passage written to stop the agent
mistaking prose for a mechanism was telling it the one real mechanism was prose
(`docs/domain-research-test-results.md:63-85`). And 5 of the 12 notes this repo's
knowledge map routes to carry **no** per-claim verdict token at all
(`docs/BACKLOG.md:529-535`).

---

## L3 · Wall versus body

**Hunts:** an impossibility the body claims and the mechanism does not deliver.

**Procedure.** Extract every statement in the agent about what it cannot do — the "may
not", "never", "cannot" list — and put each in a table against the mechanism named for
it. Then classify each mechanism:

- an **absent tool** — check the `tools:` line and confirm the tool is genuinely not
  there, and that no granted tool subsumes it. A path-scoped write gate next to `Bash`
  is decorative; `Agent` is a shell one hop away wherever nesting is on.
- a **hook** — check the file exists, is executable, is wired with an **anchored**
  matcher, and that a re-runnable control harness names it. A hook whose controls were
  run once by hand cannot detect its own regression.
- **prose** — the finding. Record it as `mechanism` class.

Then, for every hook in force, say **what class of failure it cannot see**. Path gates
cannot see content or speech. Do not accept a green control table as containment.

**Forces:** one row per stated impossibility — `claim · file:line · mechanism named ·
mechanism verified how · holds / decorative / prose only`; plus one line naming what the
mechanisms are structurally blind to.

**Why this one exists:** *"every wall here is a path gate; every failure mode the brief
cares most about is content or speech"* — 44 of 44 control rows passing, and zero
observations of behaviour (`docs/domain-research-test-results.md:291-296`). Four of seven
installed hooks had no re-runnable harness (`docs/audit-agent-builder-loop-p5.md:328-385`).
And a gate written to enforce safety was found to **deny the compliant artefact and allow
the dangerous one** (`.claude/skills/agent-assembly/evals.md:664-736`).

**Note this pass cannot execute.** Every row here is read, not run. Say so, and route the
payload replays up.

---

## L4 · Reachability and collision

**Hunts:** a part nothing routes into, or two parts competing for the same work.

**Procedure.** Two directions.

- **In.** Grep the whole tree for the agent's name and for the *symptoms* it exists to
  handle. Which files route work to it — a description, a step, a NOT-clause, a
  procedure? A zero count is the finding. Then check the reverse: does every part the
  agent routes *to* exist, as a file, at the path it names?
- **Across.** Take every agent description in the repo, strip stopwords, and compute
  term overlap against this one. For any pair above the roster's own noise floor, check
  whether a NOT-clause in one names the other. A deliberate split has NOT-clauses in both
  directions; a collision has none. Report the pair, the overlap, and the shared terms.

**Forces:** `routes-in count · the query`; `routes-out targets · exists or dead`; and a
pair table `agent A · agent B · overlap · NOT-clause present`.

**Why this one exists:** an entire pipeline stage was built, walled and tested with
nothing routing into it — `grep -icE 'research|domain-researcher|sweep|commission'`
returned **0** across all four artefacts of the loop that owned it
(`docs/BACKLOG.md:476-482`). And two agents in this repo overlap at **0.195** on
description terms with no NOT-clause between them, standing open as an unchecked eval
case (`docs/review-agent-builder-loop.md:56-71`).

---

## L5 · Promise coverage

**Hunts:** something the agent's own documents say exists, and does not.

**Procedure.** Do not read for what is present. Take every list the agent or its
documents promise — the artefacts a step emits, the files a placement table assigns, the
references a skill opens, the eval suite, the controls that were run, the specs, the hook
proposals — and check each item **as a listing**, never as a reading of the report that
claims it. Then sweep the reverse direction: files under `references/` and `assets/` that
no step opens never load, so they are promises that cannot be kept.

Every step in the agent's procedures must end in an artefact. A step ending in a
consideration is a promise with nothing behind it; count them.

**Forces:** one row per promised item — `promised at file:line · exists · listing that
proves it`; plus a count of steps with no artefact.

**Why this one exists:** an arm of this repo's own ablation asserted *"the bar is in
`EVALS-migration-reviewer.md`, written by a subagent that did not author any of this"*
and `git ls-tree` showed no such file (`.claude/skills/agent-assembly/evals.md:793-812`).
A claimed artefact is the cheapest lie to tell and the cheapest to catch. Separately, a
preloaded skill was found not to exist at all (`docs/CHANGELOG.md:143`), two of seven
agents shipped with no eval artefact of any kind, and two reference files sat in tiers
whose whole definition is "loads when a step opens it" with no step opening either
(`docs/audit-agent-builder-loop-p5.md:494-547`).

---

## Choosing

If the request names a fault class, take the matching lens. If it does not, take **L1 ·
Grounding**: it is the class this repo's own reviews found most of, and it is the one a
reader who already knows the system is least likely to run unprompted.

Then name the four you did not run. That sentence is the document's honesty and step 1
requires it.
