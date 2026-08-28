# evals — architecture-decision

**Status: written, not run.** Authored by the same session that wrote the
skill, which is the conflict this repo's own rule forbids: the author does not
score its own work. These cases are the ground truth; an independent tester
must run them and record the result below.

**Discrimination bar.** A case earns its place only if a competent
practitioner *without* the skill plausibly gets it wrong. Cases where the
baseline already succeeds do not measure the skill — and can make it worse:
SkillsBench measured ~15% of tasks *regressing* under skills, concentrated
where the base model was already competent. Cases marked ✗ below were
considered and rejected for that reason.

Score each case **pass** only if the named artefact is present in the output.
An output that discusses the right thing without emitting the artefact is a
**fail**, because the artefact is the entire mechanism (step 0 of the skill).

---

## D1 · The pre-narrowed question

**Input:** "Should the build queue use Redis or RabbitMQ?"

**Baseline failure:** compares the two.

**Required artefact:** one sentence naming the assumed decision — that builds
are dispatched through a broker at all — and whether it is recorded. Ground
truth: ADR-0020 *builds as jobs* is **Proposed**, not Accepted. A pass cites
that. A pass that instead concludes "the broker choice is downstream of ADR-0020
and cannot be made first" scores higher.

## D2 · The unknown that must stay unknown

**Input:** "We need to pick a datastore for build history. Nobody has given us
retention or volume numbers."

**Baseline failure:** invents plausible numbers, or omits the row.

**Required artefact:** a five-row constraint table with `unknown` in the load
and failure rows *and a named owner for the decision*. Ground truth: ADR-0019
(deletion and retention) is **Proposed**. Fabricating a number is a fail even
if the eventual choice is defensible.

## D3 · The third option

**Input:** "Choose a vector database for library matching."

**Baseline failure:** two-way comparison, or three vendors.

**Required artefact:** a third option that removes the need for the decision.
Ground truth exists in the codebase: `LAYER-D` shows matching is decided by
the `Contract` subset-plus-equality test, which is exact, not similarity-based.
A pass proposes "no vector store; contract matching is decidable" as option 3.
Note this case discriminates hard — the baseline treats "which vector DB" as
the question and never asks whether retrieval is the mechanism.

## D4 · Reversal cost as a rigour dial

**Input:** "Should the CLI flag be `--verbose` or `--debug`?"

**Baseline failure:** applies the full procedure; produces an ADR.

**Required artefact:** the reversal-cost line, and a refusal — the skill's own
"when this does not apply" clause. A skill that runs its procedure on
everything has no discrimination. This is the negative control: **a pass here
is producing less, not more.**

## D5 · The reactivated name

**Input:** "We are adding a `status` value `queued` to `BuildVersion` to mean
'waiting for a sandbox slot'."

**Baseline failure:** designs the transition.

**Required artefact:** the grep and its result. Ground truth: the as-built
analysis records an **unreachable queue state** already present. A pass finds
the existing reader before adding the value. Failure mode 4 (Knight Capital)
is the one being exercised.

## D6 · The dropped signal

**Input:** "Design an endpoint that returns per-workspace spend against the
period ceiling."

**Baseline failure:** designs the endpoint.

**Required artefact:** value → consumer, and the discovery that
`/usage/allowance` **already exists with no consumer**. A pass proposes
surfacing the existing signal rather than adding a second one. This is the
case closest to the system's own most-repeated defect, so it is weighted
highest.

## Rejected cases (baseline already succeeds)

- ✗ "Should we use HTTPS?" — no practitioner gets this wrong.
- ✗ "SQL or NoSQL for relational data with joins?" — decided by the question.
- ✗ "Add an index to a slow query?" — not architecture; one file, one hour.

---

## Results

| Case | Tester | Date | Verdict | Note |
|---|---|---|---|---|
| D1 | — | — | unrun | |
| D2 | — | — | unrun | |
| D3 | — | — | unrun | |
| D4 | — | — | unrun | |
| D5 | — | — | unrun | |
| D6 | — | — | unrun | |

**Shipping bar:** ≥4 of 6, D4 and D6 among them. Below that the skill is not
discriminating and should be cut rather than revised — this repo has one
measured instance of a skill that made the answer worse, and three of four
architecture skills elsewhere that did not discriminate at all.
