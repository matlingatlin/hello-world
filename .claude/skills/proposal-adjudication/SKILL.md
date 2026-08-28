---
name: proposal-adjudication
description: "Use when candidate proposals have to be ruled against what already exists and what has already been proposed — is each one already built, already one of the standing proposals by id, genuinely new, or not applicable — with file:line or proposal-id evidence for every ruling. Also checks the candidate set's framing distribution against measured human reference rates, and discards runs whose required tables are missing. NOT for generating candidates (blank-slate-positions, comparable-products-sweep), NOT for deciding which to do (selection-dossier, and the choice is a human's), NOT for auditing existing capability (capability-retirement-audit)."
---

# Ruling on what a candidate actually is

A candidate that restates something the system already does, or something
already written down as proposal `E-7`, is not a bad candidate — it is a
*different* candidate, and it has to be labelled correctly or the whole set is
worthless. This procedure is why you were saturated with the corpus: judging
already-published ideas, a model scored novelty **6.14/10 without retrieval and
2.38/10 with it**. Without the existing reality in front of you, a novelty
judgment inflates about 2.6×.

Two traps this procedure is shaped around:

**Similarity scores do not detect restatement.** Measured: human-written
reference questions were *more* similar to their source material than model
outputs, while being *less* narrow. The pathology is structural, not lexical. So
every ruling below is a **named** nearest neighbour — a proposal id or a
`file:line` — never a score.

**Novelty scoring rewards vagueness.** In one 2026 study the worst system scored
**highest** on novelty (3.73/4) and last on quality (1.00/4), because a vague,
topic-agnostic proposal *"has no precise prior art to collide with, so it scores
as novel."* A candidate you cannot find a neighbour for is as likely to be empty
as to be new, and step 4 is where you tell those apart.

This procedure opens `references/corpus.md` at step 1 and `references/evidence.md`
before any number or effect size goes into a document.

## 0 · Admit or discard the run

Before reading a candidate file's content, check it carries its required tables:
the relational map and carry-back table from `blank-slate-positions` step 3, and
the coverage and actor tables from `comparable-products-sweep` step 3.

A missing table is not a small defect. In the study behind the analogy step,
**~15% of runs silently skipped the differentiation step and declared the ideas
already varied.** Those runs are discarded, not read — a run that skipped the
step and says it did not is worse than no run.

**Artefact:** per candidate file, `admitted` or
`discarded: <which table is missing>`. A discarded run is reported to whoever
commissioned it, not repaired by you.

## 1 · Load the corpus, by absolute path

Open `references/corpus.md`. Every path there is absolute, because
**`docs/as-built/` is not in this repository** and twelve files here cite it as
though it were (backlog B128). A `file:line` you quote from a document you could
not open is the failure this whole reference exists to prevent.

**Artefact:** the list of corpus documents you actually opened, and the list you
expected and could not. The second list is not empty by default — say so if it is.

## 2 · Rule each candidate against a named neighbour

For every candidate, find the nearest thing that already exists — by reading, by
`Grep`, by proposal id — and then rule:

| Ruling | Bar | Evidence required |
|---|---|---|
| `already-built` | the system does this now | `file:line`, plus the consumer, because a computed-and-dropped value is not a built capability |
| `already-proposed` | one of the standing proposals covers it | the proposal id and its document, plus what the candidate adds or contradicts, if anything |
| `partly` | overlaps a neighbour but carries something it does not | the neighbour **and** the specific delta, in one sentence |
| `new` | you looked and found no neighbour | **the searches you ran.** "I found nothing" is evidence only if you can name where you looked |
| `not-applicable` | it contradicts something settled | which ADR or document, and whether the contradiction is worth raising as a Proposed ADR |

A `new` ruling with no named searches is downgraded to `unverified`. So is any
ruling resting on a document you could not open.

**Artefact:** the ruling table — candidate → ruling → named neighbour or named
searches → delta.

## 3 · Tabulate the framing distribution of the whole set

Individually, each candidate reads fine. The defect is in the distribution, and
it is only visible in aggregate.

Count the candidate set by the framing labels the prospector attached, and put
them beside the measured human reference rates (11,683 papers, 9 model
configurations, identical context):

| Framing | Human | LLM measured | This set |
|---|---|---|---|
| bridge two disconnected things | **12.1%** | 47.1–64.2% | |
| synthesise / unify | **5.1%** | 22.5–38.7% | |
| everything else | 82.8% | — | |

Normalised entropy for reference: humans **0.926**, LLMs **0.550–0.758**.

This is a **diagnosis of the generation run, not a licence to delete
candidates.** If the set sits at LLM rates, the finding is that the candidate
supply is 4–5× over-concentrated and more prospector instances with different
briefs are needed — a supply problem, reported upward. Deleting candidates to
flatten the table would be you selecting, which is not yours.

**Artefact:** the filled table, and one line: `supply adequate` or
`supply over-concentrated — more instances needed, and here is what their briefs
should differ on`.

## 4 · Separate the vague from the new

For each `new` candidate, ask the question that separates a real proposal from a
topic-agnostic template: **what would this look like at `file:line`, and what
would it be wrong about?**

A candidate that cannot be made concrete enough to be wrong is marked
`too vague to rule`. That is not a soft `new`; it is a request back to the
generator.

**Artefact:** each `new` candidate → one concrete consequence someone could
observe, or `too vague to rule`.

## 5 · Say what you could not settle

Some candidates turn on a product or business question no `file:line` answers —
who the curator is, what happens on deletion, whether a signal is wanted
downstream. Do not resolve those by inference and do not let the inference hide
inside a ruling.

**Artefact:** the open-question list, each phrased as a question with a named
person or document that could answer it.

## When this does not apply

- There are no candidates yet. Nothing to rule on.
- You are being asked which candidates to do. That is `selection-dossier`, and
  the choice at the end of it is a human's — measured, model-versus-expert
  agreement on idea quality is **22–40%** where expert-expert is 60%, and the
  disagreement runs in opposite directions rather than being merely noisy.
- The question is whether an existing capability should survive. That is
  `capability-retirement-audit`.
