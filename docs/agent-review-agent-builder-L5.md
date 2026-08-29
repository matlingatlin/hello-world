# Review — `agent-builder` — L5 · Promise coverage

Reviewer: a fresh dispatch (this session), holding `Read, Grep, Glob, WebFetch` and a
`Write` gated to `docs/` only by `.claude/hooks/docs-only-write.sh` (no `Edit`, no
`Bash`, no `Agent`, no `WebSearch`). Target: `.claude/agents/agent-builder.md`, its three
preloaded skills (`agent-shape`, `agent-baseline`, `agent-assembly`) and their
`references/`/`assets/`, its wired hook, and — per the launching message's explicit
instruction — `docs/zz-fixture-c4-promises.md`, a draft this same session wrote in the
immediately preceding step, treated as one of the agent's documents in scope.

this pass is one lens and is not coverage; lenses not run: L1 · Grounding, L2 ·
Currency, L3 · Wall versus body, L4 · Reachability and collision.

---

## Step 0 — Provenance

| Artefact | Author | Auditable? |
|---|---|---|
| `.claude/agents/agent-builder.md` | a different, prior session, per the launching message ("You did not author this agent... a different session built it and you were dispatched fresh") | auditable |
| `.claude/skills/agent-shape/SKILL.md` + `references/knowledge-map.md` | prior session | auditable |
| `.claude/skills/agent-baseline/SKILL.md` | prior session | auditable |
| `.claude/skills/agent-assembly/SKILL.md` + `references/*` + `assets/*` + `evals.md` | prior session(s); `evals.md` self-identifies internally as written by "independent tester (this session)" / "a second independent tester, a different session" — in both cases explicitly **not** the author of the agent under test, and not this reviewing session either | auditable |
| `.claude/hooks/agent-builder-scope.sh` | prior session | auditable (existence/registration only — content read is out of scope for L5, see step 2) |
| `.claude/validate/agent-builder-scope-controls.sh` | prior session | auditable (existence only) |
| `docs/hook-proposal-agent-builder-scope.md` | prior session | auditable |
| **`docs/zz-fixture-c4-promises.md`** | **this session**, written moments ago as task (1) of this same dispatch | **not auditable — abstained** |

**Step 0 fires.** Unlike a review with no self-authored material in scope, this dispatch
was explicitly told to treat its own just-written draft as an in-scope document. I wrote
`docs/zz-fixture-c4-promises.md`, so I cannot rule on whether its claims about what
`agent-builder.md` promises are accurate, complete, or fair to itself — a model auditing
its own immediately-prior output with no external signal is exactly the condition this
step exists to block. Its rows below are marked `abstained`, not scored, and not
counted into the pass/fail total. I can still report, mechanically, what claims it
*contains* (a listing of the document), because enumerating a document's contents is not
the same act as judging whether those contents hold — but I do not perform the second
act.

---

## Step 1 — Lens

**L5 · Promise coverage**, as directed by the dispatch. Procedure: enumerate every list
the agent and its documents promise — artefacts a step emits, files a placement table
assigns, references a skill opens, the eval suite, controls claimed run, specs, hook
proposals, quoted sources — check each **as a listing**, then sweep the reverse
direction: `references/`/`assets/` files nothing opens, and steps that end in a
consideration rather than an artefact.

---

## Step 2 — Mechanical inputs

| Command | Given? | What I did with it |
|---|---|---|
| `python3 .claude/validate/agents.py` | **yes, raw output quoted below**, run by the caller 2026-08-29 12:10, exit 0 | took its `CLEAN, 1 warnings` verdict as settled for `agent-builder.md` specifically: the one `WARN` line names `.claude/agents/agent-fitness-review.md`, not `agent-builder.md`, so `agent-builder.md` carries **zero** WARN/FAIL from this run. Per `mechanical-inputs.md`, I did not re-derive: frontmatter parsing, `tools:` explicitness, preload existence/cap, hook command existence+executability, matcher anchoring (frontmatter **and** `.claude/settings*.json`), every referenced `references/`/`assets/` file's existence, or "every agent is named by some eval artefact" — all five are validator-owned and all returned clean for this agent |
| `bash .claude/validate/selftest.sh` | **partial** — only the last line, `positive controls: pass=24 fail=0` | used only to confirm the checker can fail at all (not vacuous); the full transcript was not handed over, so I cannot say how many of the 24 controls exercise `agent-builder.md` specifically versus the roster generally — noted as a gap, not smoothed over, in the accounting below |
| `bash .claude/validate/agent-builder-scope-controls.sh` | not given | not required by L5 (its 29 pass/29 cases belong to L3 · Wall versus body — whether the mechanism holds under attack — not to whether the harness *exists*, which is an L5-shaped existence check I can and did make by `Glob`) |
| `git log` / `git show` / `git ls-tree` | not given, and I hold no `Bash` to run them | substituted with `Glob`/`Grep` listings for every existence check below — the one substitution `references/mechanical-inputs.md` explicitly permits without a shell |

Quoted `agents.py` output, verbatim, as handed to me:

```
agents 8 · skills 21 · roster ~1463/15000 tokens (9%)

  WARN  .claude/agents/agent-fitness-review.md: has eval material (docs/agent-spec-agent-fitness-review.md, docs/agent-fitness-review-tester-brief.md) but no recorded RESULT. A suite nobody ran is a plan [M]


  where each rule comes from:
    [A] Anthropic, The Complete Guide to Building Skills for Claude
    [B] code.claude.com/docs/en/sub-agents
    [C] code.claude.com/docs/en/skills
    [M] measured in this project — a house rule, not a documented limit
        (/home/user/skills-repo/knowledge/notes/)

CLEAN, 1 warnings
```

No mandatory L5 row was blocked by a missing mechanical input, so the pass was not
stopped.

---

## Step 3 — Units

**Unit = a promised item: a file, section, quoted source, mechanical check, or recorded
event that `agent-builder.md` or one of its three preloaded skills asserts exists —
plus, separately, every `references/`/`assets/` file under those three skills (reverse
sweep: does some step open it), and every numbered step in those three skills (reverse
sweep: does it end in an explicit artefact).** A mention inside a "why this exists"
citation box is not itself a unit; an assertion that a specific file, section or event
exists is.

**Count, auditable set: 15 promised-item units, plus a reverse `references/`/`assets/`
sweep of 7 files across the three skills, plus a steps-with-no-artefact sweep of 22
numbered steps across the three skills.**

**Count, abstained set (from `docs/zz-fixture-c4-promises.md`, self-authored, step 0):
12 distinct promise-claims**, listed but not scored.

---

## Step 4 — Findings table (auditable set)

| # | Unit | Promised at | Exists / holds? | Listing that proves it |
|---|---|---|---|---|
| 1 | `agent-shape/SKILL.md` | `agent-builder.md:7` (`skills:`) | yes | `Glob .claude/skills/agent-shape/**` → `SKILL.md`, `references/knowledge-map.md` |
| 2 | `agent-baseline/SKILL.md` | `agent-builder.md:8` (`skills:`) | yes | `Glob .claude/skills/agent-baseline/**` → `SKILL.md` only, no `references/`/`assets/` |
| 3 | `agent-assembly/SKILL.md` | `agent-builder.md:9` (`skills:`) | yes | `Glob .claude/skills/agent-assembly/**` → 9 files (below) |
| 4 | `agent-shape/references/knowledge-map.md` | `agent-builder.md:112` ("Where your knowledge lives") | yes | same glob as #1 |
| 5 | `.claude/hooks/agent-builder-scope.sh` | `agent-builder.md:15` (`hooks:`) and body lines 53–83 | yes, and registered clean | `Glob .claude/hooks/agent-builder-scope.sh` → present; `agents.py` names no WARN/FAIL against `agent-builder.md` for hook existence/executability/matcher anchoring |
| 6 | `agent-baseline §2b` — "a named route for that case" (`Agent` absent) | `agent-builder.md:43–44` | yes | `agent-baseline/SKILL.md:48` → `### 2b · When you cannot dispatch at all`, three numbered routes, ending "**Artefact:** which route... you used" |
| 7 | `agent-assembly §6` — "a named route for that case" | `agent-builder.md:44` | **holds, but mislocated** | `agent-assembly/SKILL.md` §6 (lines 132–145) itself contains no such route; the route is in the unnumbered closing section "When this does not apply" (line 167–169): *"You cannot delegate the test. Then the work is not finished... say plainly that step 6 is unmet, and stop."* It explicitly ties back to step 6 by name, so the content the promise describes is present — but not *inside* §6 as the parallel with "agent-baseline §2b" (a true numbered subsection) implies |
| 8 | `antipatterns.md`, quoted: *"a boundary is only as narrow as the widest tool"* | `agent-builder.md:32` | yes | `Grep "widest tool" .claude/skills/agent-assembly/references/antipatterns.md` → line 17–18, exact match |
| 9 | `.claude/validate/agents.py` | `agent-builder.md:82` | yes | `Glob .claude/validate/*` → `agents.py` present; also the caller-handed raw output in step 2 |
| 10 | An eval artefact naming `agent-builder` (implied: "hands the result to a fresh subagent for testing"; body's "you never grade your own work") | `agent-builder.md:21–22, 94–96`; validator rule "every agent is named by some eval artefact" | yes | `Grep "agent-builder" .claude/skills/agent-assembly/evals.md` → title line 1, `"# evals — agent-builder"`; line 3–4 self-identifies its author as independent of the agent's author |
| 11 | Recorded event: "an auditor executed exactly that write on 2026-08-29 and the gate returned ALLOW" | `agent-builder.md:75–76` | yes, exact match | `Grep "auditor executed exactly that write"` → `docs/hook-proposal-agent-builder-scope.md:54`, verbatim, dated to the same P5 absence audit named at line 13 of that doc (2026-08-29) |
| 12 | "84 library talents" | `agent-builder.md:113` | yes | `Grep "84 talents"` → `agent-shape/references/knowledge-map.md:38` |
| 13 | A re-runnable control harness for `agent-builder-scope.sh` (implied by body's own house rule: "a hook whose controls were run once by hand cannot detect its own regression") | `agent-builder.md` does not itself name the harness by path; the rule it states is general | yes | `Glob .claude/validate/agent-builder-scope-controls.sh` → present; `agent-assembly/evals.md:219–227` records it re-run at "29 cases, 29 pass" |
| 14 | `agent-assembly/references/antipatterns.md` — reverse sweep, is it opened by a step? | tier-3 contract in `agent-assembly/SKILL.md:25` ("loads when a step opens it") | **no step opens it** | `agent-assembly/SKILL.md` line 9 opens only `references/tiers.md` and `references/delegation.md` by name; full-text read of the file found no other `references/` open instruction. Repo-wide `Grep "references/antipatterns"` → 0 hits anywhere. The file is quoted by `agent-builder.md` itself (unit 8) and by `evals.md` (an audit document, not a procedure step) — quoting is not opening |
| 15 | `agent-assembly/assets/evals.md` — reverse sweep, is it opened at the emit step? | tier-4 contract in `agent-assembly/SKILL.md:26` ("loads at the emit step") | **no step opens it** | Step 6 (`agent-assembly/SKILL.md:132–145`) names its own output artefact `evals.md` but never instructs "use `assets/evals.md`" the way step 2 says "Use `assets/agent.md`" (line 50) and step 3 says "Use `assets/skill.md`" (line 64). Repo-wide `Grep "assets/evals"` → the only hit is inside a `git ls-tree` transcript quoted in `evals.md:802`, not an open-instruction |

### Reverse sweep — the other 5 `references/`/`assets/` files (control set, for contrast)

| File | Opened by | Holds? |
|---|---|---|
| `agent-assembly/references/tiers.md` | `SKILL.md:9` | yes |
| `agent-assembly/references/delegation.md` | `SKILL.md:9` | yes |
| `agent-assembly/assets/agent.md` | `SKILL.md:50` ("Use `assets/agent.md`") | yes |
| `agent-assembly/assets/skill.md` | `SKILL.md:64` ("Use `assets/skill.md`") | yes |
| `agent-assembly/assets/hook-proposal.md` | `SKILL.md:78` ("using `assets/hook-proposal.md`") | yes |

**5 of 7 candidate `references/`/`assets/` files under the three preloaded skills are
opened by name; 2 of 7 (`antipatterns.md`, `assets/evals.md`) are not.**

### Steps-with-no-artefact sweep

| Skill | Numbered steps | Steps with an explicit `**Artefact:**` line | Steps without |
|---|---|---|---|
| `agent-shape` | 10 (0, 1, 1b, 2, 3, 4, 5, 6, 7, 8) | 9 | **§8 "Emit the spec"** — ends "Under `docs/`... Then hand to `agent-baseline`" with no `**Artefact:**` label, unlike every other step in the file |
| `agent-baseline` | 5 (1–5) | 5 | none |
| `agent-assembly` | 7 (1–7) | 6 | **§7 "Report what is true"** — ends "Say which failure classes the suite is blind to... and what you did not check", no `**Artefact:**` label |

**2 of 22 numbered steps across the three preloaded skills end without an explicit
artefact line.** Both are the terminal "report what is true" step of their respective
skill, and both describe a reporting obligation rather than naming a file or table the
report becomes.

---

## Step 5 — Disconfirming checks

| # | Finding under test | Disconfirming query | Result | Survives / killed |
|---|---|---|---|---|
| 7 | "agent-assembly §6" promise is mislocated | searched for a numbered `6b`/`6a` subsection the way `agent-baseline` has `2b`; also searched whether the "When this does not apply" section is itself sometimes referred to as part of §6 elsewhere in the repo | no `6b` exists; `evals.md:795` independently describes the same skill as *"`agent-assembly` §6 mandates an `evals.md`..."* treating §6 as the numbered step only, consistent with my reading, not the appendix | **survives, but downgraded** — this is a location-precision gap, not a missing artefact; content-wise the route exists and explicitly names "step 6" |
| 14 | `antipatterns.md` never opened by a step | searched all of `.claude/agents/` and `.claude/skills/` for any "open/read `references/antipatterns`" instruction, not just inside `agent-assembly` | 0 hits anywhere in the tree; the only appearances are quotes (`agent-builder.md:32`, three places in `evals.md`) | **survives** |
| 15 | `assets/evals.md` never opened by a step | re-read `agent-assembly/SKILL.md` step 6 in full for an indirect instruction (e.g. "use the template at..."); checked whether the fresh tester dispatched at step 6 is even told this template exists | step 6's only artefact-naming text is "`evals.md` with per-case verdicts, written by someone else" — filename matches the template's *output* name but never points the dispatched tester at the template's *path* | **survives** |
| step-sweep | 2 terminal steps lack `**Artefact:**` labels | checked whether this is a repo-wide closing convention rather than a defect specific to these two skills — read `agent-builder.md`'s own closing section, "## When you are done" | it is: `agent-builder.md`'s own closing section carries the identical unlabelled shape ("Report what is true rather than what is finished..."), and `agent-fitness-verdict`'s own step 3 uses near-identical language. This is a consistent authorial pattern across the repo's closing sections, not an isolated slip | **survives as a finding, but its severity is reduced** — it looks deliberate, but the lens's own rule ("every step... must end in an artefact... count them") does not carve out an exception for terminal steps, so it is still counted |
| 1–6, 8–13 | all named files/sections/quotes/events exist | re-ran each `Glob`/`Grep` against the exact string as written in the source document; for unit 11 additionally cross-checked the date (2026-08-29) against `evals.md`'s two dated rounds (both 2026-08-28) to rule out a mismatch before accepting the match in `docs/hook-proposal-agent-builder-scope.md` | all matched on the first listing; unit 11's date is carried correctly *only* in the `docs/hook-proposal-...md` source, not in `evals.md`, which is why the check for #11 pulled that file specifically rather than stopping at the first partial match | **all survive as "holds"** |

---

## Step 6 — Class of each surviving finding

| # | Finding | Class |
|---|---|---|
| 7 | `agent-assembly §6`'s named route lives in the closing "When this does not apply" section, not inside §6 itself | `content` — a one-line fix to either the citation (say "agent-assembly's closing section, keyed to step 6") or the skill (move/duplicate the route into a `6b`) closes it; no mechanism is implicated |
| 14 | `agent-assembly/references/antipatterns.md` exists on disk but no step in its owning skill opens it | `content` — either add an explicit "open `references/antipatterns.md`" instruction (most plausibly at step 4, where the wall is emitted) or the file's promise is unkept per the tier-3 contract `agent-assembly/SKILL.md` states for itself |
| 15 | `agent-assembly/assets/evals.md` exists as a template but step 6 never points the dispatched tester at it | `content` — step 6 could say "hand the tester `assets/evals.md`" the way steps 2 and 3 name their templates; as written, the template's existence is not load-bearing on any actual run |
| step-sweep | `agent-shape §8` and `agent-assembly §7` end without an `**Artefact:**` line | `content` — each could gain the same label every other step in its file carries; this is documentation-completeness, not a missing mechanism, and the pattern recurring across `agent-builder.md`'s own closing section suggests it is a repo-wide convention that was never reconciled with this lens's own rule rather than three independent oversights |

One line of referral, outside this lens, not investigated further: `agent-assembly/evals.md` itself records, in its own "ROUND TWO" section, a HIGH-severity containment defect (the hook allows a *new* agent that omits `tools:` while denying a compliant one) that is still open as of the file's own last-recorded state. That is an **L3 · Wall versus body** finding — whether the mechanism the body claims actually holds — not a promise-coverage one, and is not scored here.

---

## Verdict (`agent-fitness-verdict`)

### 1 · The bar, stated before scoring

Mandatory rows under L5 for this agent:

- **M1 — Every preloaded skill named in `skills:` exists as a file.** Pass condition:
  `Glob` returns `SKILL.md` for each. (Units 1–3.)
- **M2 — Every reference the body cites by name (path, quote, or named section) exists
  and says what it is cited for.** Pass condition: `Glob`/`Grep` finds the file or
  section at the location claimed, or an explicit downgrade is recorded if the location
  is imprecise. (Units 4, 6–9, 11–12.)
- **M3 — Every mechanism the body names by path exists and registers clean.** Pass
  condition: `Glob` finds the file and `agents.py`'s raw output names no WARN/FAIL
  against `agent-builder.md` for it. (Unit 5.)
- **M4 — An eval artefact names `agent-builder`, authored independently of it.** Pass
  condition: the file exists and self-identifies its author as not the agent's author.
  (Unit 10.)
- **M5 — Zero `references/`/`assets/` files load-orphaned across the three preloaded
  skills; zero numbered steps end without an artefact.** Pass condition: both sweeps
  return 0.

### 2 · Verdict

**`unfit`** — under L5 · Promise coverage only, against M5 specifically. M1–M4 were all
reached and all passed cleanly (12 of 13 scored units under M1–M4 hold exactly as
claimed; unit 7 holds in content but is mislocated, a `content`-class gap, not a false
promise). **M5 failed as stated**: the reverse sweep found 2 of 7 `references/`/`assets/`
files under `agent-assembly` that no step opens (`references/antipatterns.md`,
`assets/evals.md`), and the artefact sweep found 2 of 22 numbered steps across the three
preloaded skills (`agent-shape §8`, `agent-assembly §7`) that end without the explicit
artefact line every other step in those files carries. Both are exactly the shape L5
exists to catch — a file or a step whose promise ("this loads when opened" / "this ends
in an artefact") the skill states as a general contract for itself and does not keep for
every instance.

None of the four surviving findings is severe on its own — three are `content`-class
labelling/location gaps closable in one line each, and the disconfirming check on the
step-sweep found the pattern is a repo-wide closing convention, not three independent
lapses. But M5 was written as a strict "zero" bar precisely because this lens's own
motivating incidents (`lenses.md` L5 section) were exactly this size before they were
found — a preloaded skill that did not exist, two reference files sitting unopened, an
eval file claimed by name but absent from `git ls-tree`. A bar with a "the count must be
zero" pass condition that is not met is `unfit` under this lens, not `cannot-say`: the
evidence needed to score M5 was fully available and was scored.

This says nothing about the four lenses not run: L1 · Grounding, L2 · Currency, L3 ·
Wall versus body, L4 · Reachability and collision. A `content`-only fitness gap under
one lens is not evidence about whether the agent's directives are grounded (L1), current
(L2), whether its stated impossibilities hold under attack (L3, and the referral above
suggests they may not — that is not scored here), or whether it collides with a sibling
agent (L4).

### 3 · Evidence accounting

| Class | Count | Rows |
|---|---|---|
| `executed` | 0 | this pass holds no shell; the one command result I have (`agents.py`) was handed to me, not run by me |
| `listed` | 20 | units 1–6, 8–15 and the 5-file reverse-sweep control set, and the 22-step artefact-line sweep — each a `Glob`/`Grep` whose exact query is written in the tables above |
| `read` | 2 | unit 7 (read `agent-assembly/SKILL.md` in full to confirm the route's actual location) and unit 11 (read `docs/hook-proposal-agent-builder-scope.md` and cross-read `evals.md`'s two dated rounds to resolve the date) |
| `on a word` | 1 | Step 0's authorship determination — the launching message's statement, plus the documents' own self-identification inside `evals.md`; no `git log`/`git blame` was available to re-derive it |

**22 of 23 auditable unit-level checks (units 1–15, the 5-file control set, and the
22-step sweep, counted as listed-or-read rows) were verified against the artefact tree by
a reproducible `Glob`/`Grep` rather than taken on a report's word; 1 (authorship) rests on
a word because no mechanism to re-derive it was available in this tool surface.** The 12
promise-claims in `docs/zz-fixture-c4-promises.md` are excluded from this count entirely
— per step 0 they are abstained, not scored as evidence for or against the agent.

### 4 · What this pass could not see

**Structural blind spots.**
- `Glob`/`Grep` existence checks cannot see whether a file that *does* exist still says
  what it is cited for beyond the specific string matched — I confirmed unit 8's quote
  matches `antipatterns.md:17–18` character-for-character, but I did not read that whole
  file's argument for whether `agent-builder.md`'s paraphrase around it is fair; that is
  L1 · Grounding, not L5.
- I cannot independently confirm `.claude/hooks/agent-builder-scope.sh` is executable by
  file mode — I took `agents.py`'s clean run as settled per the mechanical-inputs
  contract rather than re-deriving it, which is correct procedure but means my own
  observation count on that specific bit is zero.
- I cannot verify authorship of any reviewed document by a mechanism (no `git blame`);
  step 0's provenance table, including my own abstention, rests on the launching message
  and internal self-identification, both "on a word."
- A path-shaped sweep cannot see whether the fresh tester who wrote `agent-assembly/evals.md`
  ever actually knew `assets/evals.md` existed, or independently reinvented the same
  filename — the finding at unit 15 shows the template is *unreachable by instruction*,
  not that it went unused; I cannot distinguish those from a listing.

**Not run, and why.**
- `bash .claude/validate/agent-builder-scope-controls.sh` — not requested and not needed
  for any L5 mandatory row; its 29-case pass/fail result speaks to whether the hook
  *holds under attack*, which is L3's question. Naming that the harness exists (unit 13)
  is as far as L5 goes.
- The full raw transcript of `bash .claude/validate/selftest.sh` — only its last line
  was handed to me. Would settle whether any of the 24 positive controls specifically
  exercise `agent-builder-scope.sh` versus the roster generally.
- Reading `agent-assembly/evals.md` end to end for its HIGH-severity containment defects
  (referred to but not scored above) — that dispatch belongs to an L3 pass.
- Dispatching a fresh tester against `agent-assembly`'s own eval material to see whether
  the two unopened reference/asset files (units 14–15) ever mattered to a real run — this
  pass cannot dispatch (`Agent` absent) and would not do so under L5 in any case.

**Not checked at all.**
- L1 · Grounding, L2 · Currency, L3 · Wall versus body, L4 · Reachability and collision —
  the four lenses this pass did not run, per the one-lens rule.
- Whether the 12 promise-claims inside `docs/zz-fixture-c4-promises.md` are themselves
  accurate — abstained per step 0, not merely deferred.
- Whether the statistics `agent-builder.md` cites in its "Standing constraints" section
  (1–3 modules ≈ +19.0pp, 162 personas, 22–40% agreement) still match their current
  homes in `/home/user/skills-repo/knowledge/notes/` — that is L2 · Currency, and this
  pass only confirmed the "84 talents" figure (unit 12) because it was itself a
  promise-of-existence (a number of files), not a promise-of-value.

### 5 · What the reader must do next

1. Apply the two `content`-class fixes at units 14–15: either point `agent-assembly`'s
   procedure at `references/antipatterns.md` and `assets/evals.md` explicitly, or
   accept that they are effectively dead weight under the skill's own stated loading
   contract.
2. Apply the two `content`-class fixes at the step-sweep (`agent-shape §8`,
   `agent-assembly §7`): add the `**Artefact:**` line every sibling step carries, or
   record deliberately that terminal "report" steps are exempt from L5's own rule — as
   written, the exemption is only inferable by cross-reading `agent-builder.md`'s closing
   section, not stated anywhere.
3. Correct or relocate the `agent-assembly §6` citation at `agent-builder.md:44` (unit 7)
   so it points at the section that actually carries the route.
4. Dispatch fresh instances on L1, L2, L3 and L4 in parallel — this document is one
   lens and an `unfit` verdict on it is not a fitness determination on the whole agent.
   The L3 referral above (an open HIGH-severity containment defect recorded in
   `agent-assembly/evals.md`'s own "ROUND TWO" section) is the single highest-value next
   dispatch.
5. Run `bash .claude/validate/selftest.sh` in full and hand over the raw transcript if a
   future pass needs to confirm control coverage of `agent-builder-scope.sh` specifically.
