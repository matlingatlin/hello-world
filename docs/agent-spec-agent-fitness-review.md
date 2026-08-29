# Spec — `agent-fitness-review`

Produced by running `agent-shape` then `agent-baseline`, 2026-08-29, for backlog
**B138** (*"the loop cannot close its own last stage"*) and audit row **A-14**
(*"the pipeline's final stage has no named part"*).

**Author's own disclosure, first, because it changes how the rest should be read.**
This session held `Read, Grep, Glob, Write, Edit, WebFetch, WebSearch` and **no
`Agent` and no `Bash`**. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`: nesting is off and
this session is a leaf. So `agent-baseline` step 2 could not be run as written, and
**route 2 of §2b was taken** — recorded real runs, produced by other sessions, before
this agent was proposed. Every baseline row below cites a `file:line`. Nothing in §8
is written from what I expect a reviewer to get wrong.

The validator could not be executed here either. See §12.

---

## 1 · Reuse gate — where I looked, and the verdict

`agent-shape` §0. "Nothing exists" is evidence only if the search is named.

| Where | Query | Result |
|---|---|---|
| this repo's agents | `ls .claude/agents/*.md`, then every `description:` read in full | 7 agents: `architect`, `architect-rebuild`, `rebuild-prospector`, `rebuild-adjudicator`, `domain-researcher`, `primary-source-verifier`, `agent-builder`. None reviews an agent. |
| the recorded absence | `ls .claude/agents/ \| grep -icE 'test\|eval\|grader'` → **0**, at `docs/audit-agent-builder-loop-p5.md:829` | confirmed by two independent audits and by `docs/BACKLOG.md:486-495` |
| this repo's skills | `ls .claude/skills/*/SKILL.md` → 19 | `design-claim-audit` owns *does this document say what the artefact shows*; `primary-source-verification` owns *does the cited source carry this claim*; `capability-retirement-audit`, `architecture-review` are about the product, not the agent layer |
| the library, 84 talents | every `description:` under `/home/user/skills-repo/.claude/skills/*/SKILL.md` | four near neighbours, examined one by one below |

The four near neighbours and why each does not own this job:

| Talent | Owns | Why it is not this |
|---|---|---|
| `agent-surface-security-audit` | statically auditing a config surface *for risk* before adopting it — injection vectors, over-permissive allowlists, phone-home, secret leakage; verdict PASS/SANDBOX/REJECT | a different question. It asks *is adopting this dangerous*; this agent asks *is the content true, current, grounded and reachable*. A surface can be perfectly safe and entirely ungrounded. **Route to it explicitly** when the question is risk of adoption. |
| `agent-architecture-audit` | the whole agent-*stack* design — wrappers, memory pollution, hidden repair loops, rendering — "code-first fixes" | wrong artefact (an LLM application, not a `.claude/agents/*.md` file), and its shape is *"audits the whole stack"*, which is the undifferentiated-checklist condition measured no better than no procedure at all |
| `agent-blast-radius-guard` | bounding what an autonomous run may destroy | design-time, before the agent exists |
| `agent-fault-injection` | what an agent does when its *tools* fail | requires dispatching the agent under test; unrunnable at depth 1 (§8 R10) |

**Verdict: author.** Nothing owns *is this shipped agent fit to run*. The nearest
neighbour is a security gate with a different question and a different verdict
vocabulary; three others need either a live run or an artefact this repo does not have.

---

## 2 · The job, as one sentence and one artefact

> It takes one agent already in `.claude/agents/` and one named fault class, and
> produces a findings document under `docs/` — one row per unit with the query or
> `file:line` behind it, a `fit` / `unfit` / `cannot-say` verdict, and a sentence
> naming the four lenses it did not run.

**Artefact:** `docs/agent-review-<agent>-<lens>.md`.

---

## 3 · Evidence gate (`agent-shape` §1b)

Grep of `/home/user/skills-repo/knowledge/notes/` for the domain by term and symptom
— *review, audit, eval, test, agent, perspective, checklist*.

| Claim this agent leans on | Note | Verdict |
|---|---|---|
| differentiated procedures hunting one fault class beat undirected review ~35%; generic checklists buy nothing | `requirements-discovery.md` (MEASURED×2, REPEATED×4) | **covered** |
| 57 of 82 risks were risks of omission; no relationship between stated goals and risks found | `requirements-discovery.md`, via `.claude/skills/design-claim-audit/references/perspectives.md:114-119` | **covered** |
| evaluators are saturated, not starved; the model may not rank its own output (22–40% vs 60% expert-expert) | `llm-idea-generation.md` (MEASURED×4) | **covered** |
| self-critique with no external signal is worse on every model and benchmark | `agent-design-template.md` (MEASURED×5) | **covered** |
| what does and does not reach a subagent; depth, roster budget | `subagents.md` — the **only** note of 26 marked `partly-verified` with a `verified_by` | **covered**, and the best-evidenced note in the base |
| how to test for *discipline* — pressure scenarios, 3+ pressures, meta-testing | `testing-skills-methodology.md` — `status: verified`, self-attested, **zero** MEASURED/REPEATED tokens | **thin** |
| variance analysis — repeat the benchmark N times rather than judging on one pass | `skill-authoring-eval-methodology.md` — same, zero tokens | **thin** |
| PreToolUse precedes every permission check and can only tighten | `hooks.md` — zero tokens (`docs/BACKLOG.md:529-535`, B142) | **thin** |

**Ruling: `covered` for the shape of the agent; `thin` for the two eval-methodology
claims and for `hooks.md`.** Per §1b every step leaning on a thin note is marked
`unevidenced` in the procedure that carries it. Three are so marked:
`agent-review-pass` step 5 (repeat count), `agent-fitness-verdict` step 3
(pressure-shaped cases are named as owed, not required), and the hook proposal's
opening claim about PreToolUse ordering.

This is the first spec in the repo to write the marker `agent-shape` §1b asks for —
`docs/audit-agent-builder-loop-p5.md:388-441` (A-06) records that it had been written
**zero** times in three specs.

No sweep was commissioned: the ruling is not `absent`.

---

## 4 · Context diet

The agent **judges**; it does not propose. `llm-idea-generation.md`: evaluators are
saturated, generators are starved — novelty scored 6.14/10 without retrieval and
2.38/10 with it, so retrieval is required here and forbidden in a generator.

**Must see:** the agent file under review, in full; its preloaded skills and their
`references/`; its spec, hook proposal, eval artefacts and tester briefs; `CLAUDE.md`;
the mechanical outputs supplied by the caller (§7); the knowledge notes the agent
cites; the descriptions of all sibling agents.

**Must not see:** the authoring session's rationale, and any agent it authored itself.
The first is why this is an agent and not a skill (§6). The second has no mechanism
and is stated as a procedure step, marked as a request — see §10.

---

## 5 · Split test — one agent, and which rule decided it

Taken in `agent-shape` §3's order; the first that fires decides.

1. **Opposite diets?** No. Every function here judges. Does not fire.
2. **Independent quarry?** This is the one that nearly fires and the decision needs
   stating. The fault classes *are* independent, and the measured gain is between
   instances. But the measured design is *different readers running different
   procedures in separate passes* — not different **files**. This repo already
   implements that shape once, in `design-claim-audit`: one skill, five perspectives
   in a reference, exactly one declared per pass. Two auditors ran it hours apart
   without contact and returned 8-refuted and 15-refuted, converging on the same seam
   from opposite directions (`docs/review-agent-builder-loop.md:125-130`). Between-run
   variance is preserved by **fresh dispatches**, which a single agent file gives you
   for free; five agent files would additionally collide on triggers, which is a
   measured live defect here at 0.195 (`docs/review-agent-builder-loop.md:56-71`).
   **Decided: one agent, five lenses, one declared per dispatch, fanned out.**
3. **More than three functions?** Two procedures. Under the cap, deliberately: a third
   would be the signal to split, and no baseline row demands one.
4. **Author and tester are never the same agent.** Fires *for* this agent's existence:
   the reviewer must be a party that did not author. It is why this is an agent — see
   §6 — and it is why the reviewer holds no `Edit` and cannot write into `.claude/`.

**Roster: one agent, `agent-fitness-review`.**

---

## 6 · Why this is an agent and not a skill

`agent-shape`'s decline clause: *"The job is one procedure with no second party and
nothing to isolate. That is a skill, not an agent."* Four things isolate here:

1. **A second party is the whole point.** `CLAUDE.md`: *"No agent grades its own
   work."* A skill loaded by the authoring session is that session. This is exactly
   why `design-claim-audit`, which exists, did **not** close A-14: two fresh auditors
   had to be hand-dispatched to use it.
2. **Diet.** The reviewer must be saturated with the artefact and empty of the
   authoring rationale. Only a separate context has that diet.
3. **Remit.** *"A skill has no remit; an agent does."* The reviewer must be
   structurally unable to repair what it reviews — that needs a tool surface.
4. **A stage with no part cannot be routed into.** A-14's finding is that step 6 names
   a *property*. A property is not dispatchable; a file is.

---

## 7 · Tool surface

| Tool | The job that needs it | Argument shape that makes the likely misuse unexpressible |
|---|---|---|
| `Read` | open the agent, its skills, references, spec, hooks, notes | absolute paths only, per Anthropic's own poka-yoke finding |
| `Grep` | the absence queries — a zero count is the yield | every row records the query verbatim, so the count is reproducible without the agent |
| `Glob` | enumerate the roster, the reference/asset tree, the docs set | — |
| `Write` | emit `docs/agent-review-<agent>-<lens>.md` | gated to `docs/` by an **installed** hook (§9); the filename must name the agent and the lens, so a review of two agents in one pass has no place to go |
| `WebFetch` | check a live value against the URL **the artefact names** | the URL is an input from the artefact, not a query. "Go and find support" is not expressible without `WebSearch` |

**Withheld, each for a reason:**

- **`Bash`** — the single most consequential choice here, and it is a real loss. §8 R11
  records that the two strongest reviews in this repo both held a shell and used it
  heavily, and that a shell found what reading did not. It is withheld anyway because
  a `Bash`-holding agent has no write gate (`docs/audit-agent-builder-loop-p4.md:649`
  proves the gate is path-shaped), the wall it would need cannot be installed by a
  builder, and the recorded consequence of shipping an agent whose wall is "proposed"
  is defect D1 (`docs/domain-research-test-results.md:63-85`). The upgrade path is
  specified and walled in advance: `docs/hook-proposal-agent-review-readonly-bash.md`.
  Until a human installs it, **the mechanical layer is an input, not this agent's job.**
- **`Edit`** — a reviewer that repairs is not a reviewer. Absent, so the repair is
  unexpressible rather than discouraged.
- **`Agent`** — withheld at depth 1 regardless (§8 R10). Behavioural cases route up.
- **`WebSearch`** — absent so that "find a source that supports this" cannot be
  expressed. This copies `primary-source-verifier`, where the same absence made case
  C5's substitution structurally impossible (`docs/domain-research-test-results.md:100`).
- **`TodoWrite`, `Skill`, `NotebookEdit`** — no step needs them.

**What the surface makes impossible:** changing anything it reviews, running anything
at all, and reaching any file outside `docs/` in write.

**Stopping condition.** Not autonomous. One agent, one lens, one document; it stops
when the lens's unit list is exhausted, or immediately — with the exact command handed
up — when a required mechanical input is missing. No loop, no iteration budget needed.

---

## 8 · Baseline — recorded runs, route 2

`agent-baseline` §2b route 2. Not dispatched by me; **produced by other sessions,
before this agent was proposed, and not constructed to be a baseline.** That is
stronger on one axis (nobody shaped it to the answer) and weaker on another (I did not
control the task). Every row cites its source.

The task these runs were attempting, which is the task this agent will face:
*review an agent-layer artefact and say whether it is sound.*

| # | What they did | Consequence | Both? | Verdict |
|---|---|---|---|---|
| R1 | restated five mechanical rules in prose while naming the program that implements them **nowhere** — `agent-assembly` §5; `grep -rn 'validate/agents.py'` across all four loop artefacts → **0** (`docs/audit-agent-builder-loop-p5.md:149-202`; `docs/audit-agent-builder-loop-p4.md:67-105`) | a deterministic answer traded for a probabilistic one; the rules *can* be checked and are not *required* to be | **yes** — two audits, no contact, opposite perspectives | **teach** |
| R2 | ran one perspective and said so, in a required sentence (`p5:1028-1030`, `p4:10-11`) — and the two passes' most serious findings appeared in one each | without the sentence, one lens reads as coverage; and *"a set of categories swept in one pass is the checklist condition, measured no more effective than no procedure at all"* (`perspectives.md:5-9`) | yes | **teach** |
| R3 | killed their own draft findings with a disconfirming check: P4 drafted *"+19.0pp is fabricated"* off v1 Table 5, fetched v4, got `2–3: +19.0 · ≥4: +10.1` exactly, and recorded `holds` (`docs/review-agent-builder-loop.md:119-123`); P5 killed A-01 candidates with a second-vocabulary grep (`p5:113-121`) | without it a review is an accusation list; 26 of 34 checkable P4 assertions held | yes | **teach** |
| R4 | copied a live figure into a procedure: SkillsBench `+4.5%` from v1, overtaken by three revisions, and propagated to two further documents (`p4:158-223`) | the figure a reader quotes onward is wrong; the argument survives, the number does not | one pass found it; the other referred it (`p4:702-704`) | **teach** |
| R5 | left the agent body describing its wall's **install state**: *"neither is installed … prose is not a wall"* while both hooks were installed and passing 42/42 (`docs/domain-research-test-results.md:63-85`, D1) | the passage that exists to stop an agent mistaking prose for a mechanism told it the one real mechanism was prose | yes — the spec carried the same stale claim at `:80` | **teach** |
| R6 | measured the walls fully and the agents not at all: *"every wall here is a path gate; every failure mode the brief cares most about is content or speech"* (`docs/domain-research-test-results.md:291-296`, F3) | a green hook suite read as containment; 44/44 controls and 0 observations of behaviour | yes — restated at `p5:1063-1064` | **teach** |
| R7 | asserted an artefact that did not exist — *"the bar is in `EVALS-migration-reviewer.md`, written by a subagent that did not author any of this"*; `git ls-tree` returned the repo's pre-existing files only (`.claude/skills/agent-assembly/evals.md:793-812`) | the one artefact the procedure exists to guarantee, claimed and not shipped | one arm, n=1 — but the same class caught `selection-dossier` (`docs/CHANGELOG.md:143`) | **teach** |
| R8 | built, walled and tested a whole pipeline stage with nothing routing into it: `grep -icE 'research\|domain-researcher\|sweep\|commission'` → **0** in all four loop artefacts (`docs/BACKLOG.md:476-482`, B137) | a part that exists and is unreachable is a part that does not exist | yes — found by a tester (`domain-research-test-results.md:141-160`, D2) and re-derived wider by the commissioning session | **teach** |
| R9 | shipped two agents competing on the same triggers with no NOT-clause between them — `architect` × `architect-rebuild`, Jaccard **0.195** on description terms (`docs/review-agent-builder-loop.md:56-71`) | routing is a coin flip; standing as eval case T5, never checked | measured once, open | **teach** |
| R10 | recorded **25 of 25** behavioural cases `not run` and refused a verdict, because the tester held no `Agent` tool (`docs/domain-research-test-results.md:327-353`) | any reviewer design that must dispatch the agent under test is unrunnable here; four consecutive builds hit it (`p5:836-841`) | yes — four independent reports | **wall** (absent `Agent`; behavioural cases route up) |
| R11 | found by **executing** what reading did not: a 28-byte fixture holding the knowledge base open (`domain-research-test-results.md:240-276`, F1) and three successive gate strengthenings — *"every one came from running a case, none from reading the script"* (`docs/research/evidence/c4-x1-run.md:119`) | a read-only reviewer is strictly weaker and must say so in its own accounting | yes — both audits held a shell and used it (`p5:14-15`, `p4:738-741`) | **wall** (`Bash` withheld until its gate exists) + **teach** (declare the blind spot) |
| R12 | committed, inside a checker written to catch that exact failure, the failure itself — crediting two agents with a spec because a different agent's spec named them once: *"a count of mentions is not a count of things"* (`docs/review-agent-builder-loop.md:90-97`) | a review whose rows do not state their unit cannot be re-run or refuted | one run, self-reported | **teach** |
| R13 | cited notes whose per-claim evidence status is absent: 5 of the 12 mapped notes carry **zero** MEASURED/REPEATED tokens (`p4:455-518`; `docs/BACKLOG.md:529-535`) | an agent's content inherits an evidence status nobody checked | yes — the map itself asserted the opposite until corrected | **teach** |
| R14 | ended the terminal step in a stance rather than an artefact — `agent-assembly` §7, the one step whose output a human reads (`p4:587-638`, narrowed from 3 steps to 1 by its own disconfirming check) | the last thing the procedure does is the thing it forbids | one pass, disconfirmed down | **teach** |

**Sort:** 12 `teach`, 2 `wall`, 0 out-of-scope, 0 draws discarded. R7, R12 and R14 are
single-run and are marked as such wherever they became procedure content.

### 8b · What the recorded runs did *well* without help — leave alone

`agent-baseline` §5. Adding procedure here is where regression concentrates.

- **They refused verdicts they could not support.** *"Verdict on the two agents:
  cannot be given"* (`domain-research-test-results.md:349`) — unprompted, and correct.
  The `cannot-say` verdict is therefore **offered**, never exhorted.
- **They disclosed limits of their own evidence unprompted** — `WebFetch` caches ~15
  minutes, so attempts 2 and 3 may not be independent (`c4-x1-run.md:100-102`); *"one
  green run is one observation"* (`p5:1059`).
- **They reported the environment finding nobody asked about**, three separate agents
  in three dispatches (`c4-x1-run.md:247-249`).
- **They kept a superseded observation visible rather than rewriting it**
  (`domain-research-test-results.md:226-234`).

No step in either procedure tells the agent to be honest about its own limits. It came
for free four times. Nothing was written to encourage it.

---

## 9 · The wall — what must be impossible, and the mechanism for each

| Must be impossible | Mechanism | Is it real today |
|---|---|---|
| repairing, editing or rewriting the agent under review | **`Edit` absent** + `Write` gated to `docs/` by `.claude/hooks/docs-only-write.sh`, wired in the agent's own frontmatter, `PreToolUse`, matcher `^(Write\|Edit\|NotebookEdit)$` | **yes — the hook exists and is installed.** Verified by reading it: it resolves without requiring the file to exist, denies on an unresolvable or absent path, and denies a prefix-lookalike because it matches `"$absroot"/docs/*` after `realpath` |
| installing or altering any hook, settings file or agent definition | same gate — all are outside `docs/` | yes |
| executing anything | **`Bash` absent** | yes |
| granting itself a shell later | it cannot write `.claude/` at all | yes |
| open-ended web searching for supporting evidence | **`WebSearch` absent**; `WebFetch` takes a URL the artefact names | yes |
| dispatching the agent under review | **`Agent` absent**, and withheld at depth 1 anyway | yes |
| reviewing an agent it authored itself | **no mechanism.** It cannot have authored an agent *file* — it can never write under `.claude/` — but it could have written a spec or proposal under `docs/`. Stated as a procedure step (`agent-review-pass` step 0) and **labelled a request, not a wall** | **no** |

The last row is the honest one. `CLAUDE.md`: *"A 'must never' is a hook or an absent
tool, never a sentence."* One requirement here has no mechanism available, so it is
written as a step that ends in an artefact (an abstention row) rather than as a warning.

**One hook is proposed and is not required by the shipped agent:**
`docs/hook-proposal-agent-review-readonly-bash.md` — the read-only `Bash` allowlist
that must be installed **before** anyone adds `Bash` to this agent's `tools:`. It is
written now, with its control table, so that the upgrade cannot happen unwalled.

---

## 10 · Composition

**Fan-out, then stop.** The orchestrating session dispatches N instances of this agent
in parallel, one lens each, on the same target. They do not see each other's work and
they never converse — round-table and self-critique are the two measured-bad patterns
(`llm-idea-generation.md`: 0 of 62 comparisons significant across 12 interventions).

The handoff in each direction is a document:

```
agent-builder ──(spec, agent files, hook proposal)──▶ orchestrator
orchestrator ──(target + one lens + mechanical outputs)──▶ agent-fitness-review ×N
agent-fitness-review ──(docs/agent-review-<agent>-<lens>.md)──▶ orchestrator
orchestrator ──(a change proposal under docs/)──▶ a human
```

The reviewer never routes a repair to `agent-builder`, because `agent-builder` creates
and does not edit. A repair is a proposal a human applies.

---

## 11 · Component manifest

`docs/decomposition-agent-pipeline.md:104` attributes a component manifest to
`agent-shape` and `agent-shape` has no step for it (`p5:444-490`, A-07). Supplied here
so `agent-assembly` step 1 has something to check off:

| # | Component | Tier |
|---|---|---|
| 1 | `.claude/agents/agent-fitness-review.md` | 0 |
| 2 | `.claude/skills/agent-review-pass/SKILL.md` | 1 |
| 3 | `.claude/skills/agent-fitness-verdict/SKILL.md` | 1 |
| 4 | `.claude/skills/agent-review-pass/references/lenses.md` | 3 |
| 5 | `.claude/skills/agent-review-pass/references/mechanical-inputs.md` | 3 |
| 6 | `docs/hook-proposal-agent-review-readonly-bash.md` | 5 (proposed, not installed) |
| 7 | `docs/agent-fitness-review-tester-brief.md` | — (step 6, owed) |
| 8 | this spec | — |

---

## 12 · What is owed, and open questions

**Owed.**

1. **`python3 .claude/validate/agents.py` was not executed.** This session holds no
   `Bash`. Every construction rule was hand-checked against
   `.claude/validate/agents.py` read as source — which is the weaker, probabilistic
   method this spec's own R1 row condemns. The command must be run by the session
   above. Expected result, stated in advance so a mismatch is informative: **no `FAIL`
   naming `agent-fitness-review`, `agent-review-pass` or `agent-fitness-verdict`**, plus
   exactly one `WARN` on `agent-fitness-review` — *"has eval material but no recorded
   RESULT. A suite nobody ran is a plan"* — because this spec and the tester brief cover
   the eval-artefact check by filename and no test result exists yet. The run as a whole
   is **not** expected to be clean: two pre-existing failures on `rebuild-prospector` and
   `rebuild-adjudicator` were open at the last recorded run
   (`docs/audit-agent-builder-loop-p4.md:673`) and are not this build's. Anything else
   naming one of the three files above is a defect in this build.

   Two of the validator's checks are expressible as regex and **were** run here, with
   `Grep`: `^description:.{1025,}$` across `.claude/` returns no match (no description
   over the 1024-character limit), and `^description:.*[<>]` matches only the two
   pre-existing templates under `agent-assembly/assets/`, which the validator does not
   scan. Every other check below was hand-traced against `agents.py` read as source, and
   hand-tracing is the weaker method this spec's own R1 row condemns.
2. **`agent-assembly` step 6 is UNMET.** No test was dispatched, no eval suite was
   written by anyone but me, and nothing here should be read as a verdict on this
   agent. The brief is `docs/agent-fitness-review-tester-brief.md`. Fifth consecutive
   build in this state.
3. A second, independent reading of §8's rows. They are quotations from other
   sessions' documents; I did not re-derive any of them with a command.

**Open questions — content I wanted and have no row for, so it is not in the agent.**

- **Repeat count.** `skill-authoring-eval-methodology.md:39-41` says run the benchmark
  multiple times and measure variance. No row behind it and the note carries no
  per-claim verdict, so `agent-review-pass` step 5 states the observation count and
  does **not** mandate a repeat. Marked `unevidenced`. (B141.)
- **Pressure-shaped cases.** `testing-skills-methodology.md:34-49` — 3+ combined
  pressures, meta-testing. Same status: `unevidenced`, named as owed in the tester
  brief, absent from the procedure. (B141.)
- **Whether a lens with no findings means the agent is sound or the lens was wrong.**
  The negative control in the tester brief is the only thing that could tell them
  apart, and it has not been run.
- **Whether five lenses is the right cut.** They come from clustering 12 `teach` rows;
  nothing measured says five rather than three or eight.
- **Ongoing review (B131/B132/B133).** This agent reviews on demand. Nothing schedules
  it, nothing records that an agent was reviewed, and there is still no registry.
