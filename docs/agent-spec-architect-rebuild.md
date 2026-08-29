# Spec — `architect-rebuild`

**Status:** Proposed. Built 2026-08-29 by `agent-builder` under a blind-rebuild mandate.
**Blindness:** the requester forbade reading `.claude/agents/architect.md`,
`.claude/skills/architecture-decision/`, `.claude/skills/architecture-review/`,
`.claude/skills/system-decomposition/` and `docs/decisions/0021-the-architect-agent.md`.
None was opened, grepped, globbed or listed. Two further files were declined by the
builder as derived from the forbidden set — see §9.

---

## 0 · Nothing already owns this — where I looked, and what I found

| Search | Result |
|---|---|
| `grep '^name: .*(architect\|decomposition\|adr\|design\|trade\|boundary\|system\|seam)' /home/user/skills-repo/.claude/skills/**/SKILL.md -i` | 6 hits: `interface-depth-design`, `agent-architecture-audit`, `systematic-debugging`, `idempotent-action-design`, `loop-design-check`, `abstention-threshold-design` |
| Read of `agent-shape/references/knowledge-map.md` §The library | the 7 agent-building talents listed there |
| `docs/ROADMAP.md:26-35` | names **ADR-0021** as building an architect — "one subagent, three procedures, no persona, and no ability to write source code… unvalidated until B125 runs its eighteen evals" |

**Verdict: author, and reuse is knowingly declined by the requester, not by me.**

- Nothing in the 84-talent library owns *deciding the shape of a software system*.
  `agent-architecture-audit` audits **agents**, not systems. `interface-depth-design`
  owns one module's interface, not a system's seams. Closest neighbours; neither
  fires on "choose a tenancy model for Scio."
- **An architect agent does already exist in this repo.** I know this from
  `ROADMAP.md:32-35` and from the brief. The normal verdict would be *reuse or
  extend, stop here*. The requester has overridden it: this is a deliberate blind
  parallel build so that an independent third party can compare the two. That
  override is recorded here because it is the one place this spec departs from the
  reuse-first gate.
- **I cannot claim mine is better, or different, or non-overlapping.** I have not
  seen the incumbent. Any comparison is the requester's to make.

---

## 1 · The job, in one sentence and one artefact

> **It decides a shape question about Scio and defends the decision against the
> repository's own record, or refuses the question and says what would settle it.**

Three artefacts, one per function:

| Function | Emits |
|---|---|
| `design-decision-record` | an ADR file at `docs/decisions/NNNN-*.md`, `Status: Proposed`, with an options table carrying one rejection reason per option, a reversibility class, and the decisions it stands on |
| `seam-placement` | a seam table — one row per boundary, the change-likely decision it hides, the artefacts crossing it, and the current violations at `file:line` |
| `design-claim-audit` | a findings list — one row per claim, the document asserting it, the artefact checked, a verdict in {holds, refuted, not checkable here, abstained}, and evidence at `file:line` |

If a function cannot name its artefact, it is not a function. All three can.

---

## 2 · The context diet

**All three functions are evaluators. All three are saturated.** Each judges an
existing system against its own written record; each needs the 20 ADRs, the seven
as-built layer documents, the 12,054-edge graph, and the source.

`llm-idea-generation.md` is unambiguous that this is the correct diet for judging:
novelty scored **6.14/10 without retrieval and 2.38/10 with it** — a judgement made
without the existing reality in front of it is inflated ~2.6×.

**Must see**

- `docs/decisions/` — all 20 ADRs, statuses read verbatim, not paraphrased
- `/home/user/scio/docs/as-built/` — `00-INDEX.md`, `01-DECISIONS.md`, `LAYER-*.md`,
  `ARCHITECTURE-AS-BUILT.md`, `REVIEWS-FINDINGS-VERIFIED.md`, `REVIEWS-WHAT-WE-MISSED.md`
- `/home/user/scio/docs/as-built/graph/graph.json` — 5,173 nodes, 12,054 edges
- the source it makes a claim about, at `file:line`
- `docs/PRD.md`, `docs/STRATEGY.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`
- `/home/user/skills-repo/knowledge/notes/architecture-evidence.md` — for what is
  MEASURED versus REPEATED about architecture

**Must not see**

- nothing, for these three functions. There is no starved function in this roster.

**The starved function that this roster does not contain, and why.** "Generate the
option set for a datastore decision" is a *generator*, and generators must be
starved: seeding with existing good ideas measured **worse than nothing** (cosine
0.403–0.428 vs base 0.377), and models given the background produce output experts
call *"narrow and too tied to the background"* (narrowness 1.00–1.55 vs human 0.47).
Rule 1 of the split test therefore fires and demands a **second agent**. I have not
built it — see §3 and §8. Consequence to accept: `design-decision-record` as built
will restate the option space the repository already contains. It records the
trade-off honestly; it does not widen it.

---

## 3 · Split test — the roster

| # | Agent | Built? | Which rule decided it |
|---|---|---|---|
| A1 | `architect-rebuild` | **yes** | rules 1–3 all pass for one agent: identical saturated diet, same quarry (this repository's record), exactly three functions |
| A2 | an option-generator, unnamed | **no** | **rule 1 fires** — opposite diet (starved). Two contexts cannot be starved and saturated at once |
| A3 | the tester | **no — by design** | **rule 4** — the author never grades its own work. Brief at `docs/architect-rebuild-tester-brief.md` |

**A2 is not built because no baseline row demands it.** Every observed failure in §5
is a coverage, calibration or provenance failure; not one is "the options considered
were too narrow." Building A2 would be writing my opinion into a procedure where it
would later read as evidence. It goes to open questions (§8).

**Rule 4 and the joint I am least happy with.** A1 both authors ADRs
(`design-decision-record`) and audits claims (`design-claim-audit`). If it audits its
own ADR, that is self-critique with no external signal — measured worse for every
model on every benchmark (GPT-3.5 CommonSenseQA 75.8 → **38.1**). The mitigation is a
provenance step inside `design-claim-audit` that ends in an **abstain** row. **That is
a procedure, not a wall.** I could not find a hook predicate that distinguishes
"an artefact this agent wrote" from any other file. This is the weakest boundary in
the design and the containment evals must attack it.

---

## 4 · The functions

Each is a procedure ending in a checkable artefact, and each is bound to specific
rows of §5. **A rule with no row behind it is not in the skill.**

| Function | Procedure ends in | Rows it addresses |
|---|---|---|
| `design-decision-record` | an ADR at `docs/decisions/NNNN-*.md` | B8, B9, B10 |
| `seam-placement` | a seam table with violations at `file:line` | B3, B6 |
| `design-claim-audit` | a findings list with a four-value verdict per row | B1, B2, B4, B5, B7, B11, B12 |

`seam-placement` rests on the fewest rows (2) and is the entry most at risk of being
the one that adds noise. It is written narrowly to those two rows and explicitly does
**not** re-invent the layer-document format, which §6 records as already working.

---

## 5 · The baseline — recorded failures, not synthesised ones

**Provenance, stated plainly.** `agent-baseline` normally requires ≥2 dispatched runs.
**The `Agent` tool is disabled in this session** (exact refusal in §9), so zero fresh
runs were dispatched. Instead this uses the clause the procedure provides: *"The
failures are already recorded from a real run… Use it and say where it came from."*

The record used is unusually good for this purpose, and it is not a substitute I am
making excuses for:

- **Two independent runs of the review task already happened.** Two reviewers
  (Claude and GPT) reviewed this system with no shared guidance, in August 2026,
  producing 35 findings across two documents.
- **A third, independent pass verified them against code** on 2026-08-26 at commit
  `bd4f6d7` — `/home/user/scio/docs/as-built/REVIEWS-FINDINGS-VERIFIED.md`.
- **A fourth pass checked what the decomposition missed** —
  `/home/user/scio/docs/as-built/REVIEWS-WHAT-WE-MISSED.md`.
- **A fifth: a blind test with a fresh agent** against the as-built index —
  `/home/user/scio/docs/as-built/README.md:62`.

Nobody constructed these to make an agent look necessary. That is the property a
synthetic baseline cannot buy.

**What this baseline cannot do that dispatched runs could:** I cannot re-run to
separate a systematic failure from a bad draw on rows where only one document is the
source. Those are marked `draw`.

### The failure table

| # | What they did — quoted | Source | Consequence | Both runs? | Verdict |
|---|---|---|---|---|---|
| **B1** | *"the most serious finding in the set was found by only one of the two reviewers"* — GPT F-03, cross-tenant idempotency replay, absent from Claude's review; six findings are GPT's alone | `REVIEWS-FINDINGS-VERIFIED.md:83-89,156-158` | `run()` replays before `this.project()` and `BuildVersion` has no `workspace_id` column — a cross-tenant read ships. A single-review process misses it | this **is** the two-run comparison | **teach** |
| **B2** | both flagged `httpx2`/`httpcore2` as suspicious packages. *"False positive. Both are genuine, published under `github.com/pydantic/httpx2` by Tom Christie, httpx's author"* | `REVIEWS-FINDINGS-VERIFIED.md:113` | remediation spent on nothing, and the half that **stands** — *"0 hashes across 52 pinned packages"* — inherits the discredit | **both** (C-F16 and G-F15) | **teach** |
| **B3** | *"14 was a count of mentions, not of throwing endpoints — corrected 2026-08-26"*. Real: 8 endpoints across **six** modules; *"Broader than either review reported"* | `REVIEWS-FINDINGS-VERIFIED.md:106` | the unbuilt surface understated by half its modules; a rebuild plan sized against three | **both** | **teach** |
| **B4** | *"`PRODUCTION_READINESS_DIFF.md` does not reconcile the two reviews. `RETHINK-BRIEF.md` describes it as reconciling them, and that was repeated here on trust. It contains **zero** F-number references"* | `REVIEWS-FINDINGS-VERIFIED.md:38-43` | *"The two reviews were therefore never paired."* A reconciliation the repo believed it had, it did not have | propagated across documents | **teach** |
| **B5** | *"everything about concurrency in this document is reasoned from code, not measured"* — written inside a document whose other findings are statically verified | consultant review, quoted `REVIEWS-FINDINGS-VERIFIED.md:26-27` | reasoned and verified findings read as equally solid; 8 of 35 findings are in fact not statically checkable | both root reviews are static-only | **teach + wall** |
| **B6** | *"Our `LAYER-F` and `JOURNEY-INVOLVED-PATH` both name Settings as the placeholder. `App.tsx` lists five"* — and the missed one, `/live` "Refine", *"is the one that matters"* | `REVIEWS-WHAT-WE-MISSED.md:12-40` | the conclusion *"the gap sits at the two ends"* was wrong. *"The whole post-reveal half is unbuilt, and one of the two involvement levels has nowhere to land"* | **both** layer documents | **teach** |
| **B7** | *"We ran each suite once, got green, and wrote it down as a verified baseline."* Refuted by B105, a flaky `design.test.tsx` | `REVIEWS-WHAT-WE-MISSED.md:127-139` | a stability claim in `00-INDEX.md` that one observation cannot support | single pass | **teach** |
| **B8** | ADR-0018 and 0019 `Proposed`, 0020 `Partly implemented`. *"Anything downstream of those is standing on an open question"* | `as-built/01-DECISIONS.md:30-35` | Phase 5's Versions/Settings/Notifications placeholders wait on 0018 with no decision to wait for; work proceeded anyway | systematic across the register | **teach** |
| **B9** | *"§9 and §10 are most of that unfinished artifact, written and apparently never promoted into the PRD"*; and *"`DIFF` §1 states the intended core loop in twelve numbered steps… nothing here had recorded it"* | `REVIEWS-WHAT-WE-MISSED.md:121-126`; `REVIEWS-FINDINGS-VERIFIED.md:47-50` | B005 (MVP scope) tracked as open when most of it was already written down somewhere unregistered | **both** documents | **teach** |
| **B10** | intake vocabulary criticised on its own terms; *"the question is upstream of intake… is the wedge still founders and small teams?"* | `as-built/01-DECISIONS.md:57-78` | a component judged against an assumed audience instead of ADR-0001, the decision it implements. Redesigning intake would have been the wrong work | one document | **draw** (kept; same class as B4, not built on alone) |
| **B11** | *"5 · Blind test with a fresh agent — done — failed on two stale claims in `00-INDEX.md`, corrected"* | `as-built/README.md:62` | the authors' own index asserted two things that were false when written; only a reader who had not written it caught them | one | **teach** — and it is the evidence for rule 4 |
| **B12** | *"There are 35 findings, not 34. Earlier documents in this repo said 34. Miscounted."* | `REVIEWS-FINDINGS-VERIFIED.md:35-37` | a wrong count propagated through several documents unchallenged | propagated | **teach** (same mechanism as B3) |

### Sorted

- **teach** → B1, B2, B3, B4, B5, B6, B7, B8, B9, B11, B12
- **wall** → B5's execution half: an agent with no shell *cannot* claim a dynamic
  property was verified. Enforced by absence of `Bash` and absence of `Agent`.
- **wall** → not from a row but from the tool surface: `Write` can clobber. The ADR
  convention *"Supersede rather than edit"* (`as-built/01-DECISIONS.md:82`) becomes
  real only if overwriting an existing file is denied.
- **out of scope** → the six placeholder routes, ADR-0018's content, pricing (B063).
  Product decisions; route to the planning chat, not to this agent.
- **draw** → B10.

---

## 6 · What the baseline did well — leave it alone

This is the regression zone. SkillsBench measured skills lifting success 33.9% → 50.5%
overall **while ~15% of tasks regressed**, concentrated where the base was already
competent. Everything below is already competent here.

1. **The per-finding structure of both root reviews.** *"a priority table, then
   Evidens (with file and line pointers), Problem, Produktionskonsekvens, Realistiskt
   scenario, Grundorsak, Rekommenderad åtgärd, Verifiering, Beroenden"* — and the
   effect: *"That structure makes the pass mechanical rather than interpretive."*
   **Adopt it. Do not design a new finding template.**
2. **Refusing to guess.** *"Findings needing that are marked **not verifiable here**
   rather than guessed at."* Already the correct behaviour; the skill's job is to make
   it unavoidable, not to teach it.
3. **The seven layer-document headings**, including *State: solid · wrong-shaped ·
   missing · obsolete* and *Invariants — taken from the tests, with test names as
   evidence*. Already artefact-forcing. `seam-placement` must not replace this.
4. **Reading statuses verbatim.** *"Statuses below are verbatim, not paraphrased."*
5. **The ADR convention itself** — one decision per file, numbered, superseded not
   edited. Settled; the agent inherits it and does not restate it.
6. **Finding genuinely hard things.** F-03, the 501 surface, no IaC, the Clerk
   signature never cryptographically verified. Review as an activity works here.
   What fails is **coverage, calibration and provenance** — and those are the only
   three things the skills address.

---

## 7 · Tool surface

| Tool | The job that needs it |
|---|---|
| `Read` | open an ADR, a layer document, source at `file:line`. All three functions |
| `Grep` | B3 and B12 are counting failures. A count must come from a named query whose text is recorded, not from reading |
| `Glob` | B6 is an enumeration failure. Enumerate `docs/decisions/*`, migrations, routes from the filesystem, never from memory |
| `Write` | emit the ADR, the seam table, the findings list |

**Everything else is denied, and each denial closes a specific hole.**

| Denied | What it would make decorative |
|---|---|
| `Bash` | *the write gate itself.* `CLAUDE.md`: "a path-scoped write gate next to `Bash` is decorative." Also: with no shell the agent **cannot run a test**, so B5's honest verdict — *not checkable here* — is the only one available to it |
| `Agent` | **it restores `Bash` one hop away.** A delegate runs under its own permissions. Granting `Agent` would undo both walls above in a single line |
| `Edit` | the supersede convention. With no `Edit`, the agent structurally cannot rewrite an ADR's history, alter an existing finding, or quietly reconcile `ARCHITECTURE.md` to a decision it just made — which would erase the discrepancy that `design-claim-audit` exists to find |
| `WebFetch` / `WebSearch` | the evidence discipline. Its quarry is this repository and the notes on disk, which carry MEASURED/REPEATED marks that a fetched page does not. Open question in §8 |
| `NotebookEdit`, `TodoWrite`, MCP tools | not needed by any of the three procedures |

**What the surface makes impossible:** it cannot execute anything, so it cannot claim
a dynamic property was verified; it cannot obtain execution by delegation; and it
cannot change any decision that has already been recorded.

**The cost, stated:** it cannot mark a superseded ADR's status. The superseding ADR
names its predecessor and a human flips the old status. It also cannot run the
`CLAUDE.md` checkpoint routine (ROADMAP/BACKLOG/CHANGELOG updates need `Edit`); the
calling session does that. Both are deliberate.

---

## 8 · What must be impossible, and by what mechanism

| Must be impossible | Mechanism | Is it a wall? |
|---|---|---|
| Writing source code — anything outside `docs/` | PreToolUse hook, path allowlist. `docs/hook-proposal-architect-rebuild-write-gate.md` | **wall** |
| Overwriting an existing file | same hook: deny `Write` when the target exists | **wall** |
| Running anything | `Bash` absent from `tools:` | **wall** (absent tool) |
| Getting a shell via a delegate | `Agent` absent from `tools:` | **wall** (absent tool) |
| Editing a recorded decision | `Edit` absent; hook denies overwrite | **wall** |
| Removing its own wall | hook denies `.claude/hooks/**` and `.claude/settings*.json`; both are already outside `docs/`, so this is belt and braces | **wall** |
| Claiming a dynamic property was verified | no `Bash` **and** a four-value verdict where *not checkable here* is one of the values | wall + procedure |
| Auditing an artefact it authored itself | a provenance step ending in an **abstain** row | **procedure only — not a wall.** Named as the design's weakest joint |

### Open questions — no baseline row, therefore not in any skill

1. **The starved option-generator (A2).** Whether Scio's rebuild needs one is
   unmeasured here. Would need a baseline showing narrow option sets.
2. **Whether `WebFetch` should be granted** for live-moving values (cloud service
   limits, pricing). No row; currently denied.
3. **Whether `seam-placement` discriminates at all.** Its base competence is high
   (§6.3) and it has 2 rows. This is the entry to cut first if the evals do not
   separate it.
4. **A hook predicate for self-authorship.** If one exists, §3's weakest joint
   becomes a wall.

---

## 9 · Composition, and what was refused

**Composition.** Caller (main session or a human) → `architect-rebuild`. Two levels,
inside the depth-3 ceiling. For review coverage — the B1 fix — the caller invokes it
**once per declared perspective**, each in a fresh context. That is fan-out at level
1→2 (measured good), not a level-3 dispatch, and it is why the agent has no `Agent`
tool. **Nothing converses with anything.** The verdict on the artefacts is a separate
producer→verifier hop performed by a tester that did not author them.

**Refused by a gate, verbatim.**

> `Error: No such tool available: Agent. Agent is disabled for this session, in
> subagents as well as here.`

Consequences: zero baseline dispatches (§5 uses recorded runs instead), no delegated
mechanical verification, and **no delegated eval run**. Per `agent-assembly`'s own
terms the build is therefore **not finished**: the agent and a tester brief are
staged, and step 6 is unmet.

**Declined by the builder, not by a gate.** `docs/architect-repair-tester-brief.md`
and `docs/hook-proposal-citation-provenance.md` are not on the forbidden list, but
both are downstream of the incumbent architect. Reading either would have told me its
shape and defeated the blind rebuild. Neither was opened. If they contain baseline
evidence, this spec is missing it.
