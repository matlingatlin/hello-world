# Review — `agent-fitness-review` — L1 · Grounding

Reviewer: a fresh dispatch of `agent-fitness-review` itself, holding `Read, Grep, Glob,
Write, WebFetch` only (no `Edit`, no `Bash`, no `Agent`, no `WebSearch`). Target: the
agent at `.claude/agents/agent-fitness-review.md`, its two preloaded skills
(`agent-review-pass`, `agent-fitness-verdict`) and the two references
`agent-review-pass` opens (`references/lenses.md`, `references/mechanical-inputs.md`).

Dispatched with one explicit, named request: find published evidence — a real URL —
behind the "~35%" differentiated-review claim, since a reviewer will be shown this
document. That request is answered in full at Unit 1 below.

this pass is one lens and is not coverage; lenses not run in this dispatch: L2 ·
Currency, L3 · Wall versus body, L4 · Reachability and collision. **L5 · Promise
coverage was run separately**, by a different dispatch, and is already recorded at
`docs/agent-review-agent-fitness-review-L5.md`; it is not re-run here, and its own
closing note explicitly deferred citation-content checking to L1 — this document is
that deferred work.

---

## Step 0 — Provenance

| Artefact | Author | Auditable? |
|---|---|---|
| `.claude/agents/agent-fitness-review.md` | a prior session, per the launching message | auditable |
| `.claude/skills/agent-review-pass/SKILL.md` + `references/*` | a prior session | auditable |
| `.claude/skills/agent-fitness-verdict/SKILL.md` | a prior session | auditable |
| `docs/agent-spec-agent-fitness-review.md` | self-identifies as "the session that built the agent" | auditable |
| `/home/user/skills-repo/knowledge/notes/requirements-discovery.md`, `architecture-evidence.md`, `llm-idea-generation.md`, `agent-design-template.md`, `agent-builder-prior-art.md`, `hooks.md` | the shared knowledge base, not this agent's authoring session | auditable |

**Caveat carried into the accounting:** I hold no `Bash`, so authorship above rests on
the launching message and each document's own self-identification (`on a word`), not
on `git log`/`git blame`. Nothing here reads as content I could have produced — I
arrived with no memory of any of it. **Step 0 did not fire** — no row abstains.

---

## Step 1 — Lens

**L1 · Grounding.** Procedure: enumerate every directive in the agent body and its
preloaded skills — every "always", "never", threshold, effect size, named failure
mode — and for each, find what put it there: a spec row, a knowledge note, a recorded
run, or nothing. Then check the *direction* of the citation: does the cited document
actually contain the row, or a restatement of it.

---

## Step 2 — Mechanical inputs

| Command | Given? | Used how |
|---|---|---|
| `python3 .claude/validate/agents.py` | yes, raw output quoted below | confirms roster state and the one open `WARN`; not otherwise load-bearing for L1, which is a content lens, not a construction-rule lens |
| `bash .claude/validate/selftest.sh` | partial — last line only, `positive controls: pass=24 fail=0` | not required by any L1 row (belongs to L3) |
| `bash .claude/validate/*-controls.sh` | not given | not required by L1; not requested |
| `git log` / `git show` / `git ls-tree` | not given, and I hold no `Bash` | Step 0's authorship rests on a word instead (see above) |

```
agents 8 · skills 21 · roster ~1463/15000 tokens (9%)

  WARN  .claude/agents/agent-fitness-review.md: has eval material (docs/agent-spec-agent-fitness-review.md, docs/agent-fitness-review-tester-brief.md) but no recorded RESULT. A suite nobody ran is a plan [M]

CLEAN, 1 warnings
```

No L1 row was blocked by a missing mechanical input; the pass was not stopped.

---

## Step 3 — Units

**Unit = a directive inside the agent body or its preloaded skills (including
`references/lenses.md` and `references/mechanical-inputs.md`) that carries a number,
an effect size, a threshold, a `p`-value, or a named-failure-mode citation to a
`file:line`, together with whatever the document says put it there.** A bare mention
with no number and no citation (e.g. "coverage comes from parallel dispatch") is a
design choice, not a grounding unit, and is out of scope for this lens.

Enumerated with `Grep` for the pattern `%|p = 0|p=0|kappa|N of M|N–M range|docs/*.md:N`
across the four files, then corrected by hand for spelled-out numbers the regex
pattern misses ("seven places", "five checks"):

| File | Grep-matched lines | Hand-caught misses |
|---|---|---|
| `agent-fitness-review.md` | 3 | 0 |
| `agent-review-pass/SKILL.md` | 4 | 0 |
| `agent-fitness-verdict/SKILL.md` | 1 | 0 |
| `references/lenses.md` | 16 | 1 ("restated in seven places") |
| `references/mechanical-inputs.md` | 0 | 1 ("five checks restated in prose") |

**Count: 25 grounding units** by this method. This is a lower bound, stated as one —
the regex catches digits and standard effect-size shapes, not every spelled-out
number, so the true population is "at least 25." I selected **12 of the 25** for a
full grounded/restated/speculation/unevidenced row with a disconfirming check,
prioritising (a) the unit the dispatch explicitly named, (b) every unit whose citation
loops back to *this agent's own* preloaded-skill files rather than only to `lenses.md`'s
"why this lens exists" boxes, and (c) at least one unit from each of the five boxes so
no lens's rationale went completely unchecked. The remaining 13 are listed at the end
of Step 4 as read-but-not-independently-traced, per the honest-residue rule.

---

## Step 4 — Findings table

| # | Directive | file:line | What put it there | Verdict |
|---|---|---|---|---|
| 1 | "Differentiated procedures hunting one named fault class outperform undirected review by roughly 35%" | `agent-fitness-review.md:25-26`; restated `agent-review-pass/SKILL.md` step header; restated `references/lenses.md:7-8` | Traces through `requirements-discovery.md:37-47` to **Porter, Votta & Basili 1995**, *Comparing Detection Methods for Software Requirements Inspections*, IEEE TSE 21(6) 563-575 (DOI `10.1109/32.391380`, paywalled — redirect confirmed live, content not fetchable), and to **Boehm & Basili 2001**, *Software Defect Reduction Top 10 List*, IEEE Computer 34(1), which is freely hosted and was fetched in full. | **grounded** — see disconfirming check below; this is the answer to the dispatch's explicit request |
| 2 | "15–50% across replications" | same three locations as #1 | same chain | **grounded**, same fetch |
| 3 | "one of two replications was not significant (21%, p = 0.21) while the other was (30%, p = 0.0019)" | `agent-review-pass/SKILL.md` step header | `requirements-discovery.md:53-55`, verbatim match | **restated**, holds — matches its cited note exactly, note itself not independently fetchable (same paywalled primary as #1) |
| 4 | "the effect was weakest on material the reader already knew ... 'fell back to their usual technique'" | `agent-review-pass/SKILL.md` step header | `requirements-discovery.md:55-58`, verbatim match | **restated**, holds |
| 5 | "In a structured risk-discovery workshop, 57 of 82 risks were risks of omission against 25 of commission" | `agent-review-pass/SKILL.md` step 4 | Content matches `architecture-evidence.md:20,58` (SEI CMU/SEI-2009-TR-012 Mission Thread Workshop, "57 risks of omission vs 25 of commission, kappa .82"; 57+25=82, arithmetic holds) | **restated, but the spec mis-cites its own source** — see finding below |
| 6 | "independent testers found 81 defects the authors had not seen" | `agent-fitness-verdict/SKILL.md:16` | Traces to `agent-design-template.md:149,156` ("MEASURED GOOD ... 81 defects here") and `agent-builder-prior-art.md:64` — both self-attested (`status: verified`, no `verified_by`) | **unevidenced** — see finding below |
| 7 | "a model ranking candidate outputs agrees with experts 22–40% of the time where expert–expert agreement is 60%" | `agent-fitness-verdict/SKILL.md` step 2 | `llm-idea-generation.md:130-132`, citing RQ-Bench (Sinhahajari, Majumder & Poria 2026, `arxiv.org/pdf/2606.12071`) | **restated, caveat dropped** — see finding below |
| 8 | "26 of 34 checkable assertions held" / one auditor's "+19.0pp is fabricated" drafted then killed by re-fetch | `agent-review-pass/SKILL.md` step 5 | `docs/review-agent-builder-loop.md:100-102,120,129` — 26 holds + 8 refuted = 34; "+19.0pp / +10.1pp is fabricated" quote present at `:120` | **grounded**, holds exactly |
| 9 | L1's own "why this lens exists": one rule restated in seven places, the validator named in one, the loop's four artefacts named it zero times | `references/lenses.md:31-36` | `docs/BACKLOG.md:496-500` (B139): "the construction rules are restated in seven places and the validator is named in one ... `19.0pp` appears in 7 places" | **grounded**, matches |
| 10 | mechanical-inputs' own claim: "five checks restated in prose, the program that implements them named nowhere" | `references/mechanical-inputs.md:9-13` | `docs/review-agent-builder-loop.md:81` (A-02): "restating five checks the validator already implements" | **grounded**, matches |
| 11 | L2's box: "5 of the 12 notes this repo's knowledge map routes to carry no per-claim verdict token at all" | `references/lenses.md:67-69` | `.claude/skills/agent-shape/references/knowledge-map.md:9-11`: "of the twelve notes this map routes to, five carry neither anywhere — `claude-md-and-memory`, `dynamic-workflows`, `hooks`, `mcp` and `skill-anatomy`" | **grounded**, exact match, both the count and the five names |
| 12 | L4's box: "two agents in this repo overlap at 0.195 on description terms with no NOT-clause between them" | `references/lenses.md:129-131` | `docs/review-agent-builder-loop.md:56-71`: `architect` × `architect-rebuild`, 0.195, "not deliberate ... no NOT-clause between them" | **grounded**, exact match |

**Read but not independently traced (13 of 25 remaining units)** — I confirmed via
`Glob` that the cited files exist (consistent with the prior L5 pass's own listings),
but did not open the cited passages to confirm content, so these are not scored:
the L2 box's SkillsBench-figure claim (`lenses.md:61-63`, `docs/audit-agent-builder-loop-p4.md:158-223`); the L2 box's "neither hook is installed ... 42 of 42" claim
(`lenses.md:64-67`, `docs/domain-research-test-results.md:63-85`); the L3 box's "44 of
44 control rows passing, zero observations of behaviour" (`lenses.md:96-98`,
`docs/domain-research-test-results.md:291-296`); the L3 box's "four of seven installed
hooks had no re-runnable harness" (`lenses.md:98-99`, `p5:328-385`); the L3 box's gate
that "denies the compliant artefact and allows the dangerous one"
(`lenses.md:100-101`, `agent-assembly/evals.md:664-736`); the L4 box's "0" grep count
for a pipeline stage nothing routes into (`lenses.md:127-129`,
`docs/BACKLOG.md:476-482`); the L5 box's `EVALS-migration-reviewer.md`,
`git ls-tree`-not-found claim (`lenses.md:154`, `agent-assembly/evals.md:793-812`);
the L5 box's "a preloaded skill was found not to exist" (`lenses.md:156`,
`docs/CHANGELOG.md:143`); the L5 box's "two of seven agents shipped with no eval
artefact" (`lenses.md:157`, `p5:494-547`); and four more of the same shape inside
`lenses.md`'s remaining boxes.

---

## Step 5 — Disconfirming checks

| # | Finding under test | Disconfirming query | Result | Survives / killed |
|---|---|---|---|---|
| 1 | "~35%" and "15–50%" are real, checkable claims, not house folklore | Fetched `https://doi.org/10.1109/32.391380` (redirects live to IEEE Xplore, `302 Found` — the paper exists and is indexed, but the page itself returned no extractable abstract text through the fetch tool, so the primary study is *confirmed to exist* but not *confirmed by content*); fetched `https://www.cs.umd.edu/~basili/publications/journals/J81.pdf` and read it as a PDF directly. Item **SEVEN** on page 136 reads verbatim: *"Perspective-based reviews catch 35 percent more defects than nondirected reviews… Improvements in fault detection rates vary from 15 to 50 percent."* — with its own citation to V.R. Basili, "Evolving and Packaging Reading Technologies," *J. Systems and Software*, 38(1), 1997, pp. 3-12. | Both figures — 35% and the 15–50% range — are present verbatim in a freely-hosted, author-published source (Barry Boehm, USC, and Victor R. Basili, University of Maryland; *IEEE Computer*, January 2001, pp. 135-137) | **survives — holds, and is the citable URL:** `https://www.cs.umd.edu/~basili/publications/journals/J81.pdf` (page 136, item SEVEN, "Software Defect Reduction Top 10 List"). The deeper primary source it in turn cites is Porter, Votta & Basili 1995, DOI `10.1109/32.391380`, confirmed to exist and be correctly attributed via the live redirect, but paywalled — I could not fetch its content and so cannot independently confirm the 21%/30%/p-value figures against the original beyond the note's restatement (row 3, "restated, holds"). |
| 5 | The "57 of 82" figure is grounded | `Grep "82 risks\|57 of 82"` across `/home/user/skills-repo/knowledge/notes/` → **one file**, `architecture-evidence.md`. `Grep` the same pattern against `requirements-discovery.md` (158 lines, read in full at the start of this pass) → **zero** matches. But `docs/agent-spec-agent-fitness-review.md:64`, this agent's own evidence-gate row, names `requirements-discovery.md` (via `design-claim-audit/references/perspectives.md:114-119`) as the note covering this exact claim. | The figure itself is correct and un-drifted (57+25=82, kappa .82 matches both places it appears) — but the spec's evidence table cites the wrong knowledge note as its home. `perspectives.md:114-119` (checked directly) does carry the number, so the citation chain is not broken, only mislabelled one hop earlier, in the spec's summary column. | **survives, downgraded** — not a fabricated or drifted number, but a real mis-citation: the spec's own §3 table names `requirements-discovery.md` for a figure that note does not contain. |
| 6 | "81 defects" is grounded | `Grep "81 defect" -r` across `docs/`, `.claude/`, and the knowledge base. Found the claim **restated in 9 files** (`.claude/agents/agent-builder.md`, `.claude/skills/agent-shape/SKILL.md`, `.claude/skills/agent-assembly/evals.md` ×2, `.claude/skills/agent-assembly/references/delegation.md`, `.claude/skills/agent-assembly/references/antipatterns.md`, `CLAUDE.md`, `.claude/skills/agent-fitness-verdict/SKILL.md`, `.claude/skills/design-claim-audit/SKILL.md`, `docs/architect-rebuild-tester-brief.md`) but traced back to only **two** knowledge-note occurrences (`agent-design-template.md:149,156`; `agent-builder-prior-art.md:64`), both self-attested with no `verified_by`. Searched `docs/CHANGELOG.md`, `docs/BACKLOG.md`, `docs/review-agent-builder-loop.md`, `docs/audit-agent-builder-loop-p4.md`, `docs/audit-agent-builder-loop-p5.md` for a recorded run producing this specific count — found none; the nearest neighbours are smaller, later, unrelated test passes (`docs/research/evidence/c4-x1-run.md`: 3, 4, 4, 5 defects across different case subsets) and an unrelated backlog-ID collision (`B081`–`B102`). | No `docs/` artefact records the audit that produced "81." The number's only home is two self-attesting notes, repeated verbatim nine times elsewhere without ever adding a citation of their own. | **survives** — a real grounding gap, and it sits inside `agent-fitness-verdict`, one of this agent's own two preloaded skills, not just in a sibling agent's rationale. Class: `unevidenced`, per the lens's own vocabulary — "a rule with no observed row behind it is an opinion wearing a table's clothes." |
| 7 | "22–40% vs 60%" carries its source note's own caveat forward | Read `llm-idea-generation.md:195-201` in full (the section following the cited figure) | Line 201: *"RQ-Bench's headline rests on 50 samples and 2 experts."* Neither `agent-fitness-verdict/SKILL.md` step 2 nor anywhere else in this agent's files carries that qualifier — the figure is quoted as a flat comparison. | **survives** — the number itself is grounded (row 7, "restated"), but the restatement strips the sample-size caveat the source note explicitly attaches to it. This is a smaller instance of the same failure shape #6 above sits at the far end of: a number travels, its evidentiary weight does not. |

---

## Step 6 — Class of each surviving finding

| # | Finding | Class |
|---|---|---|
| 5 | Spec's evidence-gate table (`docs/agent-spec-agent-fitness-review.md:64`) names the wrong knowledge note for the "57 of 82" figure | `content` — a one-line correction to the spec's table (`architecture-evidence.md`, not `requirements-discovery.md`), a proposal a human applies |
| 6 | "81 defects," restated in 9 files including this agent's own `agent-fitness-verdict/SKILL.md`, has no `docs/`-recorded run behind it, only two self-attesting notes | `content` — the fix is either producing the missing audit record (or pointing the notes at the file that already contains it, if one exists outside my search radius) or downgrading the token from implied-MEASURED to REPEATED until one is found. Not a defect this agent's own procedure can self-correct: `agent-review-pass` step 2 explicitly forbids re-deriving what a program should settle, and there is no program that settles *this* — it is a documentation gap in the shared knowledge base, one layer below the agent |
| 7 | "22–40% vs 60%" restated without the source note's own 50-sample/2-expert caveat | `content` — add the qualifier where the figure is used, or leave it in `agent-fitness-verdict` only if the step's own point (a *recommendation*, not a delegated ranking) tolerates the caveat's absence; a human's call, not mine |

**One line of referral, outside this lens, not investigated further:** `hooks.md`
carries zero `MEASURED`/`REPEATED` tokens per the knowledge map, yet the agent body's
claim about it ("`PreToolUse` runs before every permission check … can only tighten")
matches `hooks.md:21-24` verbatim and correctly, because that is a **documented**
platform behaviour, not a study claim — the knowledge map's own distinction between
"documentation transcription" and "research synthesis" applies exactly as designed
here, and the grounding is sound. Recorded because it is a case where a "thin" note
is nonetheless the right home, so a token-count sweep alone (an L2 concern) would
have mis-flagged it.

---

## Verdict (`agent-fitness-verdict`)

### 1 · The bar, stated before scoring

Mandatory rows under L1 for this agent:

- **M1 — The flagship effect-size claim the agent's whole one-lens-per-pass design
  rests on must trace to a real, checkable, external source.** Pass condition: the
  cited document, fetched, contains the number verbatim. (Units 1–2.)
- **M2 — No numeric or effect-size claim inside this agent's own preloaded skills
  (not a sibling agent's, not a reference box's rationale) may be unevidenced —
  present with no `docs/`-recorded run and no external citation behind it, only
  self-attestation repeated elsewhere.** (Unit 6.)
- **M3 — Every source this agent's own spec names in its evidence-gate table must
  actually contain the figure the spec attributes to it.** (Unit 5.)
- **M4 — A figure whose own source note attaches an explicit sample-size or scope
  caveat must not be restated as an unqualified comparison inside this agent's
  operative procedure.** (Unit 7.)

### 2 · Verdict

**`unfit`** — under L1 · Grounding only. M1 passed cleanly: the dispatch's explicit
request is answered, with a real URL, verified by fetching it. But M2, M3 and M4 each
failed, each on a disconfirmed, surviving finding: `agent-fitness-verdict/SKILL.md`
itself carries an unevidenced number (81 defects) that is repeated nine times
elsewhere in the tree without ever picking up a citation; this agent's own spec
mis-names the source note for the "57 of 82" figure; and this agent's own
`agent-fitness-verdict` step 2 restates a figure with its source's stated caveat
dropped. None of the three is catastrophic alone, and all three are `content`-class —
correctable by a human, not by a mechanism — but the bar was stated before scoring and
three of four mandatory rows did not clear it. This says nothing about L2 · Currency,
L3 · Wall versus body, or L4 · Reachability and collision, none of which ran in this
dispatch.

### 3 · Evidence accounting

| Class | Count | Rows |
|---|---|---|
| `executed` | 0 | this pass holds no shell |
| `listed` | 2 | Step 4 units 9–10 confirmed via `Grep`/exact-quote match against `docs/` files named by their citation |
| `read` | 9 | units 1–8, 11–12 and the three disconfirming-check follow-ups (units 5, 6, 7) — each opened directly and quoted |
| `on a word` | 1 | Step 0's authorship table |

**11 of 12 scored units were verified against the cited artefact directly (fetched,
read, or grepped) rather than taken on a report's word; 1 of 12 (Step 0 authorship)
rests on a word because no mechanism to re-derive it was available in this tool
surface.** Unit 1/2's deepest primary source (Porter, Votta & Basili 1995) was
confirmed to exist and be correctly attributed via a live DOI redirect, but its content
was not independently fetchable (paywalled) — that one link in an otherwise-grounded
chain is `on a word` from the secondary source (`requirements-discovery.md` and Boehm
& Basili 2001), not independently executed.

### 4 · What this pass could not see

**Structural blind spots.**
- `Read`/`Grep`/`WebFetch` can confirm a citation points somewhere and that the target
  contains the words claimed. They cannot confirm the *underlying study itself* was
  conducted as described — I fetched Boehm & Basili's magazine column, not Porter,
  Votta & Basili's original IEEE Transactions paper (paywalled), so "grounded" here
  means "the chain to a real, indexed, peer-reviewed paper is intact and its headline
  figure is independently repeated by its own original author," not "I read the
  underlying experiment."
- Whether the 13 unscored units (Step 4's "read but not independently traced" list)
  hold or drift is genuinely unknown from this pass — I confirmed file existence only,
  which is an L5 promise-coverage check, not an L1 content check, and re-doing L5's
  work was out of scope here.
- No mechanism here can detect whether the two self-attesting knowledge notes behind
  "81 defects" are themselves accurate; I can only report that no `docs/` record of
  the underlying audit is reachable by `Grep`, not that the number is wrong.

**Not run, and why.**
- Independent verification of Porter, Votta & Basili 1995's original content —
  blocked by the DOI's paywall; `WebFetch` returned a redirect, not the paper. Would
  settle: whether the 21%/30%/p-value figures (unit 3) match the primary source or
  only its restatement in `requirements-discovery.md`.
- The 13 unscored grounding units listed at the end of Step 4 — each would need its
  own `Read` of the specific cited line range in `docs/audit-agent-builder-loop-p4.md`,
  `p5.md`, `docs/domain-research-test-results.md`, and `agent-assembly/evals.md`, none
  of which was opened in this pass. Time/scope-bounded, not blocked by any missing
  tool.
- Whether the "81 defects" audit record exists somewhere outside the `docs/` and
  `.claude/` trees I can reach (e.g. in `/home/user/skills-repo/docs/` or another
  sibling repo) — not searched, because this dispatch's `Glob`/`Grep` scope was the
  two repos already named by the knowledge notes' own file paths.

**Not checked at all.**
- L2 · Currency, L3 · Wall versus body, L4 · Reachability and collision — the three
  lenses (of the four not run) with no prior pass on record for this agent. L5 ·
  Promise coverage was already run separately (`docs/agent-review-agent-fitness-review-L5.md`).
- Whether `docs/agent-fitness-review-tester-brief.md`'s 25 behavioural cases would
  surface a different grounding picture under live use — this pass holds no `Agent`
  and did not touch that brief.

### 5 · What the reader must do next

1. **The specific request is answered:** cite
   `https://www.cs.umd.edu/~basili/publications/journals/J81.pdf` — Boehm, B. &
   Basili, V.R., "Software Defect Reduction Top 10 List," *IEEE Computer* 34(1),
   January 2001, p. 136, item SEVEN — for the "35% more defects / 15–50% range"
   figure. For the deeper primary experiment, cite Porter, L.G., Votta, L.G. &
   Basili, V.R., "Comparing Detection Methods for Software Requirements Inspections:
   A Replicated Experiment," *IEEE Transactions on Software Engineering* 21(6),
   1995, 563-575, DOI `10.1109/32.391380` — confirmed to exist and correctly
   attributed, but paywalled, so hand a subscription-backed fetch to whoever needs
   the primary numbers rather than the magazine restatement.
2. Correct `docs/agent-spec-agent-fitness-review.md:64` — the "57 of 82" row's
   Note column should name `architecture-evidence.md`, not `requirements-discovery.md`.
3. Track down or produce the `docs/` record behind "81 defects" (currently
   self-attested only, in `agent-design-template.md` and `agent-builder-prior-art.md`),
   or downgrade its status in those two notes — this agent's own
   `agent-fitness-verdict/SKILL.md:16` inherits whatever is decided.
4. Decide whether `agent-fitness-verdict` step 2's "22–40% vs 60%" line should carry
   RQ-Bench's own stated limit (50 samples, 2 experts) forward.
5. Dispatch fresh `agent-fitness-review` instances on L2, L3 and L4 in parallel — this
   document, plus the existing L5 review, cover two of five lenses on this agent.
