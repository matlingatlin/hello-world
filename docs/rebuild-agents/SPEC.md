# Spec — the rebuild-proposal agents

Written 2026-08-28 by `agent-builder`. Covers `agent-shape` steps 0–8 and the
`agent-baseline` observation the assembly was allowed to build from.

**Nothing here is implemented in product code and nothing here decides product
scope.** Per `CLAUDE.md`, the feature set, the differentiator and the stack stay
open; these agents *produce proposals* and *prepare a selection*, and a human
selects.

---

## 0 · Does anything already own this job?

Searched, in this order:

| Where | How | Result |
|---|---|---|
| `/home/user/hello-world/.claude/agents/` | glob, then read each | two agents: `architect`, `agent-builder`. Neither owns it — see below |
| `/home/user/hello-world/.claude/skills/` | glob, then read `architecture-review/SKILL.md` in full | `architecture-decision`, `system-decomposition`, `architecture-review`, plus the three `agent-*` builder skills |
| `/home/user/skills-repo/.claude/skills/` (84 talents) | frontmatter grep for `name:`/`description:`, then a symptom grep for `idea\|ideation\|brainstorm\|propos\|novel\|divers\|rewrite\|rebuild\|elicit\|requirement\|discover\|analog\|opportunit\|roadmap\|feature` (61 files hit), then read the descriptions of the eleven plausible owners | nearest three examined in full |
| `/home/user/skills-repo/.claude/agents/` | glob | one agent, `rag-pipeline-reviewer`. Unrelated |

The three nearest, and why each misses:

- **`brainstorming`** — *"You MUST use this before ANY implementation of a feature… Classifies the request (spike / bounded / architectural), explores intent and requirements, presents a design, and STOPS for your human partner's approval."* Pre-implementation design exploration for one change. It is not corpus-aware, has no starvation, and has no way to tell a fresh proposal from a restatement of 85 that already exist.
- **`decision-council`** — its own description says it *"DECIDES between options — distinct from brainstorming (which GENERATES options)"*. It consumes an option set; it does not produce one, and it does not appraise an existing system.
- **`external-domain-audit`** — the closest *method*: build the knowledge base from the outside first and design blind before opening the implementation. But its quarry is conformance to an external protocol/RFC/SDK spec, not what a product should become.
- **local `architect`** — owns architecture *decisions*, decomposition, and review of a design against its claim (`.claude/agents/architect.md:3`). Its diet is deliberately saturated and its scope is architecture, not product capability. It has no generation-under-starvation, no comparable-products pass, and no duplication adjudication. Its `architecture-review` procedure explicitly hands the job away: *"It is **not** a defence against anchoring, and it must not be carried into any step where you are producing a design"* (`architecture-review/SKILL.md:60-61`).

**Verdict: author.** Two new agents. One existing asset is reused rather than
rebuilt — `.claude/skills/architecture-decision/references/far-domain-analogy.md`
is opened directly by the new generator skill instead of being copied.

---

## 1 · The job, as one sentence and one artefact

The need decomposes into two jobs with **incompatible context diets**, so it is
stated twice.

| Agent | One sentence | The artefact |
|---|---|---|
| `rebuild-prospector` | It answers what a product in this problem space could be, without having seen how this one is built, and emits candidates. | `docs/rebuild/candidates/<run-id>.md` — a candidate list, each candidate with its origin move, plus the two required tables (relational map, comparable-products coverage) |
| `rebuild-adjudicator` | It takes the existing system and its 85 standing proposals as evidence, rules on what each candidate actually is, appraises what should stop existing, and emits a dossier a human selects from. | `docs/rebuild/dossier/<date>.md` — every candidate with `already-built / already-proposed (id) / new / not-applicable`, a retire/keep/rewrite inventory at `file:line`, and two separately scored axes with no ranking |

---

## 2 · The context diet

### `rebuild-prospector` — starved

**Must see**

- `docs/rebuild/brief/*.md` — a problem brief written by a human. Problem, user,
  what they have at the end, constraints of the *domain*, and an assigned
  ordinary occupational role for this instance. **No mechanism, no layer names,
  no component names.**
- `.claude/skills/architecture-decision/references/far-domain-analogy.md` —
  checked: contains no Scio solution vocabulary.
- The open web, via `WebSearch` / `WebFetch`.

**Must not see**

- `/home/user/scio/docs/next/**` — the 85 standing proposals.
- `/home/user/scio/docs/as-built/**` — the layer-by-layer description.
- `/home/user/scio/docs/triage/**`, `/home/user/scio/docs/mined/**`.
- This repo's solution documents: `docs/ARCHITECTURE.md`, `docs/LAYER-*.md`,
  `docs/LIBRARY.md`, `docs/DESIGN.md`, `docs/DATA-MODEL.md`, `docs/PRD.md`,
  `docs/STRATEGY.md`, `docs/UX-FLOW.md`, `docs/decisions/**`, `docs/BACKLOG.md`,
  `docs/RETHINK-BRIEF.md`.
- Any source file in either repository.

Why, and how strongly it is measured: seeding a generator with existing good
ideas measured **worse than no seed** (cosine 0.403–0.428 vs base 0.377; human
seeds p = .95); models given background material produce outputs experts call
*"narrow and too tied to the background"* (narrowness 1.00–1.55 vs human 0.47);
five independent measurements converge on *starve the generator*. Sources with
per-claim marks: `/home/user/skills-repo/knowledge/notes/llm-idea-generation.md`.

Residual leak this diet does **not** close: a subagent loads the whole
`CLAUDE.md` hierarchy whatever its tools are (measured, canary probe —
`knowledge/notes/subagents.md:23-30`). This repo's `CLAUDE.md` names the product
category and the doc map. It names files the prospector cannot open. Accepted,
and recorded here rather than hidden.

### `rebuild-adjudicator` — saturated

**Must see** — everything above that the prospector must not: both repos' docs
in full, the source tree, and the candidate files.

Why: judging already-published (therefore non-novel) ideas, a model scored
novelty **6.14/10 without retrieval and 2.38/10 with it** — a 2.6× inflation.
An adjudicator without the 85 in front of it will certify restatements as new.

**Must not see** — nothing is withheld. The one thing it must not *do* is rank,
which is §6.

---

## 3 · Split test

| Rule | Fires? | Consequence |
|---|---|---|
| 1 · opposite diets → always separate | **yes** | starved generator and saturated evaluator cannot share a context window. **This decides the roster.** |
| 2 · independent quarry → separate | n/a once 1 has fired | |
| 3 · more than three functions → split | no | 2 and 3 functions respectively |
| 4 · author and tester never the same | **yes** | the prospector never adjudicates its own candidates; the adjudicator never generates |

Within the adjudicator, three procedures share one diet and are sequentially
dependent (the retirement inventory and the candidate rulings both feed the
dossier), so per the rule they are **one agent, three skills** — not three
agents. They are not undifferentiated buckets: each is a distinct procedure over
a distinct input producing a distinct artefact, which is the *scenario* condition
Porter et al. measured at ~35% over ad hoc, rather than the *checklist* condition
they measured at no better than ad hoc.

**Roster: two agents.**

---

## 4 · Functions

### `rebuild-prospector`

| Function | Procedure | Emits |
|---|---|---|
| `blank-slate-positions` | derive positions from the brief alone, on named non-negotiables of the problem, before any external input | a position list, each falsifiable, each with the thing it refuses |
| `comparable-products-sweep` | enumerate comparable products from the outside and diff their feature and role coverage against the brief | a coverage table: capability → who has it → present in brief / absent / deliberately refused |

The far-domain relational map is not a third skill: `blank-slate-positions`
opens the existing
`.claude/skills/architecture-decision/references/far-domain-analogy.md` and runs
its four moves. Reuse, not rebuild.

### `rebuild-adjudicator`

| Function | Procedure | Emits |
|---|---|---|
| `capability-retirement-audit` | for each existing capability, what breaks if it is deleted, who consumes it, what evidence it works | inventory rows: capability → `file:line` → `keep / rewrite / retire / unverified` → what breaks |
| `proposal-adjudication` | for each candidate, name its nearest standing proposal by id, rule on status, and tabulate the framing distribution of the candidate set | ruling rows + the framing-distribution table against the measured human reference rates |
| `selection-dossier` | assemble both into a document a human selects from, with two separately scored axes and a stated non-ranking | the dossier, sorted by id, with the human's decision column empty |

---

## 5 · Tool surface

### `rebuild-prospector`

| Tool | The job that needs it |
|---|---|
| `Read` | open the brief and the analogy reference. **Gated by hook to an allowlist of two paths.** |
| `Write` | emit the candidate file. Gated by the same hook to `docs/rebuild/candidates/`. |
| `WebSearch` | the comparable-products sweep — the strongest measured lever for "what is missing" (Ferrari et al.: comparable-products pass added **up to 42% additional feature coverage**, 8–17% novel roles) |
| `WebFetch` | read a product's own documentation rather than a summary of it |

Deliberately absent, each because its presence would make the diet decorative:

- **`Grep` and `Glob`** — a `Grep` with no `path` searches the whole repo and
  returns matching *lines*, which is content. An absent tool beats a gated one,
  so they are not granted at all and the hook has two matchers instead of five.
- **`Bash`** — a shell reads any file. A read gate plus `Bash` is not a gate.
- **`Agent`** — a delegate has its own context and its own permissions. A
  starved agent that can dispatch a reader is not starved.
- **`Edit`**, **`Skill`**, **`TodoWrite`** — no job needs them.

**What this surface makes impossible:** the prospector cannot obtain the
existing system's solution vocabulary by any route available to it.

### `rebuild-adjudicator`

| Tool | The job that needs it |
|---|---|
| `Read`, `Grep`, `Glob` | the corpus and the source tree; `file:line` evidence for every retirement row |
| `WebSearch`, `WebFetch` | whether a candidate is already a commodity someone else ships — a real adjudication, not a nicety |
| `Write`, `Edit` | the dossier. Gated to `docs/` by the **already-installed** `.claude/hooks/docs-only-write.sh` |

Absent: **`Bash`** (it must not run or repair anything; a finding is handed
over, not applied), **`Agent`** (it would let the saturated agent commission a
generator and grade its own supply), **`NotebookEdit`**, **`Skill`**.

**What this surface makes impossible:** the adjudicator cannot change the system
it is appraising, and cannot generate the candidates it rules on.

---

## 6 · Where the wall goes

| Must be impossible | Mechanism |
|---|---|
| the prospector reading the 85 proposals, `as-built/`, triage, or any solution document | **hook** — `rebuild-prospector-diet.sh`, PreToolUse, `^(Read\|Write)$`, read-allowlist of exactly two paths, deny by default. Proposal: `hook-proposal-prospector-diet.md` |
| the prospector reaching those files by shell or delegate | **absent tools** — no `Bash`, no `Agent`, no `Grep`, no `Glob` |
| the prospector writing anywhere but its candidate directory | same hook, write branch |
| the adjudicator writing outside `docs/` | **hook** — the existing `.claude/hooks/docs-only-write.sh`, already installed, reused unchanged |
| the adjudicator editing code or tests | same hook, plus no `Bash` |

**Stated as a request, not a wall, and marked as such in both agent bodies:**

- that the adjudicator does not rank. There is no hook for a sentence in a
  document. The mitigation is structural instead — the dossier template has no
  rank column, rows are sorted by id, and the two axes are scored separately
  because originality and feasibility measured **r = −0.71**, which makes a
  single "quality" score incoherent rather than merely crude.
- that a human selects. Enforced only by the dossier's empty decision column.

This distinction is itself the measured point: eight anchoring-warning variants,
differing in content and timing, were **all indistinguishable from no warning**,
and one "be as different as possible" instruction made conformity *worse*
(.25 → .33). Anything that must hold is a hook or an absent tool.

---

## 7 · Composition

```
human writes brief  ──►  rebuild-prospector  ×k, parallel, blind to each other
   (per-instance             │  candidates/<run-id>.md
    ordinary role)           ▼
                       rebuild-adjudicator  (saturated, different diet)
                             │  dossier/<date>.md
                             ▼
                       human selects
```

- **Fan-out** of prospector instances — measured good. The gain is *between*
  instances (individuals working alone and pooled beat the same people
  interacting, d = 1.395, k = 34, N = 2,577), so the instances **never converse**
  and never see one another's candidate files.
- **Producer → independent verifier with a different diet** — measured good.
- The fan-out is run by the human or the main session. **Neither agent holds
  `Agent`**, so neither can convene the other; there is no round table to form.
- Depth is 2. Nothing here approaches the depth-3 ceiling.

The per-instance **ordinary occupational role** is the one place a persona is
used, and only because this is diversity work: ordinary personas measured **2.6×**
between-agent variation and ordinary beats visionary. The variation is the
measured effect, so the role lives in the per-instance brief, **not** in the
agent body — a single fixed persona baked into the file would buy none of it and
would carry the correctness penalty (MMLU 71.6% → 66.3%).

**No count is given to the prospector, ever.** Quotas act as ceilings: told
"5–7" → produced 7; told "at least 20" → 21; **told nothing → 29.**

---

## 8 · The baseline, observed

### 8.0 · How it was observed, and what that costs

`agent-baseline` requires dispatched runs. **The `Agent` tool was refused for
this session**, verbatim:

> `Error: No such tool available: Agent. Agent is disabled for this session, in subagents as well as here.`

So no fresh runs were dispatched. Substituted: **the artefacts that unaided runs
on this exact job already left behind** — seven `docs/next/` layer documents
(85 proposals), four `docs/triage/` documents, and `docs/RETHINK-BRIEF.md`.
These were written without skills or subagents, by runs other than this one, and
every row below is quoted at `file:line` from them.

What the substitution buys: real, full-length output on the real task, longer
and more careful than a dispatched run would produce, and not authored by me.

What it does **not** buy, and no row below may be read as if it did:

1. I did not control the prompt. A failure may be an artefact of a brief I
   cannot see. This is why the uniform proposal counts are marked `draw`.
2. "Both runs did it" becomes "N of 7 documents did it". Documents written under
   a shared template are **not** independent draws, so a 7/7 result shows the
   template, which is exactly what several rows below claim — but it cannot
   separate template from model.
3. There is no negative control. I cannot say what these runs would *not* have
   produced.

The task prompt that a fresh baseline should use is saved below in §8.4,
verbatim, unrun.

### 8.1 · Failure table

| # | What they did — quoted | Consequence | Spread | Verdict |
|---|---|---|---|---|
| 1 | The proposal space is partitioned by the existing decomposition. `docs/next/README.md:8`: *"One document per layer, same nine headings."* All 85 proposal ids carry a layer letter — `A-1…A-10`, `B-1…B-10`, `C-1…C-12`, `D-1…D-10`, `E-1…E-15`, `F-1…F-14`, `G-1…G-14` | A "fresh eyes" proposal cannot be *expressed*: no row can say layers B and C should be one thing, that F should not exist, or that the product's shape should not be a pipeline. The option space was the as-built carve | 7/7 | **teach** (prospector's option space is the problem, not the layer set) + **wall** (diet) |
| 2 | The nine headings are `Where the layer stands / Refining what exists / What is missing / Out of the box / The means / Retrieval versus packing / Token economy / Data worth owning / ADR proposals` (`docs/next/README.md:10-18`). **Every one adds or refines. None subtracts.** | The owner asked "what to keep, what to rewrite". *Keep* implies the option of not-keep, and the artefact has no slot to hold it. Across 85 proposals the only deletions are housekeeping — `G-14` *"`modules/stream/` deleted"* | 7/7 | **teach** → `capability-retirement-audit` |
| 3 | Generation was performed saturated. The wide brainstorm is §4, *after* §1 "Where the layer stands", §2 "Refining what exists" and §3 "What is missing", inside a document about that layer. Its yield is layer-shaped: `LAYER-A-INTAKE.md:353` §4.1 *"Elicit by proposing, not by asking"* is a change to the existing question loop; §4.2 is *"Named for completeness, because it is the pattern an architect would reach for"* and rejected as *"pattern-fitting"* | The single most-converged finding in the literature is that this is the wrong order, and it cannot be fixed by ordering the sections, because ordering is prose | 7/7 | **wall** — the generator gets a separate agent with a hook, not an earlier section |
| 4 | The repo's own defence against exactly this is a sentence. `docs/RETHINK-BRIEF.md:16-19`: *"**Write Pass A before opening the codebase, before reading the reviews, and before reading the appendix of this file.**"* and `:145` *"**Do not read this until step 5.**"* And the same file, `:8-11`, records that defence already failing once: *"An earlier draft of this document did the exact thing it warned against: it told the blank-slate pass what the answer was… A blank slate handed a conclusion is not a blank slate."* | One documented instance of the prose wall failing, in the file whose job was to hold it. Eight anchoring-warning variants measured indistinguishable from no warning | 1 documented instance, plus row 3's 7/7 | **wall** |
| 5 | The author ordered its own proposals. `LAYER-D-LIBRARY.md:609` *"**Ordering.** **D-2 first, and by a distance**"* … *"D-7 and D-8 are the strategic pair — D-7 stops us buying the non-differentiator, D-8 builds the one thing that cannot be bought."* Also `LAYER-A-INTAKE.md:692`, `LAYER-B:702`, `LAYER-C:847`, `LAYER-E:966`, `LAYER-F:944` | Model-vs-expert agreement on idea quality is **22–40%** where expert-expert is 60%, and they disagree in *opposite* directions. Worse, the orderings **mix two kinds**: dependency order, which is checkable (`LAYER-A-INTAKE.md:696` *"A-2 next — it is what makes A-4, A-5 and A-6 decidable"*), and value order, which is not (the D-7/D-8 line) — with no marker separating them | 6/7 | **teach** → `selection-dossier`: dependency edges are stated and checkable; value order is the human's and is left empty |
| 6 | No scored axes anywhere. The §9 tables carry `# \| Proposal \| What it decides` and nothing else | A human is handed 85 rows, an author-supplied order, and no way to select. Selection is the measured bottleneck — groups that generated more and more original ideas **selected no better than chance**, and instructing them to pick original-and-feasible **did not improve selection at all** | 7/7 | **teach** → two axes, scored separately (r = −0.71) |
| 7 | The comparable-products pass was run properly in **one** of seven layers and thinly elsewhere. `LAYER-F-DESIGN-WINDOW.md:9` *"how Lovable, v0, Figma Make, Bolt and Replit actually implement element-level…"* with a mechanism table at `:574`; competitor mentions by file: F 12, G 11, E 9, D 4, B 3, **A 2**, C 0 | The strongest measured lever for "what is missing" — **up to 42% additional feature coverage**, 8–17% novel roles, up to 21% of post-interview content on completely novel topics — was applied to one seventh of the surface | 1/7 done well | **teach** → `comparable-products-sweep` as a required step with a coverage table |
| 8 | Twelve files in **this** repo cite `docs/as-built/…` as a local path. It is not here; it is at `/home/user/scio/docs/as-built/`. Includes `.claude/agents/architect.md`, `docs/ROADMAP.md`, `docs/BACKLOG.md`, `docs/decisions/0021-the-architect-agent.md` and four skill files | An agent following the citation opens nothing and either stops or invents. Already open as B128 | 12 files | **teach** → the corpus manifest in the adjudicator's reference file gives absolute paths only, and the dossier carries a verified-vs-carried count |
| 9 | Proposal counts per document cluster tightly: 10, 10, 12, 10, 15, 14, 14 | Consistent with a quota, and quotas measured as ceilings (told 5–7 → 7; told nothing → **29**). But I cannot see the instruction that produced them | not established | **draw** — kept, not built on. Acted on only as an omission: no count is given to the prospector |

### 8.2 · What the baseline did well — leave this alone

This is the regression zone. Skills lifted task success 33.9% → 50.5% overall
*and regressed roughly 15% of tasks*, concentrated where the base was already
competent, with software engineering the weakest domain at +4.5%. Nothing in
either agent re-teaches any of the following, and a reviewer should treat any
future rule that does as noise.

| Already competent | Evidence |
|---|---|
| **`file:line` discipline, and a stated verification method** | `LAYER-A-INTAKE.md:717` *"Code claims carry `file:line` and were verified against the working tree, with `pytest -k intake` → 67 passed"* |
| **Estimates marked as estimates, with the right instrument named** | same footer: *"Prompt sizes are chars÷4 estimates and are marked as such — `messages.count_tokens` is the correct instrument and no key was available"* |
| **Speculation labelled** | `LAYER-A-INTAKE.md:385-387` *"### 4.3 Speculation: … **Marked as speculation.** No evidence from our system supports it yet; it is offered because it predicts specific, testable things"* |
| **Rejected options recorded with reasons rather than dropped** | `LAYER-A-INTAKE.md:378` *"**Verdict: not for this layer.** … Adopting it here would be pattern-fitting."*; the six-row *Alternatives considered* table at `LAYER-G-CROSS-CUTTING.md:964-971` |
| **Unanswerable questions surfaced instead of silently decided** | `LAYER-D-LIBRARY.md:617` *"**Two open questions I could not settle from the code**"*; `LAYER-A-INTAKE.md:705` |
| **Blockers named as blockers** | `A-10` *"**blocked on ADR-0019**"*; `D-1` *"Depends on ADR-0019"* |
| **A far-domain analogy did happen, unprompted, and was done properly** | `LAYER-A-INTAKE.md:390-405` maps intake onto survey design and Krosnick's satisficing model, then derives **three testable predictions**. This is the right shape. The finding in row 7 is that it was unsystematic, not that it was absent or poor |
| **No rewrite folklore** | grepped `/home/user/scio/docs` for `100x\|100×\|Standish\|CHAOS\|IBM Systems Sciences\|cost of a defect\|10x more expensive\|68% vs 21%\|312 attempts\|rewrites fail\|second-system`, case-insensitive: **no matches**. The temptation to write a folklore ban was refused on this evidence |
| **Licensing and consent treated as first-class** | `A-10` *"ReqElicitBench's data is not vendored"*; `D-1`, `G-4` |

### 8.3 · Rows the agents were **not** built from

`agent-assembly` may build only from `teach` and `wall`. Recorded here instead:

- Row 9 (`draw`).
- **Open question, no row behind it:** whether a keep/rewrite/retire verdict
  should carry a cost estimate. The rewrite-vs-refactor literature is *empty* —
  the one large measured study (328 Microsoft engineers, Windows 7 history) found
  preferentially refactored modules decreased post-release defects **7% less**
  than the rest. Any keep-vs-rewrite argument has to rest on something other than
  the literature. `capability-retirement-audit` therefore asks what *breaks*,
  which is checkable, and not what it *costs*, which is not.
- **Open question:** whether the prospector should also be denied `WebFetch` of
  a URL that could mirror the sibling repo. It is not published, so the route is
  hypothetical; the hook does not cover it and the gap is named rather than
  papered over.

### 8.4 · The baseline task prompt — verbatim, saved, **unrun**

> You are working in /home/user/hello-world. Do this job end to end and use whatever approach you think best.
>
> /home/user/hello-world is a working AI app builder (product name: Scio) — a web-based competitor to Lovable. It is roughly 26,000 lines across four workspaces and was built end to end without a single skill or subagent.
>
> A sibling repository at /home/user/scio documents it exhaustively:
> - /home/user/scio/docs/as-built/ — what the system IS, layer by layer (Layers A through G), with claims traced to file:line.
> - /home/user/scio/docs/next/ — what to DO with it. Seven layer documents; the §9 section of each carries numbered ADR proposals. 85 proposals exist in total.
> - /home/user/scio/docs/triage/ — triage of mined findings into SKILL / ADR / FIX / DROP.
>
> The owner wants to rebuild the product with fresh eyes: what to keep, what to add, what is missing, what to rewrite — for the app, its functions, and its layers.
>
> Produce those proposals.
>
> Write your proposal document to <scratch path> — do not write anything into /home/user/hello-world or /home/user/scio. In your final message give me (a) the path, (b) a count of proposals you produced, and (c) a short rationale: how you produced them, what you read and in what order, and how you decided what went in.
>
> Work alone. Do not ask me questions; make your own calls and record them.

Dispatch this to **at least two** independent parallel runs that cannot see each
other, then re-derive §8.1 against their outputs. Until that is done, every row
in §8.1 is marked **`observed from prior artefacts, not from dispatched runs`**.

---

## 9 · Placement table (`agent-assembly` step 1)

| Spec item | Tier | Where |
|---|---|---|
| what each agent is; the boundary and its mechanism; the map of functions | 0 · agent body | `.claude/agents/rebuild-prospector.md`, `.claude/agents/rebuild-adjudicator.md` |
| blank-slate derivation + the analogy pass | 1 · `skills:` | `.claude/skills/blank-slate-positions/` |
| comparable-products coverage | 1 · `skills:` | `.claude/skills/comparable-products-sweep/` |
| retire/keep/rewrite inventory | 1 · `skills:` | `.claude/skills/capability-retirement-audit/` |
| candidate rulings + framing distribution | 1 · `skills:` | `.claude/skills/proposal-adjudication/` |
| the dossier and the non-ranking | 1 · `skills:` | `.claude/skills/selection-dossier/` |
| doc-driven / checkpoint rules binding every agent here | 2 · `CLAUDE.md` | already there, unchanged |
| the corpus manifest with absolute paths; the measured numbers and their limits | 3 · `references/` | `.claude/skills/proposal-adjudication/references/corpus.md`, `.../evidence.md` |
| the far-domain four moves | 3 · `references/` | **reused**: `.claude/skills/architecture-decision/references/far-domain-analogy.md` |
| the brief template; the candidate template; the dossier template | 4 · `assets/` | inside the owning skills |
| the prospector's diet | 5 · hook | `docs/rebuild-agents/hook-proposal-prospector-diet.md` — **a human installs it** |
| the adjudicator's write boundary | 5 · hook | existing `.claude/hooks/docs-only-write.sh`, reused unchanged |

Nothing is placed in `.claude/rules/`: measured by canary probe, scoped and
unscoped, **it does not reach a subagent**.
