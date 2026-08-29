# Audit — the agent-builder loop, perspective P5 · Absence

Run of `.claude/skills/design-claim-audit/SKILL.md` against the loop that turns
"we should have an agent for X" into a shipped, tested agent.

**Date:** 2026-08-29. **Tree state at close:** `4f67ce7`. The pass opened at
`5c7aaf1`; **three commits landed during it** — `0451c1a`, `bf14c2a`, `4f67ce7` —
and `.claude/validate/agents.py` and `.claude/validate/selftest.sh` changed on disk
mid-audit. Every count below was re-run at `4f67ce7` unless the row says otherwise,
and every grep excludes this file so the audit does not count itself.

**Auditor:** a session that authored none of the artefacts under audit. A shell was
available and was used; the `not checkable here` verdict below is used for what a
*moving tree* could not settle, not for what a shell could not run.

---

## 0 · Provenance

| Artefact | Author | Verdict on auditability |
|---|---|---|
| `.claude/agents/agent-builder.md` | the commissioning session (commits `04c2961`, `dd6eb99`, `ab284ad`, `a0e1c67`) | auditable — not this session's work |
| `.claude/skills/agent-shape/` | same | auditable |
| `.claude/skills/agent-baseline/` | same | auditable |
| `.claude/skills/agent-assembly/` | same | auditable |
| `.claude/validate/agents.py`, `selftest.sh` | same (`4c6db65`, `8d43f78`, `bf14c2a`) | auditable |
| `.claude/hooks/*.sh` | same | auditable |
| `docs/decomposition-agent-pipeline.md` | `system-decomposition`, run by the commissioning session | auditable |
| `docs/BACKLOG.md` B125–B137 | same | auditable |

**No row abstains.** Step 0 did not fire: this session wrote none of it, in this
session or a previous one.

## 1 · Perspective

**P5 · Absence.** Hunts what is not there. The procedure is: take each capability
the loop *claims*, grep for the absence of its mechanism by name across the whole
tree, and treat a zero count as the yield. Then check each promised list against
the tree.

`this pass is one perspective and is not coverage; perspectives not run: P1 ·
Tenancy and identity, P2 · Failure handling, P3 · Lifecycle and reachable state,
P4 · Claim versus artefact.`

Anything noticed outside P5 is a one-line referral at the end, not an
investigation.

**Pre-read per step 6:** `/home/user/scio/docs/as-built/REVIEWS-FINDINGS-VERIFIED.md`
was opened. Its 35 findings are all about the Scio product code (deploy, sandbox
egress, observability, idempotency replay, 501 endpoints). **No finding below
re-reports one of them**; the surfaces do not overlap.

---

## The capability table

One row per capability the loop claims. `count` is the number of **matching lines**
returned by the query, at `bf14c2a`, unless a different unit is named.

| # | Capability claimed | Query run | Count | Verdict |
|---|---|---|---|---|
| A-01 | every agent ships with evals | per-agent: files whose name is `evals.md`/`*tester-brief*`/`*test-results*` **and** which name the agent | prospector **0**, adjudicator **0** (5 others ≥1) | refuted |
| A-02 | assembly routes into the validator | `grep -rn 'validate/agents.py' .claude/skills/agent-{assembly,shape,baseline}/ .claude/agents/agent-builder.md` | **0** | refuted |
| A-03 | shape → baseline → assembly is the order | `grep -rniE '\bspec\b\|\bbaseline\b\|failure table' .claude/hooks/` → 2 incidental; `grep -niE '\bevals?\b' .claude/validate/agents.py` | **0** | refuted |
| A-04 | hooks ship as proposals a human installs | `grep -rl 'agent-builder-scope' docs/hook-proposal-*.md docs/rebuild-agents/hook-proposal-*.md` | **0** | refuted |
| A-05 | a hook's controls are a re-runnable table | hooks with a script under `.claude/validate/` naming them | **3 of 7** | refuted |
| A-06 | `unevidenced` marks steps leaning on thin evidence | `grep -rn 'unevidenced' --exclude-dir=.git --exclude=audit-agent-builder-loop-p5.md .` | **2**, of which **0** are the marker on a spec step | refuted |
| A-07 | `agent-shape` emits a component manifest | `grep -rni 'manifest' .claude/skills/agent-shape/` | **0** | refuted |
| A-08 | tier-3/4 files load when a step opens them | orphan sweep over `*/references/*`, `*/assets/*` | **2 of 21** orphaned | refuted |
| A-09 | every agent names a stopping condition | `grep -rni 'stopping condition' .claude/agents/` | **1 of 7** | refuted |
| A-10 | four credentialing rows are empty | `grep -rniE '\bproctor\|\bfppe\b\|\boppe\b\|\bre-review\b\|\bregistry\b\|\bwithdrawal\b' .claude/` | **0** | holds |
| A-11 | the backlog carries status per item | `grep -nE '\| B1(2[5-9]\|3[0-7]) \|' docs/BACKLOG.md` | **0** of 14 | refuted |
| A-12 | procedure content comes from the measured base | `grep -rniE 'variance\|repeat[- ]n\|multiple runs' .claude/` → 1 unrelated; `grep -rniE 'pressure scenario\|rationali[sz]ation' .claude/` | **0** | refuted |
| A-13 | matchers are anchored | `grep -ni 'settings' .claude/validate/agents.py` | **0** | refuted |
| A-14 | the test goes to a fresh subagent | `ls .claude/agents/ \| grep -i 'test\|eval\|grader'` | **0** | refuted |
| A-15 | research drafts and verdicts pair up | `grep -rniE 'drafts/\|verdicts/\|commissions/' .claude/validate/agents.py` | **0** | not checkable here |
| A-16 | the pipeline decomposition ran `system-decomposition` | `grep -n '^## 2 ' docs/decomposition-agent-pipeline.md` | **0** | refuted |
| A-17 | `agent-shape` emits a spec under `docs/` per agent | specs found: `docs/agent-spec-*.md` + `docs/rebuild-agents/SPEC.md` | **3** for **7** agents | refuted |

---

## Findings

### [A-01] Two of the seven agents ship with no eval artefact of any kind

| Field | Assessment |
|---|---|
| Priority | P1 · Category | Coverage of a promised list |
| Status | Verified problem |
| Confidence | High · Effort | M |

**Evidence.** `CLAUDE.md` (§"Building agents in this repo") states: *"Every agent
ships with evals carrying a negative control and a containment case — can it exceed
its remit?"* `agent-assembly/SKILL.md` step 6 repeats it as the step's artefact.

Unit: **one file whose name marks it an eval suite, a tester brief or a test-results
document, and whose text names the agent.** Query, per agent:

```
grep -rl "<agent>" --exclude-dir=.git . | grep -Ei "evals\.md|tester-brief|test-results" | wc -l
```

| Agent | Count |
|---|---|
| `agent-builder` | 3 |
| `architect` | 8 |
| `architect-rebuild` | 1 |
| `domain-researcher` | 2 |
| `primary-source-verifier` | 2 |
| **`rebuild-prospector`** | **0** |
| **`rebuild-adjudicator`** | **0** |

**Disconfirming check (step 3).** Second vocabulary, in case the suite is named
something else:
`grep -rlniE 'prospector|adjudicator' --exclude-dir=.git . | xargs grep -lniE 'eval|tester|test case|verdict'`
→ **7** files. Inspected one by one: `docs/rebuild-agents/SPEC.md` is the *spec and
baseline* (its verdict column is `teach`/`wall`/`draw` — baseline vocabulary, not
eval vocabulary); `docs/CHANGELOG.md:143` records a defect *found in* the
prospector's preload; `.claude/skills/proposal-adjudication/SKILL.md` is a skill;
`docs/agent-spec-domain-research.md` names them only as prior work. **None is a
test of either agent.** The finding survives.

`git log --all --oneline --name-only | grep -i 'eval\|tester'` returns no deleted
suite either — the artefacts were never written.

**Problem.** Two of seven agents — 29% of the roster — were built, walled and
shipped with the step the loop calls non-negotiable never run and never staged. The
other three untested agents at least carry a *tester brief* saying step 6 is unmet
(`docs/architect-rebuild-tester-brief.md`, `docs/domain-research-tester-brief.md`);
these two carry nothing, so a reader cannot tell the step was skipped.

**Consequence.** The containment case is exactly the case these two need. Both
carry `Write` and a diet hook (`rebuild-prospector-diet.sh`); the prospector's whole
value rests on its diet being real, and nothing has ever tested that the diet holds.

**Root cause.** The promise lives in `CLAUDE.md` prose and in a skill step. Nothing
counts agents against eval suites — see A-02 and A-14.

**Recommendation.** Either write the two suites, or write the two tester briefs that
say the step is unmet, matching the precedent the other three set. Then add the
count to `.claude/validate/agents.py`: an agent with no eval artefact is a `WARN`.

**Verification.** Re-run the per-agent query; every row ≥1.

**Dependencies.** A-14 (no tester agent exists to dispatch to).

---

### [A-02] The arrow `assembly → validate` has no call site

| Field | Assessment |
|---|---|
| Priority | P1 · Category | A stage nothing routes into |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** `docs/decomposition-agent-pipeline.md:74-76`: *"All forward: research
→ shape → baseline → assembly → validate → test. No part imports a later one."* and
`:81-83`: *"assembly points at the validator, not the reverse."*

```
grep -rn 'validate/agents.py' .claude/skills/agent-assembly/ .claude/skills/agent-shape/ \
  .claude/skills/agent-baseline/ .claude/agents/agent-builder.md
→ 0
grep -rn 'selftest' .claude/skills/ .claude/agents/ docs/
→ 0
```

`agent-assembly/SKILL.md` step 5 ("Verify mechanically — by delegation") lists five
checks in prose — line-anchored frontmatter, dead cross-references, the tool
surface, referenced files, claimed artefacts — **every one of which the validator
already implements**, and names the validator nowhere. The delegate is told what to
look for, not what to run.

**Disconfirming check.** `grep -rn "agents\.py" --exclude-dir=.git .` outside
`.claude/validate/` → **10** hits, at `docs/hook-proposal-research-commission.md:170`,
`docs/hook-proposal-note-promotion.md:196`, `docs/domain-research-tester-brief.md:84`,
`docs/domain-research-test-results.md:58,189`, `docs/agent-spec-domain-research.md:12,475`,
and three others. So the validator *is* named — in specs, hook proposals and test
results, i.e. in **documents the builder produced**, never in the **procedure that is
supposed to invoke it**. The arrow is drawn in the map and absent from the road.

**Problem.** The document that decided the validator's shape says the validator is
the single home of the construction rules and that assembly points at it. The
skills describe the procedure but do not point at it, so the one part that
mechanically enforces the rules is reached only if the delegate happens to find it.

**Consequence.** The rules can be checked and are not required to be. A build that
skips the validator produces no signal that it was skipped; step 5's artefact ("the
check output") is satisfied by any delegate's output.

**Root cause.** The change-matrix decision (§1) moved the *rules* into the validator
and did not move the *call* into the procedure.

**Recommendation.** One line in `agent-assembly/SKILL.md` step 5: *"Run
`python3 .claude/validate/agents.py` and paste the raw output"*, and one in step 6
for `.claude/validate/selftest.sh`. Both files exist and both exit non-zero on
failure.

**Verification.** `grep -c 'validate/agents.py' .claude/skills/agent-assembly/SKILL.md` ≥ 1.

**Dependencies.** None.

---

### [A-03] Nothing requires a spec, a baseline or an eval suite to exist before an agent file is created

| Field | Assessment |
|---|---|
| Priority | P1 · Category | A rule stated in prose and enforced nowhere |
| Status | Verified problem |
| Confidence | High · Effort | M |

**Evidence.** The order is asserted in four places:
`agent-builder.md:75` *"Run them in that order"*; `agent-shape/SKILL.md:132`
*"Then hand to `agent-baseline` — **not** to assembly"*; `agent-baseline/SKILL.md`
("Handing over") *"`agent-assembly` builds only from the `teach` and `wall` rows"*;
`agent-assembly/SKILL.md` ("When this does not apply") *"**No baseline was run.**
Assembly builds from observed failures."*

What enforces it:

```
grep -rniE '\bspec\b|\bbaseline\b|failure table' .claude/hooks/          → 2
```
Both are incidental: `agent-builder-scope.sh:54` is the self-protection path list
(`.claude/skills/agent-baseline/*`), and `note-promotion.sh:87` is a prose comment.

```
grep -niE '\bevals?\b' .claude/validate/agents.py                        → 0
grep -rniE '\bevals?\b|\btester\b' .claude/hooks/                        → 1 (a comment)
grep -rn 'agent-spec' .claude/hooks/ .claude/validate/                   → 0
```

`agent-builder-scope.sh` decides on **path shape only**: allowed roots, denied
subpaths, and `[ -e "$abs" ]` for create-only. It has no notion of a precondition
file.

**Disconfirming check.** The same repo *does* build sequence gates when it means to:
`research-commission.sh` refuses a draft write unless
`docs/research/commissions/<id>.md` exists, and `note-promotion.sh` refuses a note
unless a verdict document for that id exists and the note does not. Both are
exercised by `.claude/validate/research-hooks-controls.sh` — **46 passed, 0 failed**
when run here (1 observation, this session). So the technique is present in the
repo, understood, and simply not applied to the builder's own three stages.

**Problem.** `CLAUDE.md` states the house rule: *"A 'must never' is a hook or an
absent tool, never a sentence. Prose warnings failed in three studies and backfired
in a fourth."* The loop's own ordering rule — the one that separates observed
failure from invented procedure content — is a sentence, in four places.

**Consequence.** An `agent-builder` run can write `.claude/agents/foo.md` and
`.claude/skills/foo-thing/SKILL.md` with no spec, no baseline and no failure table
in the tree, and every wall and every validator reports clean. The failure this
guards against is the one the skills themselves name: *"you are writing your
opinion into a procedure, where it will read as evidence."*

**Root cause.** Stage 1 (research) was walled because a *tester* found it orphaned
(B137). Stages 2–4 were never subjected to the same test.

**Recommendation.** Extend `agent-builder-scope.sh` by the pattern
`research-commission.sh` already establishes: a write to `.claude/agents/<n>.md` is
denied unless `docs/agent-spec-*.md` naming `<n>` exists. Ship it as a proposal
under `docs/` with a control table, per the loop's own rule — and note that the
proposal for this hook's *current* version was never written (A-04).

**Verification.** Add the deny case to a control harness and run it; the harness
does not yet exist (A-05).

**Dependencies.** A-04, A-05, A-17.

---

### [A-04] The wall that binds `agent-builder` was installed without the proposal the loop requires

| Field | Assessment |
|---|---|
| Priority | P2 · Category | A promised list, incomplete |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** The rule appears three times.
`agent-builder.md:33` *"Emit hooks as proposals under `docs/`; a human installs them."*
`agent-shape/SKILL.md` §6 *"Emit the hook as a **proposal for a human to install**,
not as something the builder writes itself."*
`agent-assembly/SKILL.md` §4 *"Write the hook under `docs/` using
`assets/hook-proposal.md`, with its controls."*

```
ls docs/hook-proposal-*.md docs/rebuild-agents/hook-proposal-*.md | wc -l   → 5
ls .claude/hooks/*.sh | wc -l                                              → 7
grep -rl 'agent-builder-scope' docs/hook-proposal-*.md \
        docs/rebuild-agents/hook-proposal-*.md                             → 0
grep -rl 'lint-fix'          docs/hook-proposal-*.md ...                   → 0
```

**Disconfirming check.** Was a proposal written and deleted?
`git log --all --oneline --name-only | grep -i hook-proposal | sort -u` returns
exactly the five that exist plus the template `assets/hook-proposal.md`. **No
proposal for `agent-builder-scope.sh` has ever been in this repository's history.**

**Problem.** The one wall standing between a privilege-granting agent and the rest
of the machine — `agent-assembly/evals.md:15` calls it *"one 60-line hook"* — is the
only agent wall with no proposal document, no stated control table under `docs/`,
and no human-install record. `docs-only-write.sh` is named in
`docs/hook-proposal-citation-provenance.md`; `lint-fix.sh` is a `PostToolUse`
formatter and arguably out of the rule's scope.

**Consequence.** The proposal is where a hook's control table lives — the cases that
must pass, the cases that must be denied, traversal, prefix-lookalike, empty path,
malformed input. For this hook that table exists only inside `agent-assembly/evals.md`,
a file the same session's tester wrote, and it is not re-runnable (A-05).

**Root cause.** The hook predates the rule: `agent-builder.md` and the hook were
committed together at `04c2961`, before the proposal discipline was written down.

**Recommendation.** Back-fill `docs/hook-proposal-agent-builder-scope.md` from
`assets/hook-proposal.md`, carrying the control table already exercised in
`agent-assembly/evals.md`, and reconcile it against the script as installed.

**Verification.** `ls docs/hook-proposal-*.md | wc -l` = 6, and each installed
non-formatter hook is named in exactly one.

**Dependencies.** A-05.

---

### [A-05] Four of the seven installed hooks have no re-runnable control harness

| Field | Assessment |
|---|---|
| Priority | P1 · Category | A promise of a list, incomplete |
| Status | Verified problem |
| Confidence | High · Effort | M |

**Evidence.** Unit: **one executable script under `.claude/validate/` that invokes
the hook with a PreToolUse payload and asserts allow/deny.**

```
for h in <each hook basename>; do grep -rl "$h" .claude/validate/ | wc -l; done
```

| Hook | Harness |
|---|---|
| `architect-rebuild-write-gate.sh` | 1 — `architect-rebuild-gate-controls.sh` |
| `note-promotion.sh` | 1 — `research-hooks-controls.sh` |
| `research-commission.sh` | 1 — `research-hooks-controls.sh` |
| **`agent-builder-scope.sh`** | **0** |
| **`docs-only-write.sh`** | **0** |
| **`rebuild-prospector-diet.sh`** | **0** |
| `lint-fix.sh` | 0 (formatter, not a wall) |

Both existing harnesses were run this session: `research-hooks-controls.sh` →
**46 passed, 0 failed**; `architect-rebuild-gate-controls.sh` → **23 passed, 0
failed**; `selftest.sh` → **16 positive controls, 0 failed**. One observation each.

**Disconfirming check.** Is `agent-builder-scope.sh` re-run from anywhere else?
`grep -rln 'agent-builder-scope' --include=*.sh --include=*.py --exclude-dir=.git .`
→ **1**, the script itself. Its containment cases exist only as prose-plus-quoted-
output inside `.claude/skills/agent-assembly/evals.md` (72 table rows), which no
command executes.

**Problem.** Three walls — including the builder's own, and including the
prospector's diet, which is the entire mechanism behind that agent's measured
reason to exist — have controls that were run once, by hand, and cannot be re-run.

**Consequence.** A regression in any of the three is silent. `agent-builder-scope.sh`
is the file whose *own header* explains that a builder able to write hooks can
delete its wall; the same reasoning applies to a wall whose controls have rotted
unnoticed.

**Root cause.** The harness discipline arrived with stage 1 (`7ef1669`) and was not
back-fitted to the three walls built before it.

**Recommendation.** Write `.claude/validate/agent-builder-scope-controls.sh` and
`.claude/validate/docs-only-write-controls.sh` on the pattern of
`research-hooks-controls.sh`, porting the cases already written in
`agent-assembly/evals.md` and `docs/rebuild-agents/hook-proposal-prospector-diet.md`.
Then have one command run all of them.

**Verification.** Each of the six non-formatter hooks named by ≥1 script under
`.claude/validate/`; all harnesses exit 0.

**Dependencies.** A-04 (the proposals carry the control tables to port).

---

### [A-06] `unevidenced` is a status a step is told to write, that nothing writes and nothing reads

| Field | Assessment |
|---|---|
| Priority | P2 · Category | A status nothing sets or reads |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.**
```
grep -rn 'unevidenced' --exclude-dir=.git --exclude=audit-agent-builder-loop-p5.md .   → 2
```
Unit: **one occurrence of the token `unevidenced`.** Both hits inspected:

1. `.claude/skills/agent-shape/SKILL.md:36` — the definition itself: *"| `thin` | the
   domain appears, but as `REPEATED` claims or without per-claim verdicts | proceed,
   and mark every step that leans on it `unevidenced` |"*.
2. `docs/research/drafts/c2-narrow.md:373` — the ordinary English adjective inside a
   `domain-researcher` draft (*"The frequency premise of the whole agent is
   unevidenced by this sweep"*). Not the 0b marker, not on a spec, not on a step.

So **0** of 2 are the marker the rule asks for. This second hit appeared mid-pass —
the draft was committed at `0451c1a`, after the audit opened — which is itself the
point: a fresh `domain-researcher` run used the word and did not use the mechanism.

**Disconfirming check.** Second vocabulary across the three specs
(`docs/agent-spec-architect-rebuild.md`, `docs/agent-spec-domain-research.md`,
`docs/rebuild-agents/SPEC.md`):
`grep -rniE 'unevidenced|no evidence behind|evidence: absent|thin coverage'`
→ **0**. The `covered`/`thin`/`absent` ruling step 0b demands is likewise recorded
in **0** of the 3 specs.

**Problem.** Step 0b was added to close B137 and introduced a three-value verdict
plus a marker. No spec carries a 0b ruling, no step downstream looks for
`unevidenced`, and nothing checks a spec has one. The marker is write-only, and
in fact never written.

**Consequence.** The distinction step 0b exists to draw — evidence-backed content
versus content the base is thin on — is invisible to `agent-baseline` and
`agent-assembly`, which read the spec. An `unevidenced` step and an evidenced one
are indistinguishable downstream.

**Root cause.** 0b was authored as a gate on *proceeding* and not as a field on the
spec that later steps read. `assets/` has no spec template, so the field has no home.

**Recommendation.** Either put the 0b verdict in a spec template that
`agent-assembly` step 1 reads, or drop the `unevidenced` marker and keep only the
`absent` → commission branch, which does route somewhere real.

**Verification.** `grep -c 'unevidenced' docs/agent-spec-*.md` ≥ 1 per spec written
after the change, or the sentence removed.

**Dependencies.** A-17 (there is no spec template and no spec for two agents).

---

### [A-07] `component manifest` — a job the pipeline attributes to `agent-shape` that `agent-shape` has no step for

| Field | Assessment |
|---|---|
| Priority | P2 · Category | A stage named, nothing routes into |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** `docs/decomposition-agent-pipeline.md:104` enumerates `agent-shape`'s
jobs: *"1 triage · 2 diet · 3 split · 4 tool surface · 5 boundary · 6 **component
manifest**"*, and rules *"six jobs, name covers one … Accepted, recorded here"*.

```
grep -rni 'component manifest' --exclude-dir=.git .   → 1   (that line)
grep -rni 'manifest' .claude/skills/agent-shape/       → 0
```

**Disconfirming check.** Second vocabulary — is job 6 present under another name?
`agent-shape` steps are: 0 reuse gate, 0b evidence gate, 1 job sentence, 2 diet,
3 split, 4 functions, 5 tool surface, 6 wall, 7 composition, 8 emit the spec. Step 8
says only *"Under `docs/`, carrying every artefact above."* There is no step whose
artefact is an enumeration of the agent's components (body, skills, references,
assets, hook). The far-domain row that motivated it —
*"Delineation of privileges — an enumerated list of permitted procedures … we grant,
we do not enumerate"* (`:20`) — is unresolved, not renamed.

**Problem.** A decomposition ruled that a part does six jobs, accepted the sixth
rather than splitting it out, and the part has five steps for it. The accepted job
was recorded and never built.

**Consequence.** `agent-assembly` step 1 must produce a placement table covering
"every spec item", against a spec that was never required to enumerate its
components. Nothing can detect a component that was specified and never placed —
which is precisely the class that caught `selection-dossier` (`docs/CHANGELOG.md:143`:
*"`selection-dossier` was preloaded by `rebuild-adjudicator` and did not exist"*).

**Root cause.** The job was enumerated in the decomposition, not in the skill.

**Recommendation.** Either add the manifest to `agent-shape` step 8 (an enumerated
list of files the agent will consist of, which `agent-assembly` step 1 checks off and
the validator can verify exists), or amend `decomposition-agent-pipeline.md:104` to
five jobs and record the delineation row as still empty.

**Verification.** `grep -c 'manifest' .claude/skills/agent-shape/SKILL.md` ≥ 1, or
the decomposition row corrected.

**Dependencies.** A-02.

---

### [A-08] Two of the loop's own tier-3/tier-4 files are opened by no step, so they never load

| Field | Assessment |
|---|---|
| Priority | P2 · Category | Something produced that nothing consumes |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** `agent-assembly/SKILL.md` step 1 defines the contract:
*"| 3 · `references/` | when a step opens it | …"*, *"| 4 · `assets/` | at the emit
step | templates |"*. A reference no step opens never enters context.

Orphan sweep — for every file under `*/references/`, `*/assets/`, `*/scripts/`,
does the sibling `SKILL.md` name it?

```
total reference/asset files under .claude/skills/ : 21
orphans                                            :  2
  agent-assembly/references/antipatterns.md
  agent-assembly/assets/evals.md
```

**Disconfirming check.** Named under a different string?
`grep -rniE 'antipattern' .claude/skills/*/SKILL.md` → **0**.
`grep -niE 'eval template|assets/evals|template for the evals' .claude/skills/agent-assembly/SKILL.md` → **0**.
`antipatterns.md` is mentioned exactly twice outside its own folder:
`.claude/agents/agent-builder.md:30`, as narrative (*"a tester quoted
`antipatterns.md` back at it"*), and in `agent-assembly/evals.md`, where the tester
listed it in a `cat` command. Neither is a step opening it.

**Problem.** `antipatterns.md` is 52 lines of the loop's negative examples — the
surface granted by omission, the boundary written as a sentence, the rules that
never arrived. `assets/evals.md` is the eval template step 6's artefact is supposed
to follow. Both sit in the tiers whose whole definition is "loads when a step opens
it", and no step opens either.

**Consequence.** Step 6 asks for `evals.md` "with per-case verdicts" and hands the
author no template; the two suites that were written (`agent-assembly/evals.md`,
`docs/domain-research-test-results.md`) share no structure with the template or with
each other. The antipattern catalogue reaches a build only by accident.

**Root cause.** The validator checks dead references in **one direction only** —
`agents.py` scans the body for `` `references/...` `` and fails if the file is
missing. It never scans the folder for files the body does not name.

**Recommendation.** Name both from the step that should use them (`antipatterns.md`
from step 2 or 3; `assets/evals.md` from step 6), and add the reverse check to
`agents.py`: a file under `references/`/`assets/` that no `SKILL.md` names is a
`WARN`.

**Verification.** Re-run the orphan sweep; count 0. Add a `selftest.sh` positive
control that plants an orphan and asserts the warning fires.

**Dependencies.** A-02.

---

### [A-09] `agent-shape` requires a stopping condition; one of seven agents states one

| Field | Assessment |
|---|---|
| Priority | P3 · Category | A required artefact nothing checks |
| Status | Verified problem |
| Confidence | Medium · Effort | S |

**Evidence.** `agent-shape/SKILL.md` §5: *"**Name the stopping condition.** An
autonomous loop needs one … Say what it is, or say the agent is not autonomous."*
It is listed among that step's required artefacts.

```
grep -rni 'stopping condition' .claude/agents/   → 1
```
`.claude/agents/domain-researcher.md:127` — *"stopping condition is the question
list, not a number of sources or claims."*

**Disconfirming check.** The step allows the alternative *"say the agent is not
autonomous"*. `grep -rniE 'not autonomous|is not an autonomous' .claude/agents/` →
**0**. So six agents state neither branch. Severity is held at P3 because six of the
seven are single-shot procedures rather than loops, and the step's own escape clause
would likely apply — but it is not written down anywhere, which is the finding.

**Problem.** A required artefact of step 5 is present in 1 of 7 agent files, and
nothing counts it.

**Consequence.** `agent-builder` holds the `Agent` tool and can dispatch; nothing in
its file bounds how many times.

**Recommendation.** State the branch in each agent body, or drop the artefact from
step 5 for non-looping agents and say so explicitly in the step.

**Verification.** Every agent file matches `stopping condition|not autonomous`.

**Dependencies.** None.

---

### [A-10] Three of the four empty credentialing rows are still empty, with nothing in `.claude/` for any of them

| Field | Assessment |
|---|---|
| Priority | P2 · Category | Absence, correctly recorded |
| Status | **Holds** — the document's claim is true and the gap is live |
| Confidence | High · Effort | L |

**Evidence.** `docs/decomposition-agent-pipeline.md:14-27` borrows hospital
credentialing and finds four rows the pipeline had nothing for: primary source
verification, proctoring (FPPE), ongoing evaluation (OPPE), suspension/withdrawal —
plus, from the noun list, the registry (`:96-98`).

```
grep -rniE '\bproctor|\bfppe\b|\boppe\b' .claude/                             → 0
grep -rniE '\bre-review\b|\bperiodic\b|\bongoing evaluation\b' .claude/       → 0
grep -rniE '\bregistry\b|\bwithdrawal\b' .claude/                             → 0
grep -rnE  '^(owner|version):' .claude/agents/                                → 0
grep -rniE 'shadow|supervised|probation|trial period|observation period' .claude/ → 0
```

**Disconfirming check.** Row 1 (primary source verification) **was** closed: stage 1
exists as `domain-researcher` + `primary-source-verifier` with two hooks, and
`docs/research/evidence/c4-x1-run.md` records two observed behavioural passes. So
the pipeline does close these rows when it works on them — the remaining three were
recorded as B131/B132/B133 and not worked.

**Problem.** Nothing observes an agent between "evals passed" and independent
operation; nothing re-reviews a live agent; no agent file carries an owner, a
version or a withdrawal path.

**Consequence.** `agent-builder.md` itself records the staleness mechanism this
guards against — Sonnet 4.5's context-anxiety mitigation, unnecessary by Opus 4.5.
Two values in the loop are declared to move on their own (model limits, subagent
limits); nothing re-checks the seven agents against them on any schedule.

**Root cause.** Recorded as backlog rather than designed, deliberately (§0b: *"Four
empty rows. They are the point of the step"*). The finding is that the record has no
status — A-11.

**Recommendation.** A registry is the cheapest of the three and unblocks the other
two: a single `docs/agents-registry.md` with one row per agent (owner, version,
spec, eval artefact, date last reviewed, state), generated and checked by
`agents.py`. That table also mechanises A-01, A-09 and A-17.

**Verification.** The registry exists and `agents.py` fails when an agent file has
no row.

**Dependencies.** A-11.

---

### [A-11] The fourteen newest backlog items carry no status, priority or phase

| Field | Assessment |
|---|---|
| Priority | P2 · Category | A status the document can carry that nothing sets |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** `docs/BACKLOG.md` carries a status table whose row shape is
`| id | description | phase | priority | status |`:

```
grep -cE '^\| B[0-9]+ \|' docs/BACKLOG.md                     → 118
last id in the table                                          → B123
grep -cE '^\*\*B1(2[4-9]|3[0-7]) —' docs/BACKLOG.md           → 14
grep -nE  '\| B1(2[5-9]|3[0-7]) \|' docs/BACKLOG.md           → 0
grep -n   'B13[1-4]' docs/ROADMAP.md                          → 0
```

B124–B137 exist only as prose sections. `CLAUDE.md` requires *"Update status in
ROADMAP and BACKLOG"* after every task.

**Disconfirming check.** Do the prose sections carry status by another means? Some
do, inline and informally — B128 *"SETTLED 2026-08-29"*, B130 *"ADDRESSED …
PENDING TEST — not closed"*. But `todo`/`done`, the phase column and the P0–P3
column are absent from all 14, so no query can list open agent-layer work, and the
two forms cannot be sorted together.

**Problem.** Every backlog item raised by the agent-builder loop lives outside the
mechanism the backlog uses to say what is open.

**Consequence.** B131, B132, B133, B134 — the four rows A-10 covers — appear nowhere
in `ROADMAP.md` and carry no priority. Nothing distinguishes them from the eleven
items that are recorded as closed in the same prose.

**Root cause.** The prose sections grew as narrative during agent-layer work; the
table was not extended.

**Recommendation.** Add the 14 rows to the status table with phase and priority,
keeping the prose as the detail; or state in the file that items above B123 use a
different convention and what it is.

**Verification.** `grep -cE '^\| B[0-9]+ \|' docs/BACKLOG.md` = 132.

**Dependencies.** None.

---

### [A-12] Two eval failure modes measured in the knowledge base have no step in the loop

| Field | Assessment |
|---|---|
| Priority | P1 · Category | A failure mode in the base with no step |
| Status | Verified problem |
| Confidence | High · Effort | M |

**Evidence.** `CLAUDE.md`: *"Knowledge is **queried** from
`/home/user/skills-repo/knowledge/notes/`, not copied."* `agent-shape/references/
knowledge-map.md` is the index of which note answers which question.

**(a) Variance across runs.** `skill-authoring-eval-methodology.md:38-40` —
*"**Variance analysis.** Run the benchmark **multiple times** and measure variance,
not a single pass — so a skill isn't judged on one lucky/unlucky run."*

```
grep -rniE 'variance|repeat[- ]n|multiple runs' .claude/   → 1
```
The single hit is `knowledge-note-drafting/references/base-format.md:54`, an
unrelated quotation about between-condition variance.

**(b) Pressure scenarios and meta-testing.** `testing-skills-methodology.md:34-49` —
*"Combine **3+ pressures**: time, sunk cost, authority, economic, exhaustion,
social … Academic questions ('what does the skill say?') test recitation, not
compliance"*, and the meta-test.

```
grep -rniE 'pressure scenario|rationali[sz]ation' .claude/   → 0
grep -rni  'meta-test' .claude/                              → 0
grep -rniE 'adversarial|under pressure|temptation|jailbreak' \
  .claude/skills/agent-{assembly,shape,baseline}/SKILL.md    → 0
```

**(c) The two notes are not cited by the loop at all.** For each of the 26 notes,
count of loop artefacts naming it (`agent-builder.md` + the three skill folders +
`agents.py`): **12 of 26 are cited 0 times**, including
`testing-skills-methodology.md` (0), `skill-authoring-eval-methodology.md` (0) and
`agent-builder-prior-art.md` (0) — the three most directly about building and
testing agents. `knowledge-map.md` lists 12 notes; neither eval note is among them.

**Disconfirming check.** `agent-baseline` step 2 does require *"at least two
independent runs"* — that is variance at the **baseline**, and it is present. The
absence is at step 6, the **eval**: `agent-assembly/SKILL.md` step 6 names four case
types (normal, negative control, containment, trigger) and one dispatch. No repeat,
no variance report. Step 7 says *"Never a green number alone"* but asks for blind
spots, not observation counts. Confirmed against `design-claim-audit`'s own step 4:
*"One green run is one observation."*

**Problem.** The loop's own audit procedure requires an observation count behind any
behavioural claim, and the loop's eval step produces exactly one observation and no
place to record that.

**Consequence.** `agent-assembly/evals.md` reports 72 rows from one session;
`docs/domain-research-test-results.md` records 2 behavioural observations out of 25
cases. Neither can distinguish a systematic pass from a lucky draw — the same
argument `agent-baseline` uses to require two runs, not applied to the test.

**Root cause.** `knowledge-map.md` routes shaping questions to the base and routes
no question to the two eval-methodology notes; step 6 was written from
first principles.

**Recommendation.** Add both notes to `knowledge-map.md` with the question each
answers, and add to step 6: the number of runs behind each verdict, and at least one
pressure-shaped containment case rather than only path-shaped ones.

**Verification.** `grep -c 'testing-skills-methodology' .claude/skills/agent-shape/references/knowledge-map.md` ≥ 1;
every eval suite states runs-per-case.

**Dependencies.** A-14.

---

### [A-13] The anchored-matcher rule is enforced in agent files and nowhere else — and `settings.json` breaks it

| Field | Assessment |
|---|---|
| Priority | P3 · Category | A rule enforced in one place only |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** `agents.py` fails any unanchored `matcher:` in an **agent**
frontmatter, with the reason *"a matcher is a substring search, so `Write` also
matches TodoWrite and `Edit` also matches NotebookEdit"*, and `selftest.sh` guards it
with three positive controls (t10, t10b, t10c).

```
grep -ni 'settings' .claude/validate/agents.py    → 0
grep -n  'matcher'  .claude/settings.json         → 1
```
`.claude/settings.json:31` — `"matcher": "Edit|Write"`, for the `PostToolUse` hook
`lint-fix.sh`. This is the exact string form `selftest.sh` case t10 plants as a
defect.

**Disconfirming check.** Is `settings.json` checked by something else?
`grep -rn 'settings.json' .claude/validate/` → **1**, at
`architect-rebuild-gate-controls.sh:49`, which asserts a *write* to the file is
denied — a path gate, not a content check. Nothing parses it.

**Problem.** The validator's scan set is `.claude/agents/*.md`, `agents/*.md`,
`.claude/skills/*/SKILL.md` and `skills/*/SKILL.md`. Project settings — which
carry the repo-wide hooks, the permission allow/deny lists and the enabled plugins —
are outside it.

**Consequence.** Low for this instance: `lint-fix.sh` firing on `TodoWrite` and
`NotebookEdit` costs a spurious formatter run, not a breach. The finding is
structural — the file that grants permissions and installs repo-wide hooks is
unchecked by the mechanical checker, so the same class of defect in a `PreToolUse`
entry there would be invisible.

**Root cause.** The validator was scoped to "agents, skills and their roster" and
settings were not in that noun list.

**Recommendation.** Anchor the matcher to `^(Edit|Write)$`, and extend `agents.py`
to parse `.claude/settings*.json` for the same matcher rule and for hook commands
that exist and are executable. Add a `selftest.sh` control.

**Verification.** Plant an unanchored matcher in a throwaway `settings.json`;
the validator names it.

**Dependencies.** None.

---

### [A-14] The pipeline's final stage has no named part

| Field | Assessment |
|---|---|
| Priority | P1 · Category | A stage nothing routes into |
| Status | Verified problem |
| Confidence | High · Effort | M |

**Evidence.** `docs/decomposition-agent-pipeline.md:74` ends the arrow list at
`test`, and `:70` gives the tester a hiding row (*"scenario design, provided the
suite still carries a negative control and a containment case"*), so the tester is
treated as **a part of the pipeline**. `agent-assembly/SKILL.md` step 6: *"Dispatch
an agent that has **not** seen the authoring."*

```
ls .claude/agents/ | grep -i 'test\|eval\|grader'   → 0
```
Seven agents exist; none is a tester. Nothing names what to dispatch, what tools it
should hold, or what diet it should have.

**Disconfirming check.** Is the tester meant to be a generic `Agent` dispatch rather
than a defined agent? Possibly — but the loop's own §0b/§3 reasoning says an
undefined dispatch inherits a diet nobody chose, and the recorded outcome is that
the step has failed in **four** consecutive builds:
`docs/architect-repair-tester-brief.md:5` (*"no `Bash` tool and no `Agent`/`Task`
tool"*), `docs/architect-rebuild-tester-brief.md:2` (*"the `Agent` tool was disabled
for the session that built it"*), `docs/domain-research-tester-brief.md:3`, and
`docs/domain-research-test-results.md:8` (*"**This session holds no `Agent` tool
either**"*). Two agents got no brief at all (A-01).

**Problem.** The stage the loop calls non-negotiable — *"an untested agent shipped
as done is the failure this whole procedure exists to prevent"* — is the only stage
with no part, no file, and no tool guarantee.

**Consequence.** Of seven agents, one has a run eval suite, two have observations on
2 of 25 cases, two have unmet briefs, and two have nothing.

**Root cause.** Testing was specified as a dispatch rather than as a part, so no
`agent-shape` pass ever ran on it and nothing gives it a tool surface.

**Recommendation.** Run the loop on the tester: shape it, baseline it, build
`.claude/agents/agent-tester.md` with an explicit `tools:` including `Bash`, and a
wall that denies writes to `.claude/agents/` and `.claude/skills/` so it can grade
but not repair. Then step 6 names a target instead of a property.

**Verification.** `.claude/agents/agent-tester.md` exists and `agents.py` is CLEAN;
step 6 names it.

**Dependencies.** A-01, A-12.

---

### [A-15] Nothing sweeps the research artefacts for orphans

| Field | Assessment |
|---|---|
| Priority | P3 · Category | Something produced that nothing consumes |
| Status | **Not checkable here** — the tree moved during the pass |
| Confidence | Medium · Effort | S |

**Evidence.** At `bf14c2a`:

```
verdicts with no matching draft:  docs/research/verdicts/x3-nosources.md,
                                  docs/research/verdicts/x4-dead.md          → 2
drafts with no matching verdict:  docs/research/drafts/c2-narrow.md,
                                  docs/research/drafts/x2-subagent-limits.md → 2
grep -rniE 'drafts/|verdicts/|commissions/' .claude/validate/agents.py       → 0
```

**Why this is `not checkable here`.** Between the start of this pass (`5c7aaf1`) and
`bf14c2a`, `drafts/x3-nosources.md` and `drafts/x4-dead.md` were removed and
`drafts/c2-narrow.md` and `drafts/x2-subagent-limits.md` appeared. The imbalance is
therefore a snapshot of work in flight, not a steady state, and **one observation of
a moving tree is not an observation**. What would settle it: re-run the pairing
query on a quiet tree.

**What does hold** is the mechanism absence: `research-commission.sh` and
`note-promotion.sh` gate the *write* (46 control rows, all passing), and no sweep
checks the tree afterwards, so an orphan on either side is silent whether or not one
exists right now.

**Recommendation.** A pairing check in `agents.py`, or an explicit note in
`docs/research/README.md` that unpaired ids are expected while fixtures live there.

**Dependencies.** None.

---

### [A-16] The pipeline decomposition has no §2 — the boundary was never drawn on team shape

| Field | Assessment |
|---|---|
| Priority | P2 · Category | A step named by the procedure, absent from its output |
| Status | Verified problem |
| Confidence | High · Effort | S |

**Evidence.** `docs/decomposition-agent-pipeline.md:3` — *"Produced by running
`system-decomposition` on the pipeline itself, 2026-08-29."* Its headings:

```
grep -n '^## ' docs/decomposition-agent-pipeline.md
→ 0 · noun list | 0b · far domain | 1 · change matrix | 3 · what each part hides
  | 4 · arrows | 5 · repaired downstream | 6 · job lists | Backlog raised
```

`grep -n '^## 2 ' docs/decomposition-agent-pipeline.md` → **0**. The skill's step 2
is `.claude/skills/system-decomposition/SKILL.md:78` — *"## 2 · Draw the boundary on
the team, and say what it costs"*.

**Disconfirming check.** Is step 2's content present under another heading?
`grep -rniE '\bteam\b|handoff cost|ownership' docs/decomposition-agent-pipeline.md`
→ 0 for team and ownership; §1 discusses *parts that open* on a change, which is the
change-matrix step, not the team step. It is a skipped step, not a renamed one.

**Problem.** A document that declares itself the output of a named procedure is
missing one of that procedure's seven steps, and every step of that procedure is
defined to end in an artefact.

**Consequence.** The step that was skipped is the one that costs a seam: what each
boundary costs to cross. The pipeline has six parts and every handoff is a document
written by one session and read by another — precisely the cost step 2 exists to
price. It is also the step most likely to have surfaced A-14, since the tester is
the one part with no owner.

**Root cause.** Not recorded; the document does not say the step was declined, which
the skill's own decline section permits.

**Recommendation.** Run step 2 and add §2, or add one line saying it was declined
and why. `agents.py` cannot check this; a reviewer can.

**Verification.** `grep -c '^## 2 ' docs/decomposition-agent-pipeline.md` = 1.

**Dependencies.** None.

---

### [A-17] Three specs exist for seven agents, and `agent-builder` has none

| Field | Assessment |
|---|---|
| Priority | P2 · Category | A promise of a list, incomplete |
| Status | Verified problem |
| Confidence | High · Effort | M |

**Evidence.** `agent-shape/SKILL.md` step 8: *"Emit the spec. Under `docs/`,
carrying every artefact above."* `agent-assembly` declines without one.

```
ls docs/agent-spec-*.md docs/rebuild-agents/SPEC.md            → 3
```
`docs/agent-spec-architect-rebuild.md` (architect-rebuild),
`docs/agent-spec-domain-research.md` (domain-researcher + primary-source-verifier),
`docs/rebuild-agents/SPEC.md` (rebuild-prospector + rebuild-adjudicator) — five
agents covered. `architect` is specified by `docs/decisions/0021-the-architect-agent.md`
instead, which is an ADR, not a spec.

```
ls docs/agent-spec-agent-builder.md 2>/dev/null | wc -l        → 0
grep -rl '^# Spec — .*agent-builder' docs/                     → 0
```

**Disconfirming check.** Was `agent-builder` exempt as the bootstrap? Nothing says
so. `git log --all --name-only | grep agent-spec` shows only the two files that
exist. `agent-builder.md` cites no spec, and `agent-assembly/evals.md` — its eval
suite — lists what it is testing (`:5-6`) without naming a spec, so the tester had
no spec to grade against either.

**Problem.** The agent that enforces "no assembly without a spec" was assembled
without one, and the loop's own gate (A-03) could not have caught it.

**Consequence.** There is no recorded must-see/must-not-see list, no tool
justification per tool, no stopping condition (A-09) and no composition decision for
`agent-builder` — the one agent in the repo holding `Agent`, `Write`, `Edit`,
`WebFetch` and `WebSearch` together.

**Root cause.** Bootstrap order: the builder was written before the procedure it
runs existed in final form.

**Recommendation.** Write `docs/agent-spec-agent-builder.md` retrospectively from
the artefacts that exist (the agent body, the hook, `agent-assembly/evals.md`), mark
it *reconstructed, not derived*, and treat any gap it exposes as a finding. Then make
the precondition mechanical per A-03.

**Verification.** Each of the 7 agents named by ≥1 spec document under `docs/`.

**Dependencies.** A-03.

---

## Out-of-perspective referrals

One line each, no investigation — these are outside P5 and belong to another pass.

- **P4** — `.claude/skills/agent-assembly/evals.md` declares *"Author: independent
  tester (this session). **Not** the author of the agent"* while living inside the
  skill folder it grades; whether the separation held is a claim-versus-artefact
  question.
- **P4** — `CLAUDE.md` asserts *"a canary probe measured that rules … do not reach a
  subagent; only this file does"*; the probe's record was not located in this pass.
- **P4** — `.claude/validate/agents.py` and `selftest.sh` were modified during this
  audit (`5c7aaf1` → `bf14c2a`, commit message *"the validator was lending a house
  rule the authority of a spec"*); any claim about the validator's messages should
  be re-checked against the new text.
- **P3** — `docs/research/verdicts/` and `drafts/` currently pair 0 for 4; whether
  either directory is reachable in steady state is a lifecycle question.
- **P2** — `agent-builder-scope.sh` denies on `__NOPATH__` and on a failed path
  resolution, so a malformed payload is fail-closed; what the *other* six hooks do
  on the same input was not examined here.

---

## Coverage and verdicts

`this pass is one perspective and is not coverage; perspectives not run: P1 ·
Tenancy and identity, P2 · Failure handling, P3 · Lifecycle and reachable state,
P4 · Claim versus artefact.`

| Verdict | Count |
|---|---|
| `refuted` | 15 |
| `holds` | 1 |
| `not checkable here` | 1 |
| `abstained` | 0 |
| **Total rows** | **17** |

**Numbers used above, with their unit and query, in one place.**

| Number | Unit | Query |
|---|---|---|
| 7 agents | files matching `.claude/agents/*.md` | `ls .claude/agents/*.md \| wc -l` |
| 19 skills | folders with a `SKILL.md` | `ls .claude/skills/*/SKILL.md \| wc -l` |
| 7 hooks | executable scripts | `ls .claude/hooks/*.sh \| wc -l` |
| 5 hook proposals | files named `hook-proposal-*.md` under `docs/` | `ls docs/hook-proposal-*.md docs/rebuild-agents/hook-proposal-*.md` |
| 3 harnesses | executables under `.claude/validate/` | `ls .claude/validate/` |
| 21 reference/asset files | files under `*/references/`, `*/assets/`, `*/scripts/` | `find */references */assets */scripts -type f` |
| 26 knowledge notes | files in the base | `ls /home/user/skills-repo/knowledge/notes/` |
| 118 backlog table rows | lines matching `^\| B[0-9]+ \|` | `grep -cE '^\| B[0-9]+ \|' docs/BACKLOG.md` |
| 14 prose backlog items | lines matching `^\*\*B1(2[4-9]\|3[0-7]) —` | `grep -cE ... docs/BACKLOG.md` |

**Behavioural claims and their observation counts.** Three harnesses were executed
**once each** this session: `selftest.sh` → 16 positive controls, 0 failed;
`research-hooks-controls.sh` → 46 passed, 0 failed;
`architect-rebuild-gate-controls.sh` → 23 passed, 0 failed;
`agents.py` → `agents 7 · skills 19 · roster ~1230/15000 tokens (8%)`, CLEAN.
**One green run is one observation** and none of these is a claim of stability.

## What this pass could not check

- **Whether any agent actually behaves as specified.** No agent was dispatched. All
  17 rows are about mechanisms present or absent in the tree, not about behaviour.
- **Whether the two existing hook harnesses cover their hooks completely.** They
  pass; whether the case sets are adequate is a different perspective's question.
- **Steady-state pairing of research artefacts** (A-15) — the tree moved during the
  pass.
- **Whether `agent-assembly/evals.md`'s 72 rows were genuinely produced by an
  independent tester.** That is provenance, P4.
- **The four perspectives not run**, and specifically: no path was traced for
  failure handling, reachable state or tenancy. This pass found what is missing; it
  did not read what is present.
