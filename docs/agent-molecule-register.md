# The agent molecule register

**What this is.** Every part an agent in this repository is made of, and for each part
four columns: what it is · what Anthropic requires · what we have measured · what we do
anyway with no evidence behind it.

**Why the fourth column is the deliverable.** It is the research agenda. A row with a full
fourth column and an empty third is a practice we invented and then followed eight times
without checking. There are more of those than anyone would guess.

Compiled 2026-08-29 by reading, not by asking: the eight agents in `.claude/agents/`, the
22 rules in `.claude/validate/agents.py` with their provenance tags, and the knowledge
base at `/home/user/skills-repo/knowledge/notes/`. Every count in this document came from
a command; none was recalled.

**Provenance tags** carry through from the validator:
`[A]` Anthropic's skills guide · `[B]` the subagents documentation · `[C]` the skills
documentation · `[M]` measured in this project.

---

## Part 1 · Frontmatter — 15 fields, and we use 6

| Field | Used | Anthropic requires | We have measured | Opinion, unbacked |
|---|---|---|---|---|
| `name` | 8/8 | required; kebab-case `[A]`; "claude"/"anthropic" reserved `[A]` | — | that it should read as a job title rather than a role |
| `description` | 8/8 | required; **drives delegation** `[B]`; ≤1024 chars `[A]`; no `<` `>` — a prompt-injection restriction `[A]`; must carry what **and** when `[A]` | nothing agent-specific | **opening with "Use when"** · **NOT-clauses routing to siblings** · **naming the artefact it emits** · that overlap between two descriptions is a defect |
| `tools` | 8/8 | optional; **omitted inherits every tool available to subagents** `[B]` | 68/68 agents in an external library set it explicitly `[M]` | that the surface should be minimal · that removing a tool is a stronger wall than a hook |
| `disallowedTools` | **0/8** | optional `[B]` | — | **never considered** — no decision recorded either way |
| `model` | 8/8 | default `inherit`; `sonnet`/`opus`/`haiku`/`fable`/full id `[B]` | **nothing at all** — zero coverage in the base | `inherit` on all eight, chosen by copying |
| `permissionMode` | **0/8** | optional `[B]` | — | **never considered** |
| `maxTurns` | **0/8** | optional; at the limit the run returns partial output and is resumable `[B]` | — | **never considered** |
| `skills` | 8/8 | preloads full content `[B]`; cannot preload `disable-model-invocation` skills `[B]` | 1–3 modules ≈ **+19.0pp**, 4+ ≈ **+10.1pp** `[M]`; compaction re-attaches at 5,000 each against a 25,000 shared budget `[M]` | that a fourth function means two agents — a reading of the same measurement, not the measurement |
| `mcpServers` | **0/8** | optional `[B]` | — | **never considered** |
| `hooks` | 8/8 | `PreToolUse` runs before every permission check `[B]` | matcher is a **substring** search, so `Write` matches `TodoWrite` `[M]`; **hooks do not load in a non-interactive session** `[M]` | that a wall must be a hook and never a sentence — measured for *prose warnings*, never for hooks specifically |
| `memory` | **0/8** | `user`/`project`/`local`; preload is first 200 lines or 25 KB `[B]` | — | **never considered** |
| `background` | **0/8** | reduced built-in tool set; `Agent` not in it `[B]`; removal applies **whether inherited or listed** `[B]` | — | **never considered** |
| `effort` | **0/8** | optional `[B]` | — | **never considered** |
| `isolation` | **0/8** | `worktree` `[B]` | — | **never considered** |
| `color` | **0/8** | optional `[B]` | — | **never considered** |

**Nine of fifteen fields have never been used by any agent here, and not one of those
nine has a recorded decision against it.** That is not restraint; it is absence. The
register cannot tell the difference between "we ruled it out" and "nobody thought of it",
and neither can anyone else, because nothing was written down.

### The sharpest row

`model:` — **eight agents set it, the knowledge base says nothing about it whatsoever.**
Every one reads `inherit` because the first one did. No cost, capability or latency
argument exists anywhere in the repo. It is the purest instance of the pattern this
register exists to expose.

---

## Part 2 · The description, measured against our own practice

All eight are well inside the documented limits, so the mechanical column is not where
the risk is.

| Agent | Chars | Opens with | NOT-clause |
|---|---|---|---|
| `agent-fitness-review` | 932 | Use when | yes |
| `domain-researcher` | 911 | Use when | yes |
| `primary-source-verifier` | 844 | Use when | yes |
| `architect-rebuild` | 840 | Use when | yes |
| `rebuild-prospector` | 666 | Use to | yes |
| `rebuild-adjudicator` | 612 | Use to | yes |
| `agent-builder` | 595 | Use when | **no** |
| `architect` | 477 | Use for | **no** |

Range 477–932 against a 1024 cap. Six of eight carry NOT-clauses; two do not, and both are
older. **No row anywhere says what a good length is, whether "Use when" outperforms
anything else, or whether a NOT-clause changes what gets delegated.** We have a house
style with an eight-agent sample and zero measurements.

**And the evidence we do hold is about the wrong artefact.** Twelve notes mention
`description`; almost every one is about **skill** descriptions and skill invocation. A
skill description competes for *model attention* against every other skill; an agent
description competes for *delegation* against a roster capped at 15,000 tokens `[B]`.
Those are different selection problems and we have been reading one as the other.

---

## Part 3 · The body — a template exists and nobody wrote it down

Seven of eight agents carry the **same four sections in the same order**:

```
## What you may not do, and by what mechanism
## Your functions
## Where your knowledge lives
## Scope
```

`architect` is the single exception — built first, four different headings.

Bodies run **686 to 1210 words** (mean ≈ 950).

| Aspect | Anthropic requires | We have measured | Opinion, unbacked |
|---|---|---|---|
| body length | **nothing** — the 5,000-word cap `[A]` is for `SKILL.md`, not an agent | — | ~1,000 words, by convergence |
| section set | nothing | — | **the four sections above, followed 7/8 times and never justified once** |
| boundary first | nothing | prose warnings failed in three studies and backfired in a fourth `[M]` | that stating the boundary **first** is better than stating it last |
| no persona | nothing | personas measurably negative for correctness `[M]` — 162 personas × 2,410 questions | — this one is genuinely backed |
| second person | nothing | — | "you" in 6/8, "it" in 2 — nobody decided, and both forms shipped |

**This is the most valuable finding in the register.** We have a de facto template. It was
never written, never argued, never checked — and it is nevertheless the strongest
regularity in the whole system. Writing it down converts an accident into a standard;
measuring it converts a standard into a rule.

---

## Part 4 · The surrounding artefacts

| Artefact | Exists for | Anthropic requires | We have measured | Opinion |
|---|---|---|---|---|
| spec `docs/agent-spec-*.md` | 3 of 8 | nothing | — | that a spec must precede assembly — enforced nowhere until today |
| evals | 4 of 21 skills; agents via briefs | nothing | ~15% of tasks get **worse** with a procedure added `[M]` | that every agent ships with a negative control and a containment case — a house rule `[M]`-adjacent, never itself tested |
| wall (hook) | 7 hooks, 6 harnessed | `PreToolUse` semantics `[B]` | 29·23·19·34·46 control rows pass `[M]`; **hooks absent in non-interactive runs** `[M]` | that a hook is the only real mechanism — undermined by the line to its left |
| hook proposal | 5 of 7 | nothing | — | that a builder may not install its own wall |
| tester brief | 4 | nothing | independent testers found 81 defects in this library `[M]` | that the tester must be a different agent — backed for *review*, not for *agent testing* specifically |

---

## Part 5 · Where the evidence actually is

26 notes. **Six carry any `MEASURED`/`REPEATED` verdict at all.** The agent-relevant ones
are mostly among the twenty that do not:

| Note | Verdict tokens | Bears on |
|---|---|---|
| `agent-design-template.md` | 5 | tiers, composition, rules-don't-reach |
| `subagents.md` | 1 · `partly-verified` | every frontmatter field |
| `skill-anatomy.md` | **0** | description, body — and it is about *skills* |
| `hooks.md` | **0** | the wall |
| `claude-code-extension-layer.md` | **0** | how the pieces fit |
| `agent-builder-prior-art.md` | **0** | what others do |
| `effective-agents-anthropic.md` | **0** | composition |

`subagents.md` is the only note in the base that names who checked it. It reached that
state one day ago, through the research pipeline, and the check found the note **wrong**
about background tool removal.

---

## Part 6 · The research agenda, ranked

Ranked by *how much of what we do rests on the gap*, not by how interesting the question
is.

| # | Molecule | Why it ranks here |
|---|---|---|
| **1** | **`description`** | it is the only field that decides whether the agent is ever used; 8/8 written to a house style with zero agent-specific evidence; our 12 notes are about the wrong artefact |
| **2** | **body: sections and length** | the strongest regularity in the system (7/8) and the least examined; every future agent inherits it |
| **3** | **`tools` vs `hooks` as the wall** | we assert a hook is the real mechanism while having measured that hooks do not load in the mode agents run in. The two halves contradict |
| **4** | **`model`** | 8/8 set it, base says nothing, and it is the one field with a direct cost consequence |
| 5 | `skills` preload cap | we have the measurement; what we lack is whether it transfers from per-task skill counts to per-agent preloads |
| 6 | the nine unused fields | not urgent, but every one is an undecided decision |

**Not on this list, deliberately:** the mechanical limits — 1024 characters, kebab-case,
reserved words, anchored matchers. Those are documented, enforced by the validator, and
covered by 24 positive controls. They are the part of the system that already works.

---

## What this register does not establish

It is a reading of artefacts, not a measurement of behaviour. It can say that eight
agents share a body structure; it cannot say the structure helps. Every row in the fourth
column is a **candidate** for research, and the point of the third column being empty is
precisely that we do not yet know which of those practices are good ones.

Two of the practices this register exposes may well turn out to be right. The register's
claim is only that we never checked.
