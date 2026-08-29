# Agent spec — `llm-component-architect`

Built to `.claude/skills/agent-assembly/assets/template/` **1.0.0**
(`assets/template/VERSION`). The first agent in this repo built to the standard;
every other row in `docs/agent-registry.md` reads `pre-template`.

Date: 2026-08-29. Author: the `agent-builder` loop, running as a leaf
(`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`, `Agent` withheld).

---

## 0 · The reuse gate — where I looked, and the ruling

### Where I looked

| Searched | How | Result |
|---|---|---|
| `.claude/agents/*.md` | `Glob`; read `architect.md` and `architect-rebuild.md` **in full** | two architects, neither mentions a model call |
| `/home/user/skills-repo/.claude/skills/*/SKILL.md` | `Glob` (84 talents) + `Grep '^description:'` across all | 17 talents touch this domain; **none owns the job** |
| `/home/user/skills-repo/.claude/agents/` | `Glob` | one agent exists: `rag-pipeline-reviewer` |
| library talents read in frontmatter | `cost-aware-model-routing`, `hybrid-parse-escalation`, `abstention-threshold-design`, `mlops-production-review`, `llm-call-ledger`, `agent-architecture-audit`, `agent-harness-construction`, `skill-scout` | each owns **one procedure inside** the job |
| `/home/user/skills-repo/knowledge/notes/` | `Glob` + `Grep` on domain terms | see §1b |

### What the neighbours actually own

- **`architect`** — "choosing a stack, datastore, boundary, protocol, tenancy or
  auth model; carving the system into parts and defending the seams; reviewing an
  existing design, diff or layer against what it claims to be". Three preloaded
  skills, at the cap. **Nothing in its file, its three skills' names, or its
  knowledge section mentions a model call, a token, latency, money or a prompt.**
- **`architect-rebuild`** — the same three functions renamed and scoped to
  `/home/user/scio/`. Its knowledge section points at `as-built/`, the ADR
  register and `architecture-evidence.md`. Same silence on model calls.
- **`rag-pipeline-reviewer`** (library) — retrieval quality, chunking, embeddings,
  RAGAS. A genuine overlap on *one* sub-question and a NOT-clause target.
- The 17 library talents own **implementations**: how to route on price
  (`cost-aware-model-routing`), how to record a call (`llm-call-ledger`), how to
  escalate from a parser (`hybrid-parse-escalation`), where an abstention cut goes
  (`abstention-threshold-design`). None of them enumerates the calls in a system
  and rules on them; each assumes the call is already identified and the question
  already framed.

### Ruling: **author** — and here is the part that is honestly `extend`

The dishonest version of this ruling is "a third architect, because AI is
different." Here is the honest breakdown.

**What is genuinely a *job* difference.** The unit of work is different. Both
existing architects work in units of *parts and the seams between them*. This
agent works in units of *one model call*: does it belong here, what does it cost,
what happens when it fails, what may enter it, and who believes its output. A
seam table cannot express any of those five columns, and a call table cannot
express a seam. The baseline in §3 is the evidence: two independent reviews of
this repo found stack, tenancy and persistence failures **and** model-call
failures in the same pass, and the architecture record covered the first class and
missed the second — ten recorded rows of it.

**What is honestly a *diet and knowledge* difference.** The three functions below
are recognisably decide / enumerate / review, which is the shape both existing
architects already have. Much of what makes this agent different is *which
artefacts it reads* and *which failure tables it carries*. I am not going to
dress that up as novel procedure.

**Why it is nevertheless a separate agent and not an extension of `architect`,
with mechanisms rather than preferences:**

1. `architect` already preloads three skills. A fourth is refused by
   `.claude/validate/agents.py:104-108` — the cap is enforced, not advisory. So
   "add a model-call procedure to `architect`" is **mechanically rejected**.
2. The alternative extension — a `references/` file under one of `architect`'s
   three skills — requires editing an existing `SKILL.md` to point at it. I cannot
   write any file under `.claude/` that already exists, so that is a human-applied
   proposal, not a build.
3. `extend` is therefore **structurally unavailable to me in either form**. It is
   recorded here as the runner-up, with its blocker named, so that a human who
   disagrees with `author` has the alternative written down rather than implied.

**What `author` costs, stated up front:** a third agent whose name a caller could
read as a sibling of the existing pair. §2 of this spec is entirely about paying
that cost down, because the existing pair already collides at Jaccard **0.195**
with no NOT-clause in either direction — an open defect, eval case T5
(`docs/review-agent-builder-loop.md:56-71`). A third collision would make it
worse, and this spec ships a proposal to repair the original pair too
(`docs/proposal-architect-not-clause-repair.md`).

---

## 1 · The job, in one sentence and one artefact

> It enumerates every model call in a system — built or proposed — and rules on
> each one: whether it should exist, what it costs in tokens, latency and money,
> what the system does when it is wrong, slow or unavailable, what untrusted text
> reaches its prompt, and who judges its output — emitting a call table at
> `docs/model-calls/NNN-slug.md` with one row per call and an explicit
> `not checkable here` for anything that needs a key or a running system.

**The artefact:** `docs/model-calls/NNN-slug.md`. Sections A–D:

- **A · the inventory** — one row per model call, each with the `file:line` or the
  proposal paragraph it came from, and the verbatim query that found it
- **B · the rulings** — five per call (placement, budget, degradation, prompt
  intake, output judgement)
- **C · the calls that should not be model calls** — with the deterministic
  mechanism named and the measured or estimated saving
- **D · `not checkable here`** — with the exact command handed to the caller

### 1b · What the base knows — ruling: `thin`

**The grep.** `Grep 'latency|fallback|degrad|prompt injection|token cost|per-token|eval|deterministic'`
over `/home/user/skills-repo/knowledge/notes/` → 60 hits across 21 of 26 files.
`Grep 'MEASURED|REPEATED|status:|verified_by'` → 63 hits across all 26.

**What reading them showed.** The hits are overwhelmingly about *authoring agents*,
not about *architecting systems that contain a model*.

| Note | What it carries for this domain | Verdict |
|---|---|---|
| `architecture-evidence.md` | six MEASURED rows — all post-mortem empiricism about distributed systems. **Zero rows about a model call.** Its own §"The gap" says it is "strong on death and empty on design" and lists the entire stability pattern language (circuit breaker, bulkhead, timeout), static stability and blast radius as **absent and recalled, not sourced** | usable for the failure-mode discipline; silent on this domain |
| `effective-agents-anthropic.md` | the workflow-vs-agent distinction; six patterns with fit tests; *"this might mean not building agentic systems at all"*; stopping conditions; poka-yoke on tool arguments | **practice, not measurement** — the note states its own basis as "work with dozens of teams", and labels its headline claim REPEATED |
| `managed-agents-architecture.md` | one transferable lesson: *"the tokens are never reachable from the sandbox where Claude's generated code runs"* — available capability, absent secret | documentation transcription of a blog post |
| `api-agent-loop.md` | the loop mechanics, `stop_reason`, parallel tool results | documentation transcription; rings 4–5 were never retrieved |
| `mcp.md`, `claude-code-extension-layer.md`, `subagents.md` | Claude Code extension mechanics | wrong subject; `subagents.md` is the base's only `partly-verified` note and it is about subagents, not systems |

**Ruling: `thin`** — the domain appears, but as documentation and practice, with
**no per-claim MEASURED verdict anywhere on model latency, model cost, model
failure behaviour, evaluation-boundary placement or prompt data intake.**

**Consequence, applied:** every step in the three procedures that leans on the base
rather than on §3's baseline is tagged `unevidenced` in the skill itself. A
documentation transcription is not laundered into a measured finding.

**No commission is raised**, because the verdict is `thin` and not `absent`, and
because this agent's content comes from §3's recorded runs rather than from the
base. A `domain-researcher` sweep on *"measured evidence for AI-system
architecture — latency and cost budgets for model calls, degradation design,
evaluation-boundary placement"* is recorded in §9 as a **recommended future
commission**, not as an input this build needs. Marking it `commission` here would
falsely block assembly for material the agent does not consume.

---

## 2 · The context diet

This agent **judges**. Four of its five rulings are checks against artefacts, and
per `llm-idea-generation.md` an evaluator is **saturated**: novelty scored 6.14/10
without retrieval and 2.38/10 with it, a 2.6× inflation when the existing reality
is absent. So it reads the system.

One sliver is generative — "name the deterministic alternative" — and the
generator rule points the other way: seeding with the existing solution measured
**worse** than nothing (0.403–0.428 vs base 0.377), and fixation on a
*self-generated* first concept measured 0.32 against 0.24 for a provided example.

**This does not make two agents.** The alternative is drawn from a bounded, known
set (stored value, lookup table, parser or grammar, rules engine, deterministic
gate, cache, human), not from open ideation; what is wanted is coverage, not
novelty. The starve rule is handled **as an ordering step inside the procedure**,
not as a diet split: `model-call-placement` step 2 requires the candidate
deterministic mechanism to be written down **before** the design's justification
for the model call is read. That is the same derive-then-look discipline the SEI
omission finding supports (57 risks of omission vs 25 of commission, kappa .82),
and it is a step that ends in a table row, not a warning.

**Must see**

- the system under review: source at `file:line`, prompt templates, ADRs,
  `ARCHITECTURE.md`, `SECURITY.md`, `COSTS.md`, `STRATEGY.md`/`PRD.md` for what the
  system *claims* about cost and quality
- the review record: `docs/REVIEW-*.md`, `docs/BACKLOG.md` — what has already been
  found, so it does not re-report it as new
- live price, context-window and rate-limit pages, fetched at the time

**Must not see**

- the design's stated reason for a model call, **before** step 2 has written the
  deterministic candidate down (ordering, enforced by the step's artefact)
- its own earlier call table for the same system. Re-reading its own verdict is
  self-critique with no external signal — measured worse on every model and every
  benchmark (GPT-4 GSM8K 95.5 → 91.5 → 89.0). The create-only gate makes
  superseding structural rather than optional.
- a price recalled from memory. Structurally unavailable: it holds `WebFetch` and
  no `WebSearch`, so it can open a URL a document names and cannot go find a page
  that agrees with a number it has already written.

---

## 3 · The split test

| Rule | Fires? | Verdict |
|---|---|---|
| 1 · opposite diets | no — one evaluator diet, one ordering step inside it (§2) | one agent |
| 2 · independent quarry | **yes, against `architect`** — §4's baseline shows the quarry is disjoint: the same two reviews found stack/tenancy/persistence failures *and* model-call failures, and the architecture record covered the first and missed the second | separate from `architect` |
| 3 · more than three functions | no — exactly three, each with baseline rows behind it | one agent |
| 4 · author ≠ tester | n/a to the roster; binds the build (§8) | tester is a fresh subagent |

**Roster:** one agent, three preloaded procedures.

---

## 4 · The baseline — route 2, recorded real runs

### Which route, and why

`agent-baseline` §2b, **route 2: recorded real runs.** Route 1 (ask the session
above to dispatch) was not taken because route 2's material is stronger here and
already exists; route 3 (no baseline) does not apply.

**Why route 2 is strong in this case.** This repository *is* a system with a model
as its central component, and it carries:

- the architecture record produced by unaided work — `docs/ARCHITECTURE.md`,
  `docs/COSTS.md`, `docs/SECURITY.md`, ADRs 0001–0021
- **two independent reviews written by someone else, recording what that record
  got wrong**, dated 2026-08-21 — eight days before this agent was proposed:
  `docs/REVIEW-2026-08-21.md` and `docs/REVIEW-PRODUCTION-READINESS.md`
- a backlog with measured before/after numbers: `docs/BACKLOG.md`

Nobody constructed any of it to be a baseline, so it cannot have been shaped to
the answer. What it is weaker on: I did not control the task, and it is one
system. Every row below cites a `file:line`.

### The failure table

| # | What they did | Consequence | Reproduced? | Verdict |
|---|---|---|---|---|
| **F1** | A model call on a read path: *"The whole + estimate are recomputed on every GET /intake: ~12s and a real Layer B+C model call per page load"* (`docs/BACKLOG.md:121`, B071) | every wizard page load cost a model call and 12.7 s. After the fix: *"`GET /intake` went from **12.7s to 0.008s** and now makes no model call at all"* (`docs/BACKLOG.md:243-245`); *"answers in **7–16 ms** and makes no model call"* (`:226`) | yes — and the multiplier was found separately: *"The app fetches /intake twice per page load … it doubled the old cost"* (`:125`, B075) | **teach** |
| **F2** | A spend ceiling plumbed and never set: *"`budget_usd` is plumbed and never set … a build estimated $1.05–$2.51 spent **$2.69** and nothing intervened"* (`docs/REVIEW-2026-08-21.md:20-33`) | the product's own wedge — "know the cost up front" — is unenforced | yes — restated independently: *"no spend ceiling on any build"*, and missing *"at three levels — the build, the workspace, and the request"* (`docs/REVIEW-PRODUCTION-READINESS.md:220-226`) | **teach** |
| **F3** | The cost signal computed and dropped: `DesignChangeResult.total_cost_usd` *"is returned by the engine and never read by the api"*; the preview build's `finished` event carries it and only four other fields are kept (`docs/REVIEW-2026-08-21.md:36-45`) | *"Billing built on this ledger would undercount the majority of spend"* | yes — recorded as the system's **default** failure class with four confirmed instances (`.claude/agents/architect.md:117-119`) | **teach** |
| **F4** | A 46-minute model job inside one HTTP request: *"no job id, no queue, no cancellation, no resumability"*, and the code's own comment says the intent was written down and unbuilt (`docs/REVIEW-PRODUCTION-READINESS.md:44-49`) | *"the engine keeps burning money on work whose result nobody will receive"*; a restart loses every running build | yes — *"the same finding seen from four sides"* (`:28`) | **teach** |
| **F5** | No degradation design: a dropped connection *"still reads as a failed build"*, and the screen contradicts its own promise one line above (`docs/REVIEW-2026-08-21.md:98-107`) | the user is told a running build failed — hit live in a real session | yes — named again as the cause of the "network error" confusion (`docs/REVIEW-PRODUCTION-READINESS.md:291`) | **teach** |
| **F6** | No rate limit on any model-calling path: *"intake (a model call per message), preview builds, `/design/change` — reachable by an authenticated user in a loop … not merely a DoS surface, it is an **unbounded bill**"* (`docs/REVIEW-PRODUCTION-READINESS.md:196-198`) | the ceiling is absent at the request level as well as the build and tenant levels | yes — F2's third level | **teach** |
| **F7** | Model-authored code trusted with the platform's secrets: `core/sandbox.py:141` starts it with `env={**os.environ, ...}`, so `ANTHROPIC_API_KEY` and a credentialled Postgres URL are one line away (`docs/REVIEW-PRODUCTION-READINESS.md:69-79`) | *"a generated app that merely logs its environment … puts the platform key in a log the user can read"* — graded **blocking** | one review, but the mechanism is named and the fix was accepted (`docs/SECURITY.md:62-64`, B091) | **teach** |
| **F8** | The prompt's *input* side unexamined while its *output* side was gated: *"the build gates constrain the output … but nothing constrains the instruction"* (`docs/REVIEW-PRODUCTION-READINESS.md:205-211`). `docs/SECURITY.md:11` still listed "Prompt injection into the agent. (Phase 2/6)" as a skeleton line; the actual analysis is dated **2026-08-22** — after the review (`docs/SECURITY.md:21`) | the one prompt carrying text across tenants was undocumented until then (`docs/SECURITY.md:36`) | yes — visible from both sides, the skeleton and the review that named it | **teach** |
| **F9** | A control that did not cover the shape it existed to stop: the secret-scan rule *"caught only the legacy `sk-<alnum>` shape, so a real `sk-ant-api03-…` key would have sailed through the one check meant to stop it"* (`docs/BACKLOG.md:250-251`) | the single control on model-authored output was blind to the actual secret | one occurrence, mechanism named | **teach** |
| **F10** | No external measure of model output quality: *"the reveal currently shows '4 of 5 parts work' with no external measure at all"* (`docs/REVIEW-2026-08-21.md:121-125`); *"the estimate model (B077) was calibrated from **two** builds because two is all the data there is"* (`docs/REVIEW-PRODUCTION-READINESS.md:241-244`) | the headline claim rests on a judge with no external signal and n=2; B077 recorded 14–33 min predicted against 46 actual (`docs/BACKLOG.md:127`) | yes — two independent reviews | **teach** |
| **F11** | The evaluation path making real model calls: *"the new `.env` loader made the test suite pick up an operator's key, so `test_api.py` was making REAL model calls — 100 seconds and real money for a unit-test run"* (`docs/BACKLOG.md:251-253`) | the eval boundary leaked into production calls; cost and latency both real | one occurrence, measured | **teach** |
| **F12** | No record of any model call: *"Zero occurrences of `import logging` or `logger.` across 17,000 lines. The engine runs 46-minute jobs costing dollars and emits nothing"* (`docs/REVIEW-PRODUCTION-READINESS.md:232-235`) | no answer to how many builds ran, what they cost, or how long a layer takes — *"every one of those is a business question"* | yes — restated as the reason B077 had n=2 | **teach**, and route the implementation to the library's `llm-call-ledger` |
| **F13** | The document that should carry the cost model is four headings and "(Phase 2)" placeholders — `docs/COSTS.md:1-13`, unchanged on 2026-08-29, eight days after *"for a product whose wedge is know the cost up front, cost is currently the least-enforced thing in the system"* (`docs/REVIEW-PRODUCTION-READINESS.md:226-227`) | the artefact a ruling would be checked against does not exist; the consideration was raised and never landed | yes — the placeholder and the review both stand today | **teach** (artefact discipline; belongs in the body, not a procedure) |
| **F14** | The model call fused with the deterministic gates around it: `build_package` is **226 lines** holding *"the attempt loop, the snapshot/rollback, five gates, the critique call, remainder collection and persistence — six responsibilities in one scope. That is where the last three bugs lived"* (`docs/REVIEW-2026-08-21.md:151-158`) | the model call has no boundary of its own, so its failure cannot be isolated or substituted | one review, with three bugs attributed | **teach** |

### Wall rows

| # | What prose will not hold | Mechanism |
|---|---|---|
| **W1** | Quietly reconciling `SECURITY.md`, `COSTS.md` or `ARCHITECTURE.md` to a ruling it just made — which would erase the discrepancy the ruling exists to find. F8 and F13 are exactly the honest gaps that would be tidied away | **`Edit` absent**, and the write gate denies overwriting any existing path |
| **W2** | "Fixing" the design instead of ruling on it | write gate scoped to `docs/`, **plus `Bash` absent** so it cannot be walked around with `echo >` |
| **W3** | Going to find a price that supports an estimate already written | **`WebSearch` absent, `WebFetch` present** |
| **W4** | Claiming to have run, measured or tested something | **`Bash` and `Agent` both absent** — execution is structurally unavailable, so `not checkable here` is the only expressible answer |

### §5 · What the baseline did well — the leave-alone list

Anything here is a place where a procedure can only add noise. SkillsBench measured
skills lifting task success 33.9% → 50.5% overall **with roughly 15% of tasks
regressing, concentrated where the base was already competent.** These are that zone.

1. **The deterministic-gate instinct is already strong.** *"The gates are real and
   they refuse … code cannot be talked out of its opinion"*
   (`docs/SECURITY.md:56-60`, `docs/REVIEW-2026-08-21.md:201-204`). So
   `model-call-placement` must **not** teach "prefer deterministic code" — that
   lesson is learned. F1 was a *coverage* failure, not an instinct failure: nobody
   enumerated which paths made a call. The procedure teaches the **enumeration**.
2. **`unjudged` as a first-class concept** — *"a criterion nobody could check rides
   along instead of being dropped"*, called *"the codebase's best instinct"*
   (`docs/REVIEW-2026-08-21.md:205-207`). `model-trust-boundary` **reuses this
   repo's own word** rather than inventing a competing one.
3. **The deterministic cost estimate** — B046, *"Cost estimate (deterministic, from
   plan + library hits)"*, done (`docs/BACKLOG.md:96`). Left alone; only its
   *time* half was miscalibrated (B077), which is F10.
4. **Tenancy** — *"genuinely well built … 404-not-403 so an id cannot be probed"*
   (`docs/REVIEW-PRODUCTION-READINESS.md:183-186`). Not this agent's subject and
   not to be re-covered. It is `architect`'s, and the NOT-clause says so.
5. **Fencing and structured replies** — controls 1 and 2 in `docs/SECURITY.md:39-55`
   are well reasoned, including the honest line *"it does not make one impossible,
   and it should never be described as if it did."* `model-trust-boundary` adds the
   **enumeration and the worst-realistic-outcome column**, not the controls.
6. **Path traversal guarding, the origin check on the marking bridge, the secret
   scan's existence** (`docs/REVIEW-PRODUCTION-READINESS.md:118-125`). Left alone —
   except F9, which is about one rule's coverage, not the control's presence.

---

## 5 · The tool surface

| Tool | The job that needs it | Argument shape that makes the likely misuse unexpressible |
|---|---|---|
| `Read` | open source at `file:line`, ADRs, prompt templates, the review record | **absolute paths only**, per Anthropic's own SWE-bench result: requiring absolute rather than relative filepaths *"eliminated"* a class of model error. The procedures name absolute paths throughout |
| `Grep` | **enumerate** every model call before ruling on any — the F1 failure class | the enumeration step's artefact is the **verbatim query plus its count**, so a row without a re-runnable query has nowhere to go in the table |
| `Glob` | list candidate files before reading them, so the inventory is derived and not sampled | same — the pattern is recorded in section A |
| `WebFetch` | read a live price, context window or rate limit at the time of the ruling | the URL must come from a file that names it (`shared/live-sources.md`, `platform.claude.com/docs/en/pricing.md`). A number with no `fetched:` date has no cell in the budget table |
| `Write` | emit the call table | the path is `docs/model-calls/NNN-slug.md` and the gate is **create-only**, so "revise the old table" is unexpressible — you supersede |

**Absent, and what each buys** (`04-wall.md`'s ladder, rung 1):

| Absent | Buys |
|---|---|
| `Bash` | nothing executes; the write gate cannot be walked around with `echo >`; **and** every claim needing a run must become a `not checkable here` row (W4) |
| `Edit` | creates but cannot rewrite (W1) — it cannot reconcile a document to its own conclusion |
| `WebSearch` | it can open a URL a document names; it cannot go find a source that agrees (W3) |
| `Agent` | cannot delegate its judgement or reach past its own tool list — and with nesting off it would not get one anyway |
| `TodoWrite`, `Skill` | not load-bearing; a smaller surface is a smaller blast radius |

**`tools: Read, Grep, Glob, WebFetch, Write`**

**Stopping condition.** Not autonomous; one pass per dispatch. Finished when every
row in section A carries five rulings or an explicit `not checkable here`, and the
file exists at its path. **No second self-review pass** — reviewing its own output
without new evidence measured worse (95.5 → 91.5 → 89.0); the remedy is an
external check, not another pass.

**What the surface makes impossible:** running anything, editing anything,
delegating anything, and writing anywhere but a new file under `docs/`.

### 5b · What it must be able to execute to prove itself

**Answered in one line:** *it must be able to fetch one moving number — a price, a
context window, a rate limit — and nothing else; every claim that needs execution
is recorded as `not checkable here` with the exact command handed to its caller.*

**Route taken: route 1 for the ruling itself (its output is judged by reading),
plus route 2 for two named classes** — written into the procedures as steps, not
as apologies:

| Class | Handed up as |
|---|---|
| an exact token count for a prompt | the `count_tokens` call or `ant` CLI command, printed in section D with the file it would run against — `model-call-budget` step 4 |
| whether a real model resists a real injection | the experiment, printed in section D. `docs/SECURITY.md:73-76` already states this correctly: *"No test proves a real model resists a real injection: that needs keys and a measured experiment, not an assertion"* — `model-trust-boundary` step 5 |

**What that costs, stated:** the caller is now part of this agent's procedure for
those rows. Section D exists so that cost is visible in the artefact instead of
being absorbed silently. This is the failure `agent-fitness-review` hit — a tool
surface fixed before anyone asked what the proving stage needed — and the answer
here is that the proving stage needs *reading*, so the surface is right.

---

## 6 · The wall

| Must be impossible | Mechanism | Rung |
|---|---|---|
| running anything | `Bash` absent | 1 |
| rewriting a document, including its own | `Edit` absent | 1 |
| corroborating a number it already wrote | `WebSearch` absent | 1 |
| delegating judgement | `Agent` absent | 1 |
| writing outside `docs/` | `PreToolUse` on `^Write$` | 2 |
| overwriting anything that exists | the same hook, create-only | 2 |

**The hook, and an honest compromise.** The installed
`.claude/hooks/architect-rebuild-write-gate.sh` already implements exactly this
gate — allow `Write` only to a **new** file under `<repo>/docs/`, fail closed on an
unparseable payload, on a missing `python3`, on traversal, on a prefix lookalike,
and on the `docs/` directory itself. Its name says `architect-rebuild`; its logic
is agent-agnostic.

I reference it, for a reason that is mechanical rather than aesthetic: I cannot
write `.claude/hooks/`, and `.claude/validate/agents.py:112-115` **fails** an agent
whose `hooks:` command does not exist. So naming a not-yet-installed hook would
fail the checker, and naming no hook would ship an agent with **no path wall at
all** while its body claimed one — the `cal-l2-currency` defect class exactly.

**The coupling is a real cost and is named in the agent's own §2:** a human editing
that script for `architect-rebuild` silently changes this agent's wall.
`docs/hook-proposal-llm-component-architect-write-gate.md` carries a decoupled copy
under its own name, with the control table, for a human to install and swap in.

**What the wall does not cover** — stated in the agent's §2, in its own words: a
path gate enforces *where*, never *what*. A ruling inferred from a function's name
is indistinguishable, in the finished table, from one read at `file:line`. The
`file:line` in each row is the only thing standing between them.

---

## 7 · Composition

- **Delegated:** nothing. `Agent` is absent; it is a leaf.
- **Dispatched by:** a session, or `architect` after it has decided the parts.
- **Pattern:** producer → independent verifier. Its table is a document another
  agent or a human checks. Nothing converses — round-table measured 0 of 62
  comparisons significant across 12 interventions and 45 conditions.
- **Handoff to `architect`:** a pipeline in one direction only. `architect` decides
  the parts; this agent rules the calls inside them. Neither reads the other's
  in-flight work.
- **Its test:** a fresh subagent that did not author it (§8). Not runnable here.

---

## 7b · Bill of materials

**No open `commission` row.** Every row is `exists` with a path I opened, or
`not needed` with a reason.

| Input | Kind | State | Route / reason |
|---|---|---|---|
| `.claude/agents/architect.md` | agent | `exists` | read in full for the reuse gate and the description test |
| `.claude/agents/architect-rebuild.md` | agent | `exists` | read in full, same |
| `.claude/skills/agent-assembly/assets/template/INDEX.md`, `00`, `01`, `02`, `03`, `04`, `05`, `LIMITS.md`, `VERSION` | template | `exists` | all nine opened; built to **1.0.0** |
| `.claude/validate/agents.py` | checker | `exists` | read in full; its constraints shaped the wall and the frontmatter |
| `.claude/hooks/architect-rebuild-write-gate.sh` | wall (interim) | `exists`, executable | referenced; coupling named in §6 |
| decoupled write gate under its own name | wall | `exists` — **written by this build** | `docs/hook-proposal-llm-component-architect-write-gate.md`, human installs |
| `.claude/skills/model-call-placement/` | skill | `exists` — written by this build | preload 1 |
| `.claude/skills/model-call-budget/` | skill | `exists` — written by this build | preload 2 |
| `.claude/skills/model-trust-boundary/` | skill | `exists` — written by this build | preload 3 |
| the baseline failure table | spec | `exists` | §4 above, 14 rows, every one at a `file:line` in this repo |
| `docs/REVIEW-2026-08-21.md`, `docs/REVIEW-PRODUCTION-READINESS.md`, `docs/BACKLOG.md`, `docs/SECURITY.md`, `docs/COSTS.md` | recorded runs | `exists` | all read; cited by line |
| `/home/user/skills-repo/knowledge/notes/architecture-evidence.md` | note | `exists`, `thin` here | pointed at for the failure-mode discipline; every step leaning on it tagged `unevidenced` |
| `.../effective-agents-anthropic.md` | note | `exists`, practice-not-measured | the workflow-vs-agent distinction and the stopping-condition rule; tagged `unevidenced` |
| `.../managed-agents-architecture.md` | note | `exists` | the credential-separation lesson for F7 |
| `.../llm-idea-generation.md` | note | `exists` | settled the diet in §2 |
| live price / context window / rate limit | moving value | `exists` as a **pointer** | `platform.claude.com/docs/en/pricing.md` and the models overview, via `shared/live-sources.md`. Never transcribed into a procedure |
| bundled `claude-api` skill | skill | **`not needed`** | (a) it cannot be preloaded — `agents.py:109-111` requires a repo-local `.claude/skills/<name>/SKILL.md`; (b) its stable copy is outside the repo and its session copy is under a version- and hash-pinned `/tmp` path that will not survive the session; (c) what this agent needs from it is the **URL list**, which is read live anyway. Recorded as an optional local cache in `model-call-budget`, not as a dependency |
| `rag-pipeline-reviewer` (library agent) | agent | **`not needed`** | it owns retrieval quality; named in a NOT-clause without promising local routing, since it is not in this repo's roster |
| `cost-aware-model-routing`, `llm-call-ledger`, `hybrid-parse-escalation`, `abstention-threshold-design`, `mlops-production-review` | library skills | **`not needed` as preloads** | each owns an implementation *downstream* of a ruling. Named as routing targets in the procedures' "When this does not apply" |
| registry row | registry | `exists` — added by this build | `docs/agent-registry.md`, status `withheld` |
| tester brief | eval | `exists` — written by this build | `docs/llm-component-architect-tester-brief.md` |
| **eval suite run by a fresh tester** | eval | **`not needed` for assembly to start; UNMET for release** | `Agent` is withheld at runtime. `agent-assembly` §6 is unmet. The agent is staged, not shipped, and the registry row says `withheld` for exactly this reason — the same status and the same reason as `agent-fitness-review` |

---

## 8 · Frontmatter decisions, including the nine unset fields

| Field | Value | Why |
|---|---|---|
| `name` | `llm-component-architect` | names the job by its unit — a model as a component of a system. Deliberately **not** prefixed `architect-`, which would read as a third sibling of the colliding pair |
| `description` | see the agent file | §2 of this spec |
| `tools` | `Read, Grep, Glob, WebFetch, Write` | §5 |
| `model` | `inherit` | **We have no measurement here.** The one sentence: the job is judgement under ambiguity where a wrong ruling is expensive, which argues for pinning up — but pinning would freeze it against a caller's deliberate upgrade, and `inherit` keeps it comparable with the other eight agents, all of which inherit. Accepted cost: it is not a reproducible eval baseline |
| `skills` | the three below | §3 |
| `hooks` | `^Write$` → `architect-rebuild-write-gate.sh` | §6, with the coupling named |

The nine, each ruled rather than ignored:

| Field | Unset because |
|---|---|
| `disallowedTools` | the `tools:` allow-list is explicit; a subtractive list on top would be a second place for the surface to rot |
| `permissionMode` | it never runs unattended, and its only write is already gated at a rung above permissions |
| `maxTurns` | no loop is plausible — one pass, no self-review, stopping condition in §5. A cap would truncate a long enumeration into a partial table that reads as complete |
| `mcpServers` | it needs no live server; its one live read is a documented URL over `WebFetch` |
| `memory` | accumulating across runs would let a stale price or a superseded ruling survive into a new table, and it breaks reproducibility |
| `background` | the caller must block: the table is the answer. And a background run gets a further reduced built-in tool set **whether inherited or listed**, which could silently remove `WebFetch` and leave the budget rulings unsourced |
| `effort` | the job is neither trivially mechanical nor uniformly hard; the default is right and we have no measurement saying otherwise |
| `isolation: worktree` | it writes one new file under `docs/`; there is nothing to collide with |
| `color` | cosmetic |

---

## 9 · Open questions — things with no baseline row behind them

Per `agent-baseline`'s handover rule, these are **not** in the agent.

1. **Whether the placement ruling generalises beyond a coverage failure.** F1 is a
   real, measured placement row (12.7 s → 0.008 s), but it is a *coverage* failure —
   nobody had enumerated the calls. This repo's instinct for "code beats a model"
   is already good (leave-alone item 1), so this baseline cannot tell whether the
   procedure helps a team whose instinct is worse. A second baseline on a different
   codebase would settle it.
2. **A `domain-researcher` sweep on measured AI-system-architecture evidence.**
   Recommended, not commissioned (§1b). Scoping sentence: *"measured evidence for
   latency and cost budgets on model calls, degradation design when a model is
   wrong, slow or unavailable, and where the evaluation boundary goes."* Nothing in
   this build consumes it; it would upgrade §1b from `thin`.
3. **Whether three preloads beat two.** `model-call-budget` and
   `model-trust-boundary` have the densest baseline support (F2–F13);
   `model-call-placement` rests on F1 and F14. A stage-ablation would say. We have
   not run one, and this project's only A/B returned **null** on n=1.
4. **Latency numbers for model calls have no source in the base.** The budget
   procedure derives latency from the system's own recorded runs (46 min, 12.7 s,
   7–16 ms) and from live rate-limit pages, and marks any general claim
   `unevidenced`. There is no measured note to cite.
5. **The T5 collision.** Repairing the existing `architect` × `architect-rebuild`
   pair requires editing two files that exist. Proposed at
   `docs/proposal-architect-not-clause-repair.md`; a human applies it.

---

## 10 · What is unmet

- **`agent-assembly` §6 — the eval suite, run by a subagent that did not author
  this.** Unmet. `Agent` is withheld at runtime. The brief is written; the run is
  owed. The registry row reads `withheld`, not `provisional`.
- **`agent-assembly` §6b — judge calibration** against
  `.claude/validate/calibration/`. Unmet, and it cannot precede a test that has not
  run. The brief names which specimen goes with which class.
- **`agent-assembly` §0b / §5 — `python3 .claude/validate/agents.py`.** I hold no
  shell. Handed up per part; see the report.
- **The commit.** `CLAUDE.md`'s definition of done includes committed. No `Bash`.
