# 0021. An architect subagent with three procedures, and a wall between it and the code

- **Status:** Proposed
- **Date:** 2026-08-28
- **Phase:** 2 (Architecture & decisions) — the missing pass this ADR names

## Context

`docs/as-built/ARCHITECTURE-AS-BUILT.md` closes on a diagnosis of this
codebase: *"Where the missing architect pass shows — not in the ideas, which
are good. In the seams."* Five seams, each small, each a decision taken where
the information to take it was not. *"Together they are the difference between
a system that was drawn and one that accreted."*

Everything in this repository was built without a single skill or subagent.
The rebuild will not be, and the first talent it needs is the one whose absence
the as-built document already measured.

Four constraints came out of the research done before writing anything, and
they are what this ADR is really recording. Three of them contradict the
obvious design.

**Personas are measurably negative.** The intuitive build is "you are a
principal architect with twenty-five years of experience." Zheng et al. (EMNLP
2024) tested 162 personas across 2,410 questions and four model families and
found no improvement, with the effect "largely random." A second study
(arXiv 2603.18507) measured MMLU falling 71.6% → 66.3% and coding down 0.65 on
MT-Bench under persona framing. Personas buy register and compliance and cost
correctness. **What "twenty-five years of experience" actually means is the
list of ways systems have failed** — and that is content, not costume. It is in
the skills, as procedures.

**Separation, however, does work.** CodeR (arXiv 2406.01304) removed agent
roles from a multi-agent SWE-bench pipeline and the resolve rate *fell*.
The mechanism is a separate context window with a restricted tool surface and a
scoped job — not an identity. So: a subagent, yes; a personality, no.

**At most three preloaded skills.** SkillsBench (arXiv 2602.12670) measured
skills lifting task success 33.9% → 50.5%, and within that: *"focused skills
with at most three modules outperform larger or exhaustive bundles"* — 1–3
modules ≈ +19.0pp, 4+ ≈ +10.1pp. It also measured ~15% of tasks **regressing**,
concentrated where the base model was already competent, and found software
engineering its *weakest* domain (+4.5%). Three is a ceiling, not a target, and
each skill has to earn its slot against a measured risk of harm. A mechanical
constraint points the same way: on compaction, preloaded skills are re-attached
at up to 5,000 tokens each against a 25,000-token shared budget, most-recent
first, so truncation risk begins around six.

**Knowing the step and performing the step are different interventions.**
Borowa et al. (arXiv 2111.04362) taught practising architects about their own
cognitive biases and measured **no debiasing effect** — practitioners were more
biased than students, attributed to attachment to systems they had built. The
2025 follow-up (arXiv 2502.04011) found the same techniques worked when applied
*as a procedure to the architecture in hand*. Hence: numbered steps, each
ending in an artefact, rather than principles to bear in mind.

Fischhoff (1978) supplies the reason the artefact is not optional. Shown a fault
tree with three of six branches deleted, subjects assigned "all other problems"
**.140**, against .078 for the full tree. The **normative** value — what they
should have assigned — was **.468**. They recovered 30% of the gap. Directing
attention explicitly at what was missing moved the second pruned condition from
.227 to .346, recovering 57% instead of 37%: real, marginally significant
(p ≈ .06–.08), and still a fraction. **1 subject of 55** assigned enough.
Detection was uncorrelated with experience (τ = .058). A consideration raised
and not written down does not land.

> **Erratum, 2026-08-28.** The paragraph above previously read *"moved the
> probability subjects assigned to 'all other causes' from .078 to .468"*, and
> `architecture-decision/SKILL.md` carried the same sentence. That reversed the
> finding: **.468 is the normative value, not an observed one.** Subjects moved
> to .140. The original wording also claimed that asking subjects to think
> harder "roughly doubled it", which the source table does not support and which
> has been removed rather than rewritten. Corrected against
> `knowledge/notes/design-fixation-and-anchoring.md`, which carries the full
> five-row table. The error's direction flattered the intervention: it described
> subjects correcting themselves almost completely when they barely corrected at
> all. Nothing in the Decision below turns on it — the conclusion "write the
> artefact down" survives, and is in fact better supported by the true numbers.

## Decision

A single `architect` subagent (`.claude/agents/architect.md`) preloading
exactly three skills, with no persona framing, and no ability to write source
code.

**The three procedures**, chosen to cover the verbs the work actually needs —
derive, choose, decompose, plan, review, conformance-check, record, re-decide:

| Skill | Verbs | Terminal artefact |
|---|---|---|
| `architecture-decision` | derive, choose, record, re-decide | an ADR carrying an observable falsifier |
| `system-decomposition` | decompose, plan, name | a change matrix, arrow verdicts, a hiding sentence per part |
| `architecture-review` | review, conformance-check | findings at `file:line` with states, and the not-checked line |

**Content is counter-rules, not literature.** Each skill carries the failure
modes with measured incidence — Yuan et al.'s 92% of catastrophic failures from
mishandled *explicitly signalled* errors; Huang et al.'s retry-induced load
sustaining over half of metastable failures; DAGOR's five production years
showing request queuing time beats CPU as the overload signal by ~50%; Knight
Capital's repurposed flag and $460M in 45 minutes; Kinesis's quadratic thread
growth and 17 hours — and this system's own six observed failures, each traced
to `file:line` in `docs/as-built/`. The ablation evidence available to us says
the rules that discriminate are the ones that **override what a competent
practitioner naturally does, with the named mechanism for why.** Rules that
merely restate good practice did not discriminate.

**The boundary is a wall, not a sentence.** `tools:` omits Bash and Agent; a
`PreToolUse` hook scoped to the agent refuses any Write, Edit or NotebookEdit
outside `docs/`. A PreToolUse hook runs before every permission check —
`bypassPermissions` included — and can only tighten. With no Bash and no
subagents there is no path around it. Nine controls are exercised against the
hook, including path traversal through `docs/`, a prefix-lookalike directory,
a payload with no path, and malformed JSON; all nine behave.

The reason is not distrust. A decision whose author can implement it in the
same breath never meets an implementer who disagrees, and that meeting is the
only test the decision gets before production.

**Every skill ships with an eval set**, written against ground truth that
already exists: the as-built analysis labels this system's real defects at
`file:line`. Each set includes a **negative control** — a case where the right
answer is to produce nothing — because a review skill that confirms everything
and a decomposition skill that finds seams everywhere both score well without
one. The evals are written and **not run**: the author does not score its own
work, and an independent tester must fill the results tables before any of
these three is treated as validated.

## Consequences

- The architect cannot implement. Its output is a document someone else acts on
  or refutes. This is slower per decision and is the point.
- Three slots are full. A fourth architecture skill displaces one of these or
  is loaded on demand through `Skill` — dynamic invocation is not what
  SkillsBench capped; preloading is.
- The `skills:` field resolves against skills visible to this project. These
  three live in `.claude/skills/` here, so they resolve. Skills held elsewhere
  (`/home/user/skills-repo`, the Scio repo) do **not** and would need plugin
  packaging — recorded as B124.
- `model: inherit`. The architect is only as good as the session that calls it;
  run it from the strongest model available. Pinning a model here was rejected
  as a value that would silently drift.
- Three skills preloaded ≈ 15,000 tokens against the 25,000-token compaction
  budget. A fourth crosses into truncation risk.
- **Unvalidated until the evals run.** Three of four architecture skills
  measured elsewhere in this project did not discriminate, and one measured
  skill made the answer worse. Nothing here is exempt from that base rate.

**Reverse this when** any of: fewer than 4 of 6 D-cases, 4 of 6 S-cases (S5
included), or 5 of 7 R-cases pass under an independent tester — cut the failing
skill rather than revise it; or a fourth procedure is needed often enough that
on-demand loading is measurably worse than preloading; or an architect decision
is found to have been silently implemented by its author, which would mean the
wall did not hold.

## Alternatives considered

**One large architect skill.** Rejected on SkillsBench's measured module count:
4+ modules roughly halved the gain against 1–3, and exhaustive bundles
underperformed focused ones.

**A persona-framed agent with no skills** — "a principal architect with
twenty-five years." Rejected on the two persona studies above. This is the
option that looks most like what was asked for, and it is the one the evidence
refuses; what was actually wanted is in the failure-mode content.

**Skills with no agent.** Rejected on CodeR: removing role separation lowered
the resolve rate. Separate context and a restricted tool surface are doing work
that a skill alone cannot do — in particular, a skill cannot be denied Write.

**Multiple architects debating** — a security architect, a data architect, a
review architect. Rejected on cost-adjusted evidence: token budget explained
80% of the performance variance in Anthropic's own multi-agent result, and
debate *lost* to self-consistency at matched compute (83.2 vs 85.3; 83.0 vs
88.2). One architect running a procedure, with an external verifier, beats
several conferring.

**Letting the architect write code behind a rule rather than a hook.** Rejected
because a rule is a convention and this project has measured what conventions
are worth. The hook is the difference between a boundary and a preference.

**No architect; keep deciding inline.** This is the option the as-built
document already evaluated for us, in the seams.
