# Review — `agent-fitness-review` — L5 · Promise coverage

Reviewer: a fresh dispatch of `agent-fitness-review` itself, holding `Read, Grep, Glob,
Write, WebFetch` only (no `Edit`, no `Bash`, no `Agent`, no `WebSearch`). Target: the
agent at `.claude/agents/agent-fitness-review.md`, its two preloaded skills, its spec,
its tester brief, its hook proposal, and its declared cross-references.

this pass is one lens and is not coverage; lenses not run: L1 · Grounding, L2 ·
Currency, L3 · Wall versus body, L4 · Reachability and collision.

---

## Step 0 — Provenance

| Artefact | Author | Auditable? |
|---|---|---|
| `.claude/agents/agent-fitness-review.md` | a prior session, per the launching message | auditable |
| `.claude/skills/agent-review-pass/SKILL.md` + `references/*` | a prior session (built alongside the agent) | auditable |
| `.claude/skills/agent-fitness-verdict/SKILL.md` | a prior session | auditable |
| `docs/agent-spec-agent-fitness-review.md` | self-identifies as "the session that built the agent" (line 3, §1) | auditable |
| `docs/agent-fitness-review-tester-brief.md` | self-identifies as "Written by the session that built the agent" (line 7) | auditable |
| `docs/hook-proposal-agent-review-readonly-bash.md` | not self-identified; treated as prior-session output, consistent with the spec's manifest (§11) | auditable |

**Caveat on this row's own evidence:** I hold no `Bash`, so I cannot run `git log` /
`git blame` to independently confirm authorship — I have only the launching message's
statement and the documents' own self-identification, which is `on a word`, not
`executed`. Nothing here reads as content I could have produced in this dispatch (I
arrived with no memory of these documents and no route to have written under
`.claude/`). **Step 0 did not fire** — no row is marked `abstained` — but the
authorship determination itself rests on a word, not a command, and that limit is
carried into the accounting below rather than hidden.

---

## Step 1 — Lens

**L5 · Promise coverage**, as directed by the dispatch. Procedure: enumerate every list
the agent and its documents promise (artefacts a step emits, files a placement table
assigns, references a skill opens, the eval suite, controls claimed run, specs, hook
proposals), check each **as a listing**, then sweep the reverse direction — `references/`
and `assets/` files nothing opens.

---

## Step 2 — Mechanical inputs

| Command | Given? | What I did with it |
|---|---|---|
| `python3 .claude/validate/agents.py` | **yes, raw output quoted below** | took its `WARN` and its `CLEAN, 1 warnings` verdict as settled; did not re-derive any of the construction-rule checks it already runs (existence of referenced `references/`/`assets/` files, hook command existence+executability, preload existence) |
| `bash .claude/validate/selftest.sh` | **partial** — only the last line, `positive controls: pass=24 fail=0`, not the full raw transcript the spec's tester brief asks for ("Paste the raw output") | used only to note the checker can fail at all (self-test not vacuous); did not need the full transcript for any L5 mandatory row, so the pass was **not** stopped for it, but the gap is recorded here rather than smoothed over |
| `bash .claude/validate/*-controls.sh` | not given | not required by L5 (belongs to L3 · Wall versus body); not requested |
| `git log` / `git show` / `git ls-tree` | not given, and I hold no `Bash` to run them | substituted with `Glob`/`Grep` listings for every existence check below — this is the one thing `references/mechanical-inputs.md` explicitly permits without a shell: "record, as a finding, that a claimed check has no call site... visible by listing" |

Quoted `agents.py` output, verbatim, as handed to me:

```
agents 8 · skills 21 · roster ~1463/15000 tokens (9%)

  WARN  .claude/agents/agent-fitness-review.md: has eval material (docs/agent-spec-agent-fitness-review.md, docs/agent-fitness-review-tester-brief.md) but no recorded RESULT. A suite nobody ran is a plan [M]

CLEAN, 1 warnings
```

No mandatory L5 row was blocked by a missing mechanical input, so the pass was not
stopped.

---

## Step 3 — Units

**Unit = a promised item: a file, reference, sibling agent/skill, or artefact that some
document belonging to `agent-fitness-review` asserts exists (by path, by cross-reference,
or by naming it as already produced).** A mention is not a promise; only an assertion
that the thing exists or will be opened counts.

Enumerated by reading the agent file, both preloaded skills and their `references/`, the
spec, the tester brief, and the hook proposal, then confirming each named path with
`Glob`.

**Count: 17 promised-item units, plus two structural sweeps** (orphaned
`references/`/`assets/` files; procedure steps ending with no artefact).

---

## Step 4 — Findings table

| # | Unit | Promised at | Exists? | Listing that proves it |
|---|---|---|---|---|
| 1 | `agent-review-pass/SKILL.md` | `agent-fitness-review.md:7` (`skills:`) | yes | `Glob .claude/skills/agent-review-pass/**` → `SKILL.md` present |
| 2 | `agent-fitness-verdict/SKILL.md` | `agent-fitness-review.md:8` (`skills:`) | yes | `Glob .claude/skills/agent-fitness-verdict/**` → `SKILL.md` present |
| 3 | `agent-review-pass/references/lenses.md` | opened at agent-review-pass step 1 | yes | same glob; also opened directly, read in full |
| 4 | `agent-review-pass/references/mechanical-inputs.md` | opened at agent-review-pass step 2 | yes | same glob; opened directly, read in full |
| 5 | `.claude/hooks/docs-only-write.sh` | `agent-fitness-review.md:14` (hooks) and body line 38 | yes, and registered clean | `Glob .claude/hooks/docs-only-write.sh` → present; `agents.py` names no `FAIL` for it (existence + executable are among the rules that command owns, per `mechanical-inputs.md`, and it returned no `FAIL`) |
| 6 | `.claude/skills/agent-shape/references/knowledge-map.md` | body, "Where your knowledge lives" | yes | `Glob .claude/skills/agent-shape/references/knowledge-map.md` → present |
| 7 | `.claude/validate/agents.py` | body, "Where your knowledge lives" | yes | `Glob .claude/validate/*` → `agents.py` present |
| 8 | `.claude/agents/agent-builder.md` (routed-to) | body, "Scope" | yes | `Glob .claude/agents/*.md` → present |
| 9 | `.claude/agents/primary-source-verifier.md` (routed-to) | body, "Scope" | yes | same glob → present |
| 10 | `.claude/skills/design-claim-audit/SKILL.md` (routed-to) | body, "Scope" | yes | `Glob .claude/skills/design-claim-audit/**` → present |
| 11 | `.claude/agents/architect.md` (routed-to) | body, "Scope" | yes | same agents glob → present |
| 12 | `/home/user/skills-repo/.claude/skills/agent-surface-security-audit/` (routed-to) | body, "Scope" | yes | `Glob` on that path → `SKILL.md`, `evals.md` present |
| 13 | `docs/agent-spec-agent-fitness-review.md` | named by the `agents.py` `WARN` and by the tester brief line 35 | yes | `Glob docs/agent-spec-agent-fitness-review.md` → present; read in full |
| 14 | `docs/agent-fitness-review-tester-brief.md` | named by the `agents.py` `WARN` and by spec §11 row 7 | yes | `Glob docs/agent-fitness-review-tester-brief.md` → present; read in full |
| 15 | `docs/hook-proposal-agent-review-readonly-bash.md` | spec §7, §9, §11 row 6; tester brief line 41 | yes | `Glob docs/hook-proposal-agent-review-readonly-bash.md` → present; opened |
| 16 | `docs/decomposition-agent-pipeline.md` (cited as the source of the "component manifest" idea, spec §11 preamble, `:104`) | spec §11 | yes | `Glob docs/decomposition-agent-pipeline.md` → present (content of the cited line not re-verified — that is L1 · Grounding's job, not L5's) |
| 17 | **A recorded eval RESULT** — the execution of the tester brief against the spec, promised implicitly by `CLAUDE.md`'s "every agent ships with evals" and named explicitly by `agents.py`'s own rule ("eval material... but no recorded RESULT") | `CLAUDE.md` (project rule) + `agents.py` `WARN` (`[M]`) | **no** | `Glob docs/agent-review-*.md` → **no files found**; repo-wide `Grep` for `agent-fitness-review` → only the 6 files already listed above (spec, brief, hook-proposal, agent file, CHANGELOG, and an unrelated routing proposal), none of which is a results/verdict document |

### Reverse sweep — references/assets nothing opens

| Skill | `references/`/`assets/` files | Opened by a step? |
|---|---|---|
| `agent-review-pass` | `lenses.md`, `mechanical-inputs.md` | both — step 1 opens `lenses.md`, step 2 opens `mechanical-inputs.md` |
| `agent-fitness-verdict` | none (`Glob` returned only `SKILL.md`) | n/a |

**0 orphaned reference files** out of 2 candidates.

### Steps with no artefact

Every step in `agent-review-pass` (0–7, 8 steps) and every step in
`agent-fitness-verdict` (1–5, 5 steps) ends in an explicit **Artefact:** line, confirmed
by reading both skill bodies in full.

**0 of 13 steps** end in a consideration with nothing behind it.

---

## Step 5 — Disconfirming checks

| # | Finding under test | Disconfirming query | Result | Survives / killed |
|---|---|---|---|---|
| 17 | No recorded eval RESULT exists anywhere for this agent | (a) `Glob docs/agent-review-*.md` — the exact filename pattern the spec's own §2 artefact line and `agent-fitness-verdict` step 5 specify (`docs/agent-review-<agent>-<lens>.md`); (b) repo-wide `Grep "agent-fitness-review"` for any alternate-named result; (c) `Grep "cannot-say|verdict.*fit"` across `docs/`, which surfaced one unrelated hit (`docs/research/verdicts/x4-dead.md`, a `primary-source-verifier` verdict on a different draft, opened and confirmed unrelated); (d) `Grep "agent-fitness-review"` in `docs/BACKLOG.md` — no match | (a) 0 files; (b) 6 files, all already accounted for and none a result; (c) the one hit is a different agent's verdict on a different artefact; (d) no backlog entry recording a run | **survives** — the gap is real, not a naming-convention miss |
| 1–16 | All named files/paths exist | re-ran each `Glob` with the exact path as written in the source document (no alternate spelling needed — every path matched on the first listing) | all matched | **all survive as "holds"** (i.e., the promise is kept, not broken) — recorded per L5's instruction that a zero-finding row is itself a finding |

---

## Step 6 — Class of each surviving finding

| # | Finding | Class |
|---|---|---|
| 17 | No recorded eval RESULT for `agent-fitness-review` exists in the tree | **`elsewhere`** — this is not a defect in any file under review; it is an action nobody has taken yet. The spec (§12, "Owed," item 2) and the tester brief (line 3, "Step 6 is UNMET") both already name it, correctly, and in advance of this review. The remedy is the orchestrating session dispatching a tester per `docs/agent-fitness-review-tester-brief.md` — not a change to any artefact this pass reviewed. |
| 1–16 | Every other promised item exists | no class — these are `holds`, not surviving problems |

One line of referral, outside this lens, not investigated further: `docs/proposal-route-into-agent-fitness-review.md` exists and is unreferenced by `agent-fitness-review.md` or either of its preloaded skills — it proposes edits to `agent-builder.md`'s description and `agent-assembly`'s step 6 so that this agent becomes reachable. Whether those edits have landed is an **L4 · Reachability** question, not a promise-coverage one, and is not scored here.

---

## Verdict (`agent-fitness-verdict`)

### 1 · The bar, stated before scoring

Mandatory rows under L5 for this agent:

- **M1 — Every preloaded skill and every reference a step opens exists as a file.**
  Pass condition: `Glob` returns the file for each path named in `tools:`/`skills:`
  frontmatter and in every "opened at step N" reference. (Units 1–4.)
- **M2 — Every mechanism the body names by path (hook) exists and is registered clean
  by the validator.** Pass condition: `Glob` finds the file and `agents.py`'s raw output
  names no `FAIL` against it. (Unit 5.)
- **M3 — Every sibling this agent's Scope section routes to exists as a real
  file/skill.** Pass condition: `Glob` finds each. (Units 8–12.)
- **M4 — The eval material the validator names as present is actually present.**
  Pass condition: both files in the `WARN` line exist. (Units 13–14.)
- **M5 — Zero `references/`/`assets/` files load-orphaned; zero procedure steps end
  without an artefact.** Pass condition: the reverse sweep and step-artefact audit both
  return 0.

M1–M5 were all reached and all passed. Finding #17 (no recorded eval RESULT) is real and
recorded, but it does not fail any M-row as stated: no document under review claims that
a result file exists at a specific path (the classic false-claim shape this lens
targets), and the validator itself treats the condition as a `WARN`/`[M]` house-rule
signal, not a construction failure. The gap is honestly disclosed in three independent
places (the validator, the spec, the tester brief) rather than concealed — which is the
behaviour this lens's own motivating incident (a claimed file that `git ls-tree` showed
never existed) was written to catch the *absence* of.

### 2 · Verdict

**`fit`** — under L5 · Promise coverage only. Every mandatory row was reached and passed;
16 of 17 enumerated promised items hold exactly as claimed, and the one gap (#17) is a
disclosed pending action, not a false promise. This says nothing about the four lenses
not run: L1 · Grounding, L2 · Currency, L3 · Wall versus body, L4 · Reachability and
collision.

### 3 · Evidence accounting

| Class | Count | Rows |
|---|---|---|
| `executed` | 0 | this pass holds no shell; the one command result I have (`agents.py`) was handed to me, not run by me |
| `listed` | 15 | units 1–14, 16 (each a `Glob`/`Grep` whose query is written in the table) |
| `read` | 1 | unit 17's disconfirming check, read against the artefact tree via `Glob`/`Grep` plus opening `docs/research/verdicts/x4-dead.md` to rule it out |
| `on a word` | 1 | Step 0's authorship determination (launching message + documents' self-identification; no `git log` available to re-derive it) |

**16 of 17 unit rows, plus both structural sweeps, were verified against the artefact
tree by a reproducible listing rather than taken on a report's word; 1 of 17 (authorship,
step 0) rests on a word because no mechanism to re-derive it was available in this
tool surface.**

### 4 · What this pass could not see

**Structural blind spots.**
- Path-existence checks (`Glob`) cannot see whether an existing file's *content* still
  matches what another document claims about it — that is L1 · Grounding, not L5. A file
  can exist and be stale, wrong, or contradict its own citation, and this pass would
  record it as "holds."
- I cannot confirm `.claude/hooks/docs-only-write.sh` is actually executable (file mode)
  independently — I took `agents.py`'s clean run as settled per the mechanical-inputs
  contract, rather than re-deriving it, which is correct procedure but means my own
  observation count on that specific bit is zero.
- I cannot verify authorship of the reviewed documents by any mechanism (no `git blame`);
  Step 0's provenance table rests on the launching message and the documents'
  self-identification, both of which are "on a word."

**Not run, and why.**
- `bash .claude/validate/*-controls.sh` for `docs-only-write.sh` — not requested and not
  needed for any L5 mandatory row; no such harness appears to exist for this hook at all
  (`.claude/validate/*-controls.sh` lists five files, covering `architect-rebuild`,
  `research-hooks`, `agent-builder-scope`, `rebuild-prospector-diet`,
  `rebuild-adjudicator-gate` — none named for `docs-only-write` or for the proposed
  `agent-review-readonly-bash`). That absence is itself an L3 finding, not scored here;
  naming it is the one-line referral this lens permits.
- The full raw transcript of `bash .claude/validate/selftest.sh` — only its last line was
  handed to me. Would settle: whether the 24 positive controls it counts include any for
  `agent-fitness-review`'s own hook specifically, versus the roster generally.
- All 25 cases in `docs/agent-fitness-review-tester-brief.md` (X1, X2, C1–C7, N1–N4,
  T1–T6) — every one requires either dispatching `agent-fitness-review` under test
  conditions or a live payload against `docs-only-write.sh`. This pass holds no `Agent`
  and no `Bash`; these are exactly the "not run" rows the spec and brief already
  predicted and named. Routes up: the orchestrating session must dispatch a tester per
  the brief.

**Not checked at all.**
- L1 · Grounding, L2 · Currency, L3 · Wall versus body, L4 · Reachability and collision —
  the four lenses this pass did not run, per the one-lens rule.
- Whether `docs/proposal-route-into-agent-fitness-review.md`'s three proposed edits have
  been applied (an L4 question, noted above as a referral only).
- Whether the figures and citations inside `lenses.md`'s "why this lens exists" boxes
  (line numbers into `docs/audit-agent-builder-loop-p4.md`, `p5.md`,
  `docs/domain-research-test-results.md`, `docs/review-agent-builder-loop.md`,
  `.claude/skills/agent-assembly/evals.md`) actually say what they're cited for — I
  confirmed those files **exist** (a promise-coverage check) but did not open them to
  confirm the cited passages support the claims, which is L1's job, not L5's.

### 5 · What the reader must do next

1. Dispatch a tester against `docs/agent-fitness-review-tester-brief.md` — X1, X2, C1–C3
   are the mandatory cases per the brief's own bar, and none has been run by anyone who
   did not build this agent. This is the single highest-value next step; it is also
   exactly the gap unit #17 names.
2. Run `bash .claude/validate/selftest.sh` in full and hand over the raw transcript
   (not just the last line) if a future L3 or L5 pass needs to confirm control coverage
   of `docs-only-write.sh` specifically.
3. Dispatch fresh `agent-fitness-review` instances on L1, L2, L3 and L4 in parallel for
   coverage — this document is one lens, not a fitness determination on the whole agent.
4. Decide, as a human, whether `docs/proposal-route-into-agent-fitness-review.md`'s three
   edits should land — flagged here only as a referral, not scored.
