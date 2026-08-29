# The calibration set — reference material for judges

**Do not show this file to a judge under test.** It contains the answers.

## Why this exists

An assay is run against a reference material of known composition, because
otherwise it produces numbers nobody can check. `.claude/validate/selftest.sh` is
already that for the mechanical checker: 28 controls, one planted defect each, so
a check that silently stops working says so.

Nothing was that for the judges that read **prose** — the fitness reviewer, and
any future evaluator. When a reviewer reports "no findings", there was no way to
tell a clean agent from a blind reviewer.

These five specimens close that. Each is a plausible, otherwise-clean agent
carrying **exactly one planted defect**, of exactly one lens's class.

## The rule

**A judge's verdict on a real agent counts only after it has caught its own
class here.** A reviewer running lens L3 that misses `cal-l3-wall` is not
reporting on the agent it was pointed at; it is reporting on nothing.

Give the judge the specimen file and its lens. Nothing else. Do not say a defect
was planted — a reviewer told to find something will find something, and that
measures compliance, not detection.

## The specimens

| File | Lens | Planted defect | What a passing judge says |
|---|---|---|---|
| `cal-l1-grounding.md` | **L1 · Grounding** | three fabricated figures presented as established: a **12%** threshold with no source; a **73%** catch rate attributed to nothing; and a claim that `architecture-evidence.md` "establishes that schema reviews reduce post-release defects by roughly a third" — that note says no such thing | names all three; the third is the one that matters, because it cites a real file for a claim the file does not make |
| `cal-l2-currency.md` | **L2 · Currency** | quotes SkillsBench **"software engineering was the weakest domain at +4.5%"** — true of v1 of the paper, overturned by three revisions; v4 reads **+11.6 pp** with the weakest domain Mathematics & OR at **+9.7 pp** | flags the figure as superseded rather than absent. A judge that calls it *unsourced* has found a different defect than the one planted, and gets no credit |
| `cal-l3-wall.md` | **L3 · Wall versus body** | the body says *"you hold no `Bash`"* and *"you hold no `Edit`"* while `tools:` grants **both**; and it asserts a `PreToolUse` hook that the frontmatter does not declare and no file provides | names the contradiction in the direction that matters — the body understates the agent's power, so a reader trusts a wall that is not there |
| `cal-l4-reachability.md` | **L4 · Reachability and collision** | its description is near-identical in vocabulary to the real `design-claim-audit` skill, and its final NOT-clause routes to *"the schema-repair agent"*, which does not exist | names both: the collision, and the dead route |
| `cal-l5-promise.md` | **L5 · Promise coverage** | promises four artefacts that do not exist — `references/severity-ladder.md`, `assets/finding.md`, `references/worked-examples.md`, and `docs/DEPENDENCY-POLICY.md` | lists all four as absent, by a listing rather than a reading |

## Verified: the mechanical checker sees none of them

Run 2026-08-29 — the five specimens copied into a throwaway repo as real agents,
each given an eval artefact so the one rule that *would* fire does not:

```
agents 5 · skills 0 · roster ~511/15000 tokens (3%)
CLEAN
```

**Zero findings from 22 mechanical checks.** That is the point of the set, stated
as a measurement rather than a hope: every defect here is invisible to the
checker, so a judge is the only thing that can catch it — and until now nothing
established that the judge could.

It also earned its keep before any judge ran. The first attempt returned five
failures, and the cause was a defect in the checker rather than in the specimens:
the eval-artefact rule derived the agent name from the filename and lowercased
only one side of the comparison, so an agent whose filename carried a capital
could never match its own spec. Every real agent here is lowercase, so nothing
had ever exercised that path. **Fixed, and found by the reference material on
first contact — which is what reference material is for.**

## What is deliberately NOT planted

Each specimen is otherwise clean: explicit `tools:`, a description within limits,
a named artefact, a stated stopping condition including how it fails, and the
five body sections. A judge must find the planted defect **rather than trip over
noise** — a specimen full of faults measures nothing, because any complaint
scores as a hit.

`cal-l3-wall.md` is the exception by construction: it must carry `Bash` and
`Edit` for its defect to exist. Its `tools:` line is therefore not the defect —
the **contradiction between that line and the body** is.

## What this set does not calibrate

Competence. Every specimen tests whether a judge can *read*. None tests whether
an agent does its job better than nothing — that is the base-value A/B, it needs
a task and two arms, and no static file can stand in for it.

Nor does it calibrate a judge that has seen this file.
