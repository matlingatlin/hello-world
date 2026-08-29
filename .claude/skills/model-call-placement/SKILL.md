---
name: model-call-placement
description: Use when deciding whether a step in a system should be a model call at all, or when auditing a system that already has model calls in it — "does this need an LLM", "could a lookup table do this", "why are we calling the model on every page load", "should this be code". Enumerates every model call mechanically and records the query that found it, names the deterministic candidate for each one BEFORE reading the design's justification, then rules each call keep, replace or hybrid with a falsifier. Emits the call inventory and the replace list. NOT for choosing a model tier or a budget once the call is kept, NOT for retrieval, chunking or embedding quality, NOT for writing or repairing the code, NOT for carving a system into parts or placing seams (use architect).
---

# Model-call placement

Rules, per step in a system, whether a model call belongs there. The idea holding
it together: **the failure is coverage, not instinct.** In the recorded baseline
for this procedure, the team's judgement about deterministic gates was excellent
and explicitly praised — and a model call still sat on a read path costing 12.7
seconds and real money on **every page load**, because nobody had enumerated which
paths made a call. So this procedure spends its first step on enumeration and its
second on withholding the design's own explanation.

Open `references/placement-rows.md` at step 3, and not before — it carries the
recorded failures and their `file:line`, and reading it earlier seeds step 2.

## 1 · Enumerate every model call, mechanically

Do not sample and do not reason about where calls "probably" are. Run queries and
record them verbatim.

At minimum, `Grep` for: the SDK entry points (`messages.create`, `client.messages`,
`beta.agents`, `anthropic`, `Anthropic(`), any HTTP call to a model endpoint, every
prompt-template file, and every function whose name contains `prompt`, `critique`,
`judge`, `extract`, `classify` or `generate`. Then `Glob` the prompt directory and
read what calls each template.

For a proposal rather than a codebase, enumerate the steps the proposal describes
and mark each one "makes a model call: yes / no / unstated". **Unstated is a
finding**, not a blank.

**Artefact:** section A of the call table — one row per call, each carrying its
`file:line` (absolute path) or the proposal paragraph, **and the verbatim query
that found it, with its hit count**. A row without a re-runnable query does not go
in the table.

## 2 · Name the deterministic candidate before reading why the call exists

For each row from step 1, write down the candidate deterministic mechanism
**before** opening the comment, docstring, ADR or proposal paragraph that explains
why a model is used. Draw from this set, and say "none, because …" when none fits:

stored or precomputed value · lookup table or enum · parser, regex or grammar ·
rules engine or decision table · deterministic gate or validator · cache keyed on
the input · a smaller earlier step that makes the call unnecessary · a human

The ordering is the whole of the intervention. Fixation on a *self-generated*
first concept measured 0.32 against 0.24 for a provided example, and the design's
justification is a provided example that arrives with authority attached. Reading
it first does not make you agree with it consciously; it removes the alternatives
from the page.

**Artefact:** one candidate per row, written down, with the timestamp order
implicit in the document — section A gains a `deterministic candidate` column, and
every cell is filled before step 3 begins.

## 3 · Read the justification, and rule

Now open the explanation. Open `references/placement-rows.md`. Rule each row:

| Ruling | Means |
|---|---|
| `keep` | the input is open-ended natural language or the output space is unbounded, and the candidate from step 2 cannot cover it |
| `replace` | the candidate covers it. Name the mechanism and what it saves |
| `hybrid` | the candidate covers the common case; the model handles the tail. Say what routes between them and what the escalation rate would have to be for this to pay |
| `unstated` | the design does not say why a model is used. This is a finding, not a `keep` |

Every ruling carries a **falsifier** — one sentence naming what would show it
wrong. *"This is `replace` unless the input can contain a field the enum does not
have; if it can, the ruling is `hybrid`."*

**Artefact:** section C of the call table — the replace and hybrid list, one row
per call, each with the named mechanism, the falsifier, and the estimated or
recorded saving in latency and money.

## 4 · Rule whether the call has a boundary of its own

A model call fused into a function that also does the retry loop, the rollback,
the gates and the persistence has no boundary — it cannot be timed, substituted,
stubbed or failed over independently. In the recorded baseline this was a
226-line function holding six responsibilities, and the reviewer attributed the
three most recent bugs to it (`references/placement-rows.md`, row P3).

For each `keep` row, answer: can this call be replaced by a stub in a test without
touching the logic around it? If no, name the function and its line count.

**Artefact:** a `isolated: yes / no` cell per `keep` row, and for each `no`, the
function at `file:line` with its length.

## 5 · Hand over what you cannot rule

A call whose input you could not see, or whose cost you could not attribute, gets
a row in section D with the exact command or artefact that would settle it. Never
a softened `keep`.

**Artefact:** section D rows, each naming what would settle the question and who
can run it.

## When this does not apply

- **The call is already kept and the question is which tier or what budget.** That
  is `model-call-budget`, and the library's `cost-aware-model-routing` owns the
  routing implementation.
- **The question is retrieval quality** — chunking, embeddings, top-k, rerank.
  Different unit entirely; the library's `rag-pipeline-reviewer` agent owns it.
- **The question is where the parts of the system go**, or where a seam belongs
  (use architect). A seam table cannot express a call ruling and this cannot
  express a seam.
- **The system has no model in it.** Then there is nothing to enumerate, and
  running this produces a table of zero rows that reads as a clean bill of health.
  Say so and stop.
- **You are being asked to implement the replacement.** Name the file, the line
  and the mechanism; hand it over.
