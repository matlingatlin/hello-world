# The agent factory — layers, functions, and why the seams sit there

Produced by running `system-decomposition` on the question before any of it was
built. The deliverable is this document.

---

## 0 · The noun list, set aside

Agent · Template · Molecule · Evidence · Note · Skill · Spec · Test · Evaluator ·
Registry · Brain · Validator.

Nouns say what the system *stores*. Kept for step 5.

---

## 0b · A division of labour borrowed from a far domain

**Function, no software nouns:** *make a specialist to a written standard, where
the standard itself has to be derived from evidence, and prove it works before
anyone relies on it.*

**Organisation that does this:** a **pharmacopoeia and the GMP operation around
it** — the body that writes drug monographs, and the manufacturer that makes to
them.

Its divisions, in its own words:

| Their division | Our part |
|---|---|
| **Monograph committee** — writes and revises the standard per substance; never the manufacturer | the template — **but no separate owner; the builder's own skill carries it** |
| **Reference standard laboratory** — physical known-good material every assay is calibrated against | **NOTHING** |
| Formulation development — what is this particular product | `agent-shape` |
| Manufacturing to the monograph | `agent-assembly` |
| **In-process control** — checks *during* the run, not only after | **NOTHING** — the validator runs after assembly |
| QC release testing — separate unit, batch by batch | validator + fitness review |
| **Qualified Person** — one accountable signature before it leaves | **NOTHING** |
| Clinical trial vs control, endpoints pre-registered | base-value A/B — **not built** |
| **Pharmacovigilance** — signal collection after release, forever | **NOTHING** (B132) |
| Batch record — lets you reconstruct what was done | the spec, partially |
| Recall / withdrawal | **NOTHING** (B133) |

Six empty rows. Two are already on the backlog. **Four are new, and one of them
is the most useful thing this step produced.**

### The reference standard laboratory

You cannot run an assay without a reference material — a sample of *known*
composition that calibrates the instrument. Without it the assay produces
numbers, and nobody can say whether they are right.

**We have judges and no reference material.** `selftest.sh` does exactly this for
the validator: 24 controls, each planting one known defect, so a checker that
stops working says so. Nothing does it for the *fitness reviewer* or for the
*base-value evaluator*. When a reviewer returns "no findings", we cannot tell a
clean agent from a blind reviewer.

**→ New part: the calibration set.** Deliberately defective agents, one planted
defect each, specified. Every judge — reviewer, evaluator, any future checker —
must catch its own class before its verdict on a real agent counts. It is the
positive-control idea moved one level up, from the checker to the judges.

### In-process control, and the Qualified Person

The user asked for validation *"either after, or continuously"*. Pharma answers
that: in-process control exists because finding a bad batch at release wastes the
batch. Assembly should call the checker **per part as it is written**, not once at
the end.

And nothing here records a **release decision**. We produce verdicts; we have no
step where one accountable party says "this goes into use", and no record of who
did. A verdict is an input to that decision, not the decision.

---

## 1 · Change matrix — what opens when

| Likely change | Parts that open |
|---|---|
| Anthropic changes a **limit** | validator alone — provided numbers live only there |
| Anthropic adds a **field** | template + validator = **2, and that is why they are in one layer** |
| We learn a new failure mode | the knowledge note alone |
| A new domain needs an agent | research → plan → make = 3, and that is the pipeline working as intended |
| **The evaluation method changes** (e.g. we add repeated runs) | **test design + evaluator + calibration set = 3** |
| Template guidance changes | template alone |

**Row five is the finding.** "How we test", "what we test against" and "who
judges" are currently tangled, so improving the method opens three parts. The
resolution is in the layering below: the calibration set is **data**, the test
design is **a procedure**, and the evaluator is **a runner**. Separated, a method
change opens one.

---

## 2 · Ownership — and here it is not organisational

One project, one human. So the usual owner question is empty. The boundary that
actually binds is different and sharper:

**Which parts may an agent write, and which require a human?**

| Part | Written by |
|---|---|
| The template (the standard) | **human** — a builder that writes its own standard has none |
| The validator (the rules) | **human** — same reason |
| The calibration set | **human** — a judge that plants its own defects grades itself |
| Knowledge notes | agent drafts, agent verifies, **human promotes** |
| Agent files and skills | agent |
| The release decision | **human** |

Four human-owned parts, and each is human-owned for the same reason: **it is the
thing the agent is measured against.** That is the seam. Everything an agent
produces sits below a line it cannot reach.

---

## 3 · The layers, and what each hides

### L1 · Standard — *what good looks like*

`template/` · `validate/agents.py` · `calibration/`

**Hides:** every threshold, every writing rule, every planted defect. All three
can change completely without anything above changing its interface.

**Public surface:** the template files, the checker's exit code and findings list,
the calibration set's manifest.

**Rule:** the *numbers* live in the validator only; the *prose* lives in the
template only. Neither imports the other. Assembly reads both.

### L2 · Evidence — *what we actually know*

`domain-researcher` → `primary-source-verifier` → the knowledge base

**Hides:** which sources, which search strategy, how a sweep is split, what
saturation means.

**Public surface:** a verified note with per-claim verdicts.

**Feeds L1.** A template rule with no note behind it is marked `[HOUSE]`; when
evidence arrives it becomes `[MEASURED]`. That tag is the join between the layers.

### L3 · Plan — *what this particular agent needs*

The shaper, extended into what the user called the brain.

**Its output is a bill of materials:** every input the agent will need — notes,
skills, references, a wall, a spec — each marked `exists`, `must be commissioned`
or `not needed`. Each missing line routes to the part that can make it: a note to
L2, a skill to the skill-maker, a hook to a proposal.

**Hides:** how the roster is decided, how the diet is set.

**Public surface:** the spec and the bill of materials.

### L4 · Make — *build it to the standard*

The assembler and the skill-maker.

**Hides:** file layout, authoring order.

**Public surface:** the files, and the checker's output after each part.

**In-process control:** the assembler calls the validator **per part**, not once
at the end.

### L5 · Prove — *does it conform, and does it work*

Three distinct things, separated because tangling them is the step-1 finding:

| Part | Question | Kind |
|---|---|---|
| **Conformance** | is it built correctly | the validator — generic, reusable, already exists |
| **Containment** | can it exceed its remit | fixtures — mostly generic, reusable |
| **Competence** | does it do the job better than nothing | **specific, must be invented per agent** |

Competence is the base-value test: the same task run with and without the agent,
judged by an evaluator that neither built the agent nor ran the arms, against
**criteria written before the run**.

**Hides:** scenario design, scoring method, how many runs.

**The calibration set sits under all three**, and no verdict counts until the
judge has caught its own planted defect.

### L6 · Release and watch

**Release:** one accountable decision, recorded — who, when, against which
template version, on what evidence. Fit, unfit, or cannot-say is L5's output;
*install* is a human's.

**Watch:** post-release signal collection. B132 is this row, and it stays open.

---

## 4 · Arrows

```
L2 Evidence ──► L1 Standard ──► L4 Make ──► L5 Prove ──► L6 Release
                    ▲              ▲            ▲
                    └── L3 Plan ───┘            │
                                   L1 calibration set
```

| Arrow | Verdict |
|---|---|
| Evidence → Standard | `ok` — evidence raises a `[HOUSE]` tag to `[MEASURED]` |
| Standard → Make | `ok` |
| Plan → Make | `ok` |
| Make → Prove | `ok` |
| Calibration → Prove | `ok` — and it is the arrow that makes Prove mean anything |
| **Standard → Evidence** | would be `wrong-direction`. The template must never tell research what to find. **Forbidden** |
| **Make → Standard** | would be `wrong-direction`. A builder that edits its own standard has none. **Enforced by human ownership, per §2** |

`unverified against the graph` — this is a reading of an unbuilt design, not a
mechanical check.

---

## 5 · The parts that will be repaired downstream

**One.** `agent-shape` fixes the tool surface at L3; L5 then needs the agent to
run something to prove itself, and cannot.

> *L3 decides the tool surface; L5 repairs it by handing commands up to the
> orchestrator; the information about what must be executed to prove the agent
> lives in L5.*

Observed, not hypothetical: `agent-fitness-review` was given no `Bash` for good
reasons and consequently cannot run the checker its own procedure depends on.

**Resolution, chosen:** pass the constraint backward explicitly. L3's bill of
materials gains one required line — *"what must this agent be able to execute to
demonstrate its own competence?"* — answered before the tool surface is fixed. If
the answer needs a shell and the safety argument says no, that tension is
recorded as a decision rather than discovered at test time.

**Second, accepted with a reason.** The template fixes the body structure before
the evidence for it exists. Agents built in between carry the old shape.
Resolution: **version the template, and record in each agent's spec which version
it was built against** — the batch record. Then a template change produces a
migration list rather than silent drift.

**Back to the noun list:** `Registry` appears in no part. That is B133, reached
again from the other side.

---

## 6 · Job lists

| Part | Jobs | Verdict |
|---|---|---|
| Template | 1 specify each part · 2 example and non-example · 3 carry provenance | name covers it |
| Validator | 1 check | exact |
| **Calibration set** | 1 hold known defects · 2 calibrate every judge | one thing, two phrasings |
| Evidence loop | 1 scope · 2 sweep · 3 extract · 4 verify · 5 promote | 5 jobs, 2 agents, already split at the honest seam |
| **Plan / brain** | 1 decide the roster · 2 set the diet · 3 **emit the bill of materials** · 4 route each gap | **four jobs, name covers one.** → rename to what it emits |
| Assembler | 1 write · 2 call the checker per part | ok |
| Test design | 1 invent the specific cases | exact |
| Evaluator | 1 run both arms · 2 score against pre-registered criteria | ok |
| Release | 1 decide · 2 record | ok |

---

## Backlog raised

- **B148** — no calibration set: judges are uncalibrated, and "no findings" is
  indistinguishable from a blind reviewer
- **B149** — validation runs after assembly, never during
- **B150** — no release step and no record of who released what, against which
  template version
- **B151** — the shaper has no bill of materials, so gaps are found at build time
  instead of planned for
- **B152** — the template is unversioned, so a change to it drifts silently
  through every agent already built
