# Spec — stage 1 of the pipeline: `domain-researcher` and `primary-source-verifier`

Written 2026-08-29 by `agent-builder`. Covers `agent-shape` steps 0–8 and the
`agent-baseline` observation that `agent-assembly` was allowed to build from.

Stage 1 of `docs/decomposition-agent-pipeline.md` — research → shape → baseline →
assembly → validate → test. It closes **B130**: nothing in this pipeline checked a
knowledge note against its cited sources.

**Two constraints from the decomposition are binding and are honoured here:**

1. Every construction rule, threshold and limit lives in `.claude/validate/agents.py`
   and **is not restated in this document or in any skill built from it.** The
   change matrix says why: a rule repeated in prose is a second place for it to rot.
   Where a cap is relevant below, it is named as "the cap the validator enforces".
2. Research is scoped by the **candidate sentence**, and `agent-shape` may commission
   one narrower second sweep (decomposition §5). The researcher takes a scope in; it
   does not decide the scope itself. §5 and §6 give the mechanism.

---

## 0 · Does anything already own this job?

| Where | How | Result |
|---|---|---|
| `/home/user/hello-world/.claude/agents/` | glob, then read | 5 agents: `architect`, `agent-builder`, `rebuild-prospector`, `rebuild-adjudicator`, `architect-rebuild`. None researches a domain; none opens a cited source |
| `/home/user/hello-world/.claude/skills/` | glob (14 skills), read `design-claim-audit/SKILL.md` in full | nearest is `design-claim-audit` — examined below |
| `/home/user/skills-repo/.claude/skills/` (84 talents) | frontmatter grep on `name:`/`description:` filtered to `literature-review, research-scout, market-research, external-domain-audit, source-grounded-implementation, deep-reading, verification-before-completion`; read `literature-review` and `deep-reading` in full | two genuine near-owners — examined below |
| `/home/user/skills-repo/.claude/agents/` | glob | one agent, `rag-pipeline-reviewer`. Unrelated |
| `/home/user/skills-repo/knowledge/notes/` | read `INDEX.md`, `research-methodology.md` in full | `research-methodology.md` is a *note about* the method, not an executable procedure, and is itself a baseline exhibit (§8, row R2) |

The four nearest, and why each misses:

- **`literature-review`** (library, community origin) — *"search planning, source
  screening, evidence log, citation checks."* The closest owner of the **search**
  half, and it is good at it: a search-protocol table, a four-key dedup order,
  three-stage screening with recorded exclusion reasons, a structured extraction
  table. It is **reused, not rebuilt** (§4). What it does not do: it takes no scope
  input, it has no MEASURED/REPEATED verdict, it does not produce a note in this
  base's shape — and its verification step, `literature-review/SKILL.md:149-157`, is
  five bullets of self-administered prose ending *"do not cite a paper for a claim
  it does not make."* That sentence is executed by the agent that wrote the
  citations. It is exactly the applicant verifying its own credentials.
- **`deep-reading`** (library, built here) — description ends *"or when verifying
  claims against a source."* Its step 6 is a **self-test**: *"Without looking at the
  source, write a summary from the notes alone. Then verify it against the source."*
  Its step 7 assigns `status: verified` — self-assigned by the reader. This is the
  procedure that produced the 26 self-attested notes in §8 row R1. It owns
  comprehension of one document; it does not own scoping, and it cannot own
  verification, because it is the author.
- **`design-claim-audit`** (this repo, the architect's) — checks a claim against a
  **repo artefact** at `file:line`, and its own step 5 routes anything needing
  execution or an external source to `not checkable here`. Its quarry is "does this
  system match this document"; the quarry here is "does this paper say this". It
  also has no shell and no fetch mandate.
- **`research-scout`** (library) — generates search terms and entities for a harvest
  queue. It fuels a sweep; it does not bound one, read a source, or write a note.

**Verdict: author two agents, reusing three existing assets rather than copying
them** — `literature-review` §2–5 for the search protocol, `deep-reading` §1–5 for
reading one long source, and the five notes added to the base on 2026-08-28 as the
output-format exemplar. None is duplicated into the new skills; each is opened at
the step that needs it.

---

## 1 · The job, as one sentence and one artefact

The need splits into two jobs (§3), so it is stated twice.

| Agent | One sentence | The artefact |
|---|---|---|
| `domain-researcher` | It takes a written commission carrying the candidate sentence that scopes it, reaches primary sources, and emits a draft note in which every claim carries its source, what was measured, effect size, sample and population, limits, and a MEASURED or REPEATED verdict. | `docs/research/drafts/<id>.md` — the draft note, plus the scope contract and the per-claim evidence table it was built from |
| `primary-source-verifier` | It takes a draft note it did not write, opens each cited source itself rather than the author's account of it, rules every claim against that source, and writes only the surviving note into the knowledge base. | `docs/research/verdicts/<id>.md` — one verdict row per claim with the quoted line; and, if it passes, `/home/user/skills-repo/knowledge/notes/<id>.md` |

`<id>` is one identifier end to end: commission, draft, verdict, note. That is what
makes the promotion gate in §6 mechanically checkable.

---

## 2 · The context diet

Neither agent is an idea generator, so the starve/saturate rule from
`llm-idea-generation.md` does **not** apply in its canonical form, and this spec
does not claim it does. What matters here is narrower and is stated exactly.

### `domain-researcher`

**Must see:** its commission (`docs/research/commissions/<id>.md`, carrying the
candidate sentence); the open web; the existing base at
`/home/user/skills-repo/knowledge/notes/` — so it extends rather than adds a rival,
which is a standing rule of that repo; and the two reused procedures named in §0.

**Must not see:** nothing is withheld from it. Its constraint is on **scope and
output**, not on input: it may read whatever the commission's questions require,
and it may not *emit* outside them. That distinction is deliberate and is the
weaker of the two available designs — §6 says what it costs.

### `primary-source-verifier`

**Must see:** the draft note, and each source the draft cites, **fetched by itself**.

**Must not see, and this is the whole design:** the researcher's working — its
search transcript, its reasoning, its account of what a source said. The draft's
claim is the thing under test; the researcher's paraphrase of the source is not
admissible evidence for it.

This is not a preference. A single agent that wrote the note **cannot be rid of its
own paraphrase**: asked "does the source say this?", it retrieves what it already
wrote. A second agent has nothing to retrieve and must fetch. The measured backdrop
is that self-critique with no external signal degrades on every model and benchmark
tested — GPT-3.5 on CommonSenseQA fell 75.8% to 38.1% across self-review rounds
(`/home/user/skills-repo/knowledge/notes/llm-idea-generation.md`).

**It is also denied `WebSearch`, by tool surface** (§5): a verifier that can search
will find *a different source that agrees* and call the claim supported. Primary
source verification means the cited source or nothing.

---

## 3 · Split test — one agent, or two? The question the task asked

In order. The first rule that fires decides. The one-agent answer was considered
first and is recorded here with why it loses, because it is the cheaper design.

| Rule | Fires? | On what |
|---|---|---|
| 1 · opposite diets | **not in its canonical form** | Neither generates ideas. A weaker form does hold — the verifier must not hold the researcher's account of the source — but this spec does not rest the roster on it |
| 2 · independent quarry | **yes** | "what does this domain know" vs "does this cited source say this". Different inputs, different artefacts, and the second is measured *between* the two, not within either |
| 3 · more than three functions | **yes** | scoping + extraction + drafting is already at the cap the validator enforces; verification + promotion makes five |
| 4 · author and tester are never the same agent | **yes — and this is the one that decides it** | §8 rows R1, R8, R10, R11 |

### Why one agent loses, on evidence rather than principle

**The one-agent design is not hypothetical. It is the status quo, and it has
already failed here.**

- `deep-reading` step 6 *is* "verify your notes against the source", run by the
  reader. `literature-review` step 8 *is* "do not cite a paper for a claim it does
  not make", run by the citer. Both procedures exist, both are in force in this
  organisation, and both are self-administered.
- Under them, **26 of 26 notes in the base carry `status: verified` and not one
  names who verified it** (§8 R1).
- Under them, a figure attributed to a real study, stating the *opposite* of what
  that study measured, shipped into a live skill and into ADR-0021 and was found
  only later by an **independent** review (`docs/CHANGELOG.md:14-20`, §8 R8).
- The same base already records the identical failure in other people's writing —
  a finding attributed to Diehl & Stroebe that is absent from their paper, and
  Mullen's conclusion reversed (`ideation-and-idea-selection.md:100-106`). It
  records it as a *warning to the reader*. Awareness was present. The check was not.

Adding a fourth step to one agent would add a fourth sentence to that list. The
separation principle this repo applies everywhere else — no agent grades its own
work — **binds here exactly as elsewhere**, and this spec does not argue for an
exception. There is none to argue.

**Roster: two agents.** Within each, the skills are sequentially dependent with the
same diet, so per the same test they are skills and not further agents. They are
not undifferentiated buckets: each is a distinct procedure over a distinct input
producing a distinct artefact.

---

## 4 · Functions — each ending in an artefact

### `domain-researcher` (three, at the cap)

| Function | Procedure | Emits |
|---|---|---|
| `research-commission-scoping` | read the commission; turn the candidate sentence into a bounded question list and an explicit out-of-scope list; rule extend-or-author against the existing base | the scope contract: question rows, exclusion rows, and one `extend <note>` / `author <name>` verdict |
| `claim-evidence-extraction` | per question, reach the **primary** source; per claim record source, locator, the quoted line, what was measured, effect size, sample and population, limits, and MEASURED or REPEATED | the claim table, one row per claim, each row carrying a quote and a locator |
| `knowledge-note-drafting` | assemble the claim table into a note in the base's existing shape, with reciprocal links and an explicit "what could not be found measured" section | `docs/research/drafts/<id>.md` and the back-link table |

The search protocol is **not** a fourth function: `research-commission-scoping`
opens `/home/user/skills-repo/.claude/skills/literature-review/SKILL.md` §2–5 and
runs it. Reading one long source is not a fourth function either:
`claim-evidence-extraction` opens
`/home/user/skills-repo/.claude/skills/deep-reading/SKILL.md` §1–5 — **§1–5 only,
never §6–7**, which are the self-verification and self-attestation this whole
stage exists to remove.

### `primary-source-verifier` (two)

| Function | Procedure | Emits |
|---|---|---|
| `primary-source-verification` | per claim row: fetch the cited source itself, quote the line that carries the claim, run one read designed to disconfirm, rule the row | `docs/research/verdicts/<id>.md` — one verdict per claim in `supported / not-supported / not-in-source / source-unreachable / not-checkable`, each with a quote or a stated reason |
| `note-promotion` | drop or downgrade every claim that did not survive; write the note into the base with a `verified_by` record; emit the back-links the neighbours need | the note path, the drop list, and the back-link patch table |

---

## 5 · Tool surface

### `domain-researcher` — `Read, Grep, Glob, WebSearch, WebFetch, Write, Edit`

| Tool | The job that needs it |
|---|---|
| `Read` | the commission; the existing base; the two reused procedures |
| `Grep`, `Glob` | the reuse-first check — is there already a note that owns this topic |
| `WebSearch` | finding the primary sources for the commissioned questions |
| `WebFetch` | reading a paper or a doc page rather than a summary of it |
| `Write`, `Edit` | the draft, built up over a long run |

Deliberately absent, each with what its presence would make decorative:

- **`Bash`** — a shell writes any path. A path-scoped write gate next to `Bash` is
  not a gate.
- **`Agent`** — a delegate has its own context and its own permissions. A researcher
  that can dispatch is a researcher that can commission its own wider sweep, which
  is the exact failure the decomposition's §5 repair exists to prevent. It also
  means it cannot dispatch its own verifier and grade its own supply.
- **`NotebookEdit`**, **`Skill`**, **`TodoWrite`** — no job needs them.

**Argument shape (poka-yoke).** The one shape that matters: the draft's path is
`docs/research/drafts/<id>.md` where `<id>` is the commission's own filename. There
is no free-text "topic" parameter anywhere in the surface, so an uncommissioned
sweep has nowhere to land. Anthropic's own report of this technique — requiring
absolute filepaths instead of relative ones — eliminated a class of model error
outright; the same move is used here on the output path rather than the input.

**Stopping condition.** Not autonomous: one run per commission, ending when every
question row in the scope contract carries either a claim row or an explicit
"not found measured" row. There is no loop that can decide to keep looking. Fetch
attempts per source are capped at three, following `research-methodology.md`'s
"cap lookup attempts (~3) and state uncertainty rather than looping".

**What this surface makes impossible:** it cannot run a command, cannot delegate,
and cannot verify its own output — the verifier is a different agent it has no
tool to call.

### `primary-source-verifier` — `Read, Grep, Glob, WebFetch, Write`

| Tool | The job that needs it |
|---|---|
| `Read` | the draft, and the base it is writing into |
| `Grep`, `Glob` | checking the base for an existing owner and for the back-links |
| `WebFetch` | the cited source itself |
| `Write` | the verdict document, and the promoted note |

Deliberately absent:

- **`WebSearch`** — this is the load-bearing absence. With it, a claim it cannot
  find in the cited source can be "verified" against some other source that agrees.
  That is corroboration, not primary source verification, and the whole point of
  B130 is the difference. Without it, the only URLs reachable are the ones the
  draft names.
- **`Edit`** — it must not rewrite an existing note. New notes only; a change to a
  note that already exists is a patch document a human applies (§6). This mirrors
  the create-only rule that governs this builder, for the same reason: an editor of
  existing records can rewrite the record.
- **`Bash`**, **`Agent`** — as above. `Agent` additionally would let it commission
  the research it is checking.

**Stopping condition.** Bounded by the draft: one verdict per claim row, no more.
Three fetch attempts per source, then `source-unreachable`.

**What this surface makes impossible:** it cannot obtain a source the draft did not
cite, cannot alter an existing note, and cannot produce the draft it is judging.

---

## 6 · Where the wall goes

| Must be impossible | Mechanism | State |
|---|---|---|
| the researcher sweeping a domain nobody commissioned | **hook** — deny a draft write unless `docs/research/commissions/<id>.md` exists and `<id>` matches the draft filename; deny all writes to the commissions directory | **proposed**, `docs/hook-proposal-research-commission.md` |
| the researcher writing into the knowledge base | same hook, deny-by-default outside `docs/research/drafts/` | **proposed**, same file |
| the researcher reaching either by shell or delegate | **absent tools** — no `Bash`, no `Agent` | **in force now** |
| a note landing in the base with no independent verdict behind it | **hook** — deny a write to `<base>/knowledge/notes/<id>.md` unless `docs/research/verdicts/<id>.md` exists | **proposed**, `docs/hook-proposal-note-promotion.md` |
| the verifier overwriting a note that already exists | same hook, create-only | **proposed**, same file |
| the verifier substituting a source of its own for the cited one | **absent tool** — no `WebSearch` | **in force now** |
| either agent verifying its own note | **absent tool** — neither holds `Agent`, so neither can convene the other; the handoff is a document a third party moves | **in force now** |

### Stated as a request, and marked as such rather than claimed to hold

- That the verifier fetches **only** URLs the draft cites. No hook checks this;
  absent `WebSearch` removes the easy route, not every route. What holds it
  structurally is the verdict table: each row carries the URL fetched, and the emit
  step requires that set to be a subset of the draft's cited URLs, with anything
  else listed separately under "corroboration, not verification".
- That the researcher does not answer a question the commission excluded. The hook
  gates the *path*, not the *content*. Content gates were tried in this repo and an
  independent tester walked past them three ways.
- That `agent-shape` commissions at most **one** narrower second sweep. That is a
  rule about a caller, and this build cannot reach the caller.

### The honest state of the wall as shipped

**Neither hook is installed, and neither agent file carries a `hooks:` block.**
This builder may not write `.claude/hooks/` and may not edit an agent that exists;
a human installs both scripts and adds the frontmatter lines given in the proposals.
Until then, each agent's real boundary is its **absent tools**, which are in force,
plus prose, which is not a wall. Both agent bodies say this in those words. The
tester brief opens with it. Do not read the table above as describing today.

---

## 7 · Composition

```
candidate sentence, from step 0 triage or a human
        │   docs/research/commissions/<id>.md
        ▼
domain-researcher            (one run per commission; several commissions may
        │                     run in parallel, blind to each other)
        │   docs/research/drafts/<id>.md
        │
        │   ── agent-shape may commission ONE narrower second sweep: <id>-b ──┐
        ▼                                                                     │
primary-source-verifier      (different quarry, fetches for itself)  ◄────────┘
        │   docs/research/verdicts/<id>.md
        │   /home/user/skills-repo/knowledge/notes/<id>.md   (new notes only)
        ▼
agent-shape  →  agent-baseline  →  agent-assembly  →  validator  →  tester
```

- **Producer → independent verifier, different diet, external signal** — the pattern
  with measured support behind it, and the reason this stage exists.
- **Fan-out is by commission, not by duplication.** Two researchers on the same
  commission is not fan-out; it is two draws on one question.
- **Nothing converses.** Neither agent holds `Agent`; the handoff is a document.
  Agents that converse collapse toward one answer — 0 of 62 comparisons significant
  across 12 interventions.
- Depth 2. Nothing here approaches the nesting ceiling.
- **No persona in either body.** Neither job is diversity work.

---

## 8 · The baseline, observed

### 8.0 · How it was observed, and what that costs

`agent-baseline` requires dispatched runs. **This session holds no `Agent` tool and
no shell** — the tool surface available was `Read`, `Grep`, `Glob`, `Write`, `Edit`,
`WebFetch`, `WebSearch`. No runs were dispatched, and none of the rows below comes
from one.

Substituted, per that skill's own clause *"the failures are already recorded from a
real run … a live run that went wrong is a better baseline than a synthetic one,
because nobody constructed it"*: **the 26 notes the base already contains.** They
are the output of unaided runs of exactly this job — go and research something,
write it down — performed by runs other than this one, under `deep-reading` and
`research-methodology`, before any of the constraints proposed here existed. Every
row is quoted at `file:line` or comes from a query stated in the row.

What the substitution buys: real, full-length output on the real task, not authored
by me, and large enough to count across (26 notes, 76 cited URLs).

What it does **not** buy, and no row may be read as if it did:

1. I did not control the prompts. A failure may be an artefact of an instruction I
   cannot see.
2. "Both runs did it" becomes "N of 26 notes did it". The notes share a template
   and a house style, so they are not independent draws; a 26/26 result shows the
   template, which is what several rows below actually claim — but it cannot
   separate template from model.
3. There is no negative control from a dispatched run. Partially compensated: §8.3
   records one claim family verified **live** against its cited source during this
   session and found sound, so the base is not uniformly defective and a verifier
   that finds a defect in everything would be miscalibrated.

The task prompt a real baseline should use is §8.5, verbatim and unrun.

### 8.1 · Failure table

| # | What they did — quoted or queried | Consequence | Spread | Verdict |
|---|---|---|---|---|
| R1 | **Every note attests to its own accuracy.** `grep -n '^status:'` over `knowledge/notes/` returns 26 hits, all `status: verified`. No note carries a verifier, a verification date distinct from the fetch date, or a record of what was checked. `INDEX.md:5-7` presents this as the base's quality contract: *"Every claim carries a source URL, a fetch date, and a status (verified / unverified / outdated)"* | The field records that the author was satisfied. A reader cannot distinguish a claim checked against its source from a claim the author remembered. This is B130 in one query | 26/26 | **wall** — a second agent, and the promotion gate |
| R2 | **A per-claim evidence verdict exists in 8 notes of 26.** `grep -c 'MEASURED\|REPEATED'` hits 8 files (36 occurrences), 5 of which are the batch added 2026-08-28 for that purpose. The other 18 carry none | Claims that are documented behaviour, claims from a study, and claims from a blog post are typographically identical. `research-methodology.md:32-39` — the note that *defines* the house method — lists "every claim needs a source" as rule 1 and carries no per-claim marks of its own | 18/26 | **teach** → `claim-evidence-extraction` |
| R3 | **Claims are not bound to a source.** `subagents.md` cites one URL and asserts on the order of forty separate facts. `long-text-comprehension.md` lists three sources and makes roughly a dozen claims across *"Verified claims"*, *"Outdated claims"*, *"Overstated claims"* (`:19`, `:29`, `:37`) — no claim names which source it came from | Verification is impossible in principle, not just undone: to check one claim a reader must re-read every source. Exactly the condition under which the Diehl & Stroebe misattribution the base itself warns about survives | 24/26 (all but the two most recent) | **teach** → `claim-evidence-extraction` (a row carries its own locator) |
| R4 | **A claim cites a source the note does not list.** `long-text-comprehension.md:61` — *"From ECC token-budget-advisor (heuristic, ±15%): prose ≈ words × 1.3; code/mixed ≈ chars / 4."* The note's `sources:` are decodeclaude.com, a claude-code GitHub issue, and *"user-provided tips text (unsourced)"*. There is no ECC entry | A number with a stated precision, in a note marked `verified`, whose origin cannot be reached from the note. `±15%` asserts a measurement; nothing here shows one was made | 1 instance found, mechanically detectable in all | **teach** → the drafting rule that the source set is the union of the claim rows' sources, and **wall** — a claim whose URL is not in the source list has no verdict row and cannot be promoted |
| R5 | **A number contradicts itself seven lines later, with no query behind either.** `skill-authoring-eval-methodology.md:50` *"all 19 are vertical/library or covered"*; `:56` *"the **Library:** the 18 vertical skills, catalogued"* | A reader cannot tell which is right and cannot check either from the note. A count of things is asserted, not queried | 1 instance | **draw** — one instance, not reproduced. Kept, not built on; the rule it would motivate is already carried by R2/R3 |
| R6 | **The closest existing owner's verification step is a sentence the author says to itself.** `literature-review/SKILL.md:149-157`, step 8 *"Verify Citations"*: *"verify DOI, PMID, arXiv ID, or official URL … do not cite a paper for a claim it does not make."* No artefact, no verdict, no second party | The most thoroughly measured non-intervention available, applied to the exact failure mode. Eight anchoring-warning variants, differing in content and timing, were all indistinguishable from no warning | the step exists and is in force | **wall** |
| R7 | **The self-attestation is procedural, and its source is identifiable.** `deep-reading/SKILL.md:55-61`, step 6: *"Without looking at the source, write a summary from the notes alone. Then verify it against the source."* Step 7: *"State claims as `verified` / `unverified` / `outdated`"* — by the same reader | R1 is not carelessness; it is this procedure executing correctly. Self-critique with no external signal measured worse on every model and benchmark tested, 75.8% to 38.1% in one case | it produced 26/26 | **wall** — the fix is a different agent, not a better sentence |
| R8 | **A misattributed figure shipped and was caught only from outside.** `docs/CHANGELOG.md:14-20`: `architecture-decision` and ADR-0021 both said Fischhoff's subjects *"moved the probability they assigned to 'everything else' from .078 to .468"*. *"They did not: .468 is the normative value … and they answered .140."* Found by *"an independent review of the agent"* | A real citation, a real study, a claim the study does not make, in a live skill and a signed decision record. The error *"flattered the intervention"* — it drifted toward what the author wanted. Identical in shape to the Diehl & Stroebe fabrication the base warns readers about | 1 instance, in our own output, shipped | **wall** — external verification; **teach** — a row carries the quoted line, never a recalled number |
| R9 | **A note's breadth is set by whoever is writing it.** Neither `deep-reading` nor `research-methodology` takes a scope input; `research-methodology.md:17-20` starts at *"Clarify the goal (1–2 questions max; skip on 'just research it')"* and *"Decompose the topic into 3–5 sub-questions"* — the topic is a given, its edges are not. The decomposition records the downstream cost: sweep "database", then `agent-shape` finds the agent only reviews migrations | Effort spent outside what the later stage needs, and the information that would have bounded it lives in a stage that runs later | structural, both procedures | **teach** → `research-commission-scoping`; **wall** → the commission gate |
| R10 | **Cross-references break, and one-sidedly.** Four `[[wikilinks]]` resolve to no note: `[[plugins]]` in `claude-code-extension-layer.md:8` and `mcp.md:8`, `[[context-budget]]` in `graphify-assessment.md:12`, `[[unified-memory]]` in `temporal-kg-agent-memory.md:8`. Links are frequently one-way — `skill-authoring-eval-methodology.md:10` names three neighbours and none names it back; `graphify-features.md` names `graphify-assessment`, which does not return it | `INDEX.md:3-5` promises *"links to related notes with [[wikilinks]] (Obsidian-compatible)"*. The graph is not the graph the index describes. `/home/user/skills-repo/CLAUDE.md` already names the cause — *"parallel authoring produces one-sided links structurally"* — and attaches no mechanism | 4 dangling; one-sidedness in the majority of pairs checked | **teach** → `knowledge-note-drafting` emits a back-link table; **out of scope** → repairing existing neighbours is a patch a human applies |

### 8.2 · What the baseline did well — leave this alone

The regression zone. Adding a procedure is not free: skills lifted task success from
33.9% to 50.5% overall **and regressed roughly 15% of tasks**, concentrated where the
base model was already competent. Nothing built here re-teaches any of the following,
and a reviewer should treat a future rule that does as noise.

| Already competent | Evidence |
|---|---|
| **Citation hygiene is close to perfect** | 76 `- url:` entries across 26 notes; 75 carry a `fetched:` date. One does not (`skill-authoring-eval-methodology.md`, agentskills.io) |
| **Full bibliographic citation, not just a link** | `ideation-and-idea-selection.md:4-21` — DOI plus *"Diehl & Stroebe 1987, Productivity Loss in Brainstorming Groups, JPSP 53(3) 497-509"* for all six sources |
| **The target output format already exists and works** | the five notes added 2026-08-28 carry a per-row evidence verdict with its effect size, k and N, and a closing section for what could not be established. The format is **theirs**, not a new one. Checked, and one qualification: four of the five use the literal MEASURED/REPEATED token; `design-fixation-and-anchoring.md:76-102` uses a per-row `Verdict` column of `fails`/`backfires` plus a closing *"Claims to distrust"* section marked REPEATED at `:148`. Same discipline, different token — the drafting procedure therefore points at the exemplars rather than fixing a single vocabulary |
| **Contradiction between primary sources is stated, not smoothed** | `ideation-and-idea-selection.md:51-54` — *"The two most-cited primary sources contradict each other on mechanism and almost no secondary account says so"*, with Mullen quoted verbatim |
| **A measurement states its own scope limit** | `subagents.md:81-84` — *"Scope limit, stated by the probe itself: this tests the subagent path only … Do not generalise this to the main session"* |
| **A number is not dressed as a limit when it is a judgement** | `subagents.md:100-104` — *"there is no size cap on an agent body … Keeping it short is a quality argument … Say it that way; do not dress it as a limit"* |
| **Awareness of the exact failure mode already exists** | `ideation-and-idea-selection.md:100-106` — *"Go to the primary source or do not cite."* Awareness is present and is not what is missing. **Do not write another warning** |
| **A moving value is recorded as a pointer, not a number** | `agent-shape/references/knowledge-map.md:43-51` |

### 8.3 · One live verification, run this session — the negative control

To check that the verifier's job can return "supported" and is not a machine for
manufacturing findings, the three documented limits in `subagents.md:88-95` were
checked against the cited source, `code.claude.com/docs/en/sub-agents`, fetched
2026-08-29.

| Claim in the note | Source says | Verdict |
|---|---|---|
| combined descriptions of non-built-in subagents, 15,000 tokens, startup warning | *"When the combined descriptions of your subagents, except the built-in ones, exceed 15,000 tokens, Claude Code shows a warning at startup with the total token count."* | **supported** |
| nesting depth 3; at the limit the `Agent` tool is withheld from all but a fork | *"up to three layers below the main conversation. At the depth limit, Claude Code withholds the `Agent` tool from every subagent except a fork"* | **supported** |
| 20 concurrent subagents | *"when 20 subagents are running in a session, spawning another with the Agent tool fails"* | **supported** |

Three of three hold, quoted. This is what a clean verdict document looks like, and
it is the reason `primary-source-verification` requires a disconfirming read before
a row may be ruled `not-supported`.

### 8.4 · Rows the agents were **not** built from

`agent-assembly` may build only from `teach` and `wall`. Recorded here instead:

- **R5** (`draw`).
- **The single missing `fetched:` date (§8.2).** One in 76. A rule about it would be
  a procedure aimed at a thing already done 75 times out of 76 — the regression zone
  precisely. Not written.
- **Open question, no row behind it:** whether `status:` should gain a `draft` value
  in the base's vocabulary. This spec avoids the question — drafts live under
  `docs/research/drafts/` and are not notes — and adds exactly **one** frontmatter
  key to the base, `verified_by:`. That is additive, every existing note stays valid
  without it, and it is flagged here as a change to the base's shape that needs the
  owner's assent rather than made quietly.
- **Open question:** whether a claim ruled `not-supported` should be deleted from the
  promoted note or retained with the verdict attached. `note-promotion` retains and
  marks, on the ground that a deleted claim is silently re-researchable and this base
  has an unusually strong habit of recording what it could not establish (§8.2). No
  measurement supports either choice.
- **Open question:** the promotion gate makes extending an existing note a
  human-applied patch. Friction gets skipped, and the reuse-first rule the base
  depends on lives on the other side of that friction. Named, not solved. Candidate
  backlog item.

### 8.5 · The baseline task prompt — verbatim, saved, **unrun**

> You are working in /home/user/hello-world. Do this job end to end and use whatever approach you think best.
>
> This project is about to build an agent whose job is: "it reviews a database migration and produces a findings list at file:line with a verdict." Nobody here has any evidence about database migration review — the knowledge base at /home/user/skills-repo/knowledge/notes/ has 26 notes and none of them touches the topic.
>
> Go and get the domain knowledge that agent will need. Write it up as a knowledge note in the style of that directory, and save it to <scratch path> — do not write anything into /home/user/skills-repo or /home/user/hello-world.
>
> In your final message give me (a) the path, (b) how many distinct claims your note makes, and (c) a short rationale: what you searched for, what you read and in what order, how you decided what went in and what stayed out, and how confident you are in each claim.
>
> Work alone. Do not ask me questions; make your own calls and record them.

Dispatch to **at least two** independent parallel runs that cannot see each other,
then re-derive §8.1 against their outputs. Until then every row in §8.1 is marked
**`observed from the existing base, not from dispatched runs`**. The rows most in
need of that check are R2 and R3, which are the ones a fresh run might well not
reproduce — the base's oldest notes predate the discipline the 2026-08-28 batch
introduced, and a run today might carry it unprompted.

---

## 9 · Placement table (`agent-assembly` step 1)

| Spec item | Tier | Where |
|---|---|---|
| what each agent is; its boundary and the mechanism; the map of its functions | 0 · agent body | `.claude/agents/domain-researcher.md`, `.claude/agents/primary-source-verifier.md` |
| scope contract from the candidate sentence; extend-or-author | 1 · `skills:` | `.claude/skills/research-commission-scoping/` |
| per-claim evidence rows with MEASURED/REPEATED | 1 · `skills:` | `.claude/skills/claim-evidence-extraction/` |
| the note in the base's shape; back-links | 1 · `skills:` | `.claude/skills/knowledge-note-drafting/` |
| per-claim verdicts against the cited source | 1 · `skills:` | `.claude/skills/primary-source-verification/` |
| what may be promoted, and the `verified_by` record | 1 · `skills:` | `.claude/skills/note-promotion/` |
| doc-driven and checkpoint rules binding every agent here | 2 · `CLAUDE.md` | already there, unchanged |
| the base's format, with `file:line` exemplars | 3 · `references/` | `.claude/skills/knowledge-note-drafting/references/base-format.md` |
| what makes a claim MEASURED rather than REPEATED | 3 · `references/` | `.claude/skills/claim-evidence-extraction/references/verdict-rules.md` |
| the search protocol; reading one long source | 3 · reused, not copied | `/home/user/skills-repo/.claude/skills/literature-review/SKILL.md` §2–5; `.../deep-reading/SKILL.md` §1–5 |
| the commission template; the note template; the verdict template | 4 · `assets/` | inside the owning skills |
| the commission gate | 5 · hook | `docs/hook-proposal-research-commission.md` — **a human installs it** |
| the promotion gate | 5 · hook | `docs/hook-proposal-note-promotion.md` — **a human installs it** |
| every construction rule, threshold and limit | — | `.claude/validate/agents.py`, and **nowhere else** |

Nothing is placed in `.claude/rules/`: measured by canary probe, scoped and
unscoped, it does not reach a subagent.

---

## 10 · What this build did not do

- **No eval suite exists and no independent tester was dispatched.** This session
  held no `Agent` tool. `docs/domain-research-tester-brief.md` is staged for a fresh
  subagent; `agent-assembly` step 6 is **unmet**, and these two agents are not
  finished until it is met.
- **The validator was not executed.** No shell. Every rule in
  `.claude/validate/agents.py` was traced by hand against the files written; that is
  a reading, not a run, and it is reported as one.
- **Neither hook is installed** (§6). The walls in the table are proposals.
- **Nothing was written into `/home/user/skills-repo/knowledge/notes/`.** The one
  fact verified live during this session — §8.3 — belongs in `subagents.md`, which
  already exists and which this builder may not edit. It is recorded here and in the
  report instead, and the patch is named in the tester brief.
