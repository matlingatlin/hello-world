---
name: model-trust-boundary
description: Use when ruling what may enter a model's prompt and what must be checked before its output is believed — "can customer data go in this prompt", "whose text ends up in there", "what if someone puts instructions in the input", "how do we know the answer is right", "who checks the model", "is our eval actually measuring anything". Enumerates every path by which text the system does not control reaches a prompt and gives each a worst realistic outcome, checks each control against the shape it must actually catch, asks whether the capability is available while the secret is absent, then rules per output who judges it, with what external signal, and what stays explicitly unjudged. Emits the intake table and the judgement table. NOT for whether a call should exist or what it costs, NOT for retrieval, chunking or embedding quality, NOT for auditing an agent's tool surface, NOT for tenancy or auth work (use architect).
---

# Model trust boundary

Rules both directions across a model call: **nothing that goes in is trusted, and
nothing that comes out is believed until something outside the model says so.**

The idea holding it together comes from the recorded baseline, which stated it
better than a rule could: the gates constrained what a model may **produce** —
"code cannot be talked out of its opinion" — and **nothing constrained what the
model was told.** One side of the boundary had three layers of control and the
other side had a skeleton heading in the threat model for eight months.

Open `references/trust-rows.md` at step 2. Do not open it at step 1 — step 1 is an
enumeration and a prior list of paths would bound it to the paths already known.

## 1 · Enumerate every path by which text you do not control reaches a prompt

Derive this on a blank page from the system's inputs first, then go looking. The
SEI measured **57 risks of omission against 25 of commission** (two raters, kappa
.82) and **no relationship** between the goals stated up front and the risks
actually found — a goals list will not find them, and neither will reading the
prompt-assembly code first, because the code sets your agenda.

Ask, for every prompt in the inventory: whose words are in it? Candidates the
baseline turned up include the user's own text, **text a model previously wrote**,
text scraped from a rendered page or a console, files in a repository the model
also writes to, and — the one people miss — **text from another tenant**.

**Artefact:** the intake table, one row per path: the path, whose words, what it
reaches (the chain, not just the first prompt), and the `file:line` where it enters.

## 2 · Give each path a worst realistic outcome

Open `references/trust-rows.md`. For each row, one sentence: what is the worst
thing that happens if this text is read as an instruction. Realistic, not
maximal — and say who bears the cost.

The distinction that matters and gets skipped: a path carrying the user's own words
into their own build costs them their own build. A path carrying **one tenant's
text into another tenant's prompt** is a different category and must be labelled as
one.

**Artefact:** a `worst realistic outcome` cell per row, naming who bears it. Not
"could cause issues".

## 3 · Rule each control against the shape it must actually catch

For every control the system claims, do not ask whether it exists. Ask **what
shape it matches, and whether that is the shape that occurs.** In the baseline a
secret scanner "caught only the legacy `sk-<alnum>` shape, so a real
`sk-ant-api03-…` key would have sailed through the one check meant to stop it."

For each control: quote the rule or the pattern at `file:line`, write down one
input it catches and one it does not, and rule `covers / partial / does not cover`.

And rank it honestly. Fencing and labelling is hygiene — the baseline's own
document says it "raises the cost of an attack; it does not make one impossible,
and it should never be described as if it did." A deterministic gate that runs
*after* the model and refuses is a different rung.

**Artefact:** per control — the pattern at `file:line`, one caught example, one
missed example, and the ruling.

## 4 · Ask whether the capability is available while the secret is absent

For any model call whose output is executed, or whose result reaches code the model
wrote, ask the question separately from "is the code sandboxed": **is the secret
reachable from where the generated code runs?**

The pattern to rule against is Anthropic's own in
`/home/user/skills-repo/knowledge/notes/managed-agents-architecture.md` — *"the
tokens are never reachable from the sandbox where Claude's generated code runs"*: a
proxy holds the credential and makes the call, so the capability is available and
the secret is absent. In the baseline the opposite was shipped — the child process
was started with the whole environment, putting an API key and a credentialled
database URL one line away from code a model wrote.

Rule the environment construction: allow-list or inherit-everything, at
`file:line`.

**Artefact:** per executed output — `secret reachable: yes / no`, the construction
at `file:line`, and for `yes`, the specific credential named.

## 5 · Rule who judges each output, with what signal

Per model output, fill four cells:

| Cell | The question | Rules |
|---|---|---|
| judge | code, a model, a human, or nothing | name it at `file:line` |
| signal | what external thing makes the verdict true | **a model judging its own output with no external signal is not a judge.** Intrinsic self-correction measured worse on every model and every benchmark — GPT-4 GSM8K 95.5 → 91.5 → 89.0 |
| negative control | the case where the right verdict is "no finding" | without one, a suite cannot tell a finding from noise |
| unjudged | what nobody checked, carried forward explicitly | reuse the system's own word if it has one |

The last cell is not a hedge; it is the strongest habit in the recorded baseline,
described there as letting "a criterion nobody could check ride along instead of
being dropped". A judgement table with no `unjudged` column is claiming complete
coverage.

Also record **n**: how many observations the judge or the calibration rests on. In
the baseline an estimate shipped calibrated on **two** runs. An n of 2 is a number
the table must show, not hide.

**Artefact:** four cells and an `n` per output.

## 6 · Check whether the evaluation path makes real calls

Ask it explicitly, because it is invisible until it bills: does the test suite, the
eval harness or the CI job call a real model? In the baseline an environment loader
change made the unit tests pick up an operator's key — "`test_api.py` was making
REAL model calls — 100 seconds and real money for a unit-test run."

**Artefact:** `evaluation path calls a real model: yes / no / unknown`, with the
fixture or key resolution at `file:line`.

## 7 · Hand up what needs a key or a running system

No test here proves a real model resists a real injection. That needs keys and a
measured experiment, and this procedure holds no shell. Print the experiment rather
than asserting the conclusion.

**Artefact:** section D rows — the experiment or command, what it would settle, and
who can run it. Never a control ruled `covers` on the strength of its intent.

## When this does not apply

- **The question is whether the call should exist, or what it costs.** Those are
  `model-call-placement` and `model-call-budget`.
- **The question is retrieval quality** — chunking, embeddings, grounding,
  citation attribution. The library's `rag-pipeline-reviewer` agent owns it.
- **The question is an agent's tool surface, permissions or blast radius.** The
  library owns those: `agent-surface-security-audit`, `agent-blast-radius-guard`,
  `agent-harness-construction`.
- **The question is where a confidence cut goes** — auto-ship versus review queue.
  The library's `abstention-threshold-design` owns the threshold; this procedure
  only rules that an abstention exists and is labelled.
- **The question is tenancy or auth** (use architect). Cross-tenant *text in a
  prompt* is this procedure's row; cross-tenant *data access* is not.
- **No untrusted text reaches any prompt and no output is acted on.** Then the
  tables are empty, and an empty table must say "enumerated, none found" with the
  queries — not be omitted, which reads identically to not having looked.
