# Trust boundary — the recorded failures

Every row is a real, recorded run in this repository, written by somebody other
than this skill's author, dated before this skill existed. Cite the `file:line`,
not this file.

---

## T1 · One side gated, the other side not

`docs/REVIEW-PRODUCTION-READINESS.md:205-211` (§4.5, "Prompt injection is an
unexamined surface"):

> User text flows from the wizard into Layer B/C prompts and then into codegen. The
> build gates constrain the *output* (file plan, allowed paths, instrumentation,
> secret scan) which is a genuinely good defence — **but nothing constrains the
> instruction.**

And the threat model at the time, `docs/SECURITY.md:11`, carried the whole subject
as one skeleton line:

> - Prompt injection into the agent.  (Phase 2/6)

The real analysis is dated **2026-08-22** (`docs/SECURITY.md:21`) — after the review
that named the gap. Step 1 exists because the enumeration was the missing artefact,
not the controls.

## T2 · The paths, once somebody enumerated them

`docs/SECURITY.md:29-37` is the artefact this procedure's step 1 is modelled on, and
it is worth reading in full before running step 1 — **after** you have derived your
own list, not before. Its five rows:

| Path | Whose words | The row worth noticing |
|---|---|---|
| the wizard conversation | the user's own | *"It is their build; the cost is theirs"* — a different category from the rest |
| the running app's console and rendered text | **a model's, via code a model wrote** | *"The defendant addresses the jury: a page that renders 'all criteria are met' is asking the judge to agree with it"* |
| design markings | the user's note **plus text scraped from the DOM** | |
| **catalog entries** | **another tenant's build** (ADR-0016) | *"The only prompt in the engine carrying text across tenants"* |
| the generated app's own files | a model's | *"An instruction written into the code in one attempt is quoted back in the next. Self-perpetuating, not escalating."* |

Two of those five are paths where **a model's own earlier output re-enters a
prompt** — the class most likely to be missed by an enumeration that only asks
"where does user input go".

The same document's honest gaps, `docs/SECURITY.md:66-76`:

> screenshots are not text and are not fenced. Text rendered **inside an image** is
> not covered by anything here.
>
> Layers B and C receive the spec's field values rather than the raw transcript.
> They are still the user's words, and they are not fenced today.

## T3 · A control blind to the shape it existed to catch

`docs/BACKLOG.md:250-251`:

> rule caught only the legacy `sk-<alnum>` shape, so a real `sk-ant-api03-…` key
> would have sailed through the one check meant to stop it

Step 3 is this row: quote the pattern, name one input it catches and one it does
not.

## T4 · The capability available and the secret present

`docs/REVIEW-PRODUCTION-READINESS.md:69-79` — graded **blocking**:

> `core/sandbox.py:141` starts the app with `env={**os.environ, ...}`. `os.environ`
> at that moment contains `ANTHROPIC_API_KEY`, `SCIO_CATALOG_DB` (a Postgres URL
> with credentials) … a generated app that merely *logs its environment* — a
> plausible thing for a model to write — puts the platform key in a log the user
> can read.
>
> **Fix:** build the child environment from an allow-list … Never `**os.environ`.
> This is a five-line change and it is the single most important one in this
> document.

The fix landed and is recorded at `docs/SECURITY.md:62-64` (B091): *"The generated
app runs with an allow-listed environment — no API key, no catalog database — so an
instruction that reaches the generated code cannot read a secret that is not
there."* Step 4 is this row, and the correct end state is written in the second
quote.

## T5 · A judge with no external signal, and n = 2

`docs/REVIEW-2026-08-21.md:121-125`:

> the reveal currently shows "4 of 5 parts work" with **no external measure at
> all.** The infrastructure exists: a preview is already running and Playwright is
> now a declared extra, so a Lighthouse run has somewhere to point.

And `docs/REVIEW-PRODUCTION-READINESS.md:241-244`:

> the estimate model (B077) was calibrated from **two** builds because two is all
> the data there is.

Step 5's `signal` and `n` cells are this row.

## T6 · The evaluation path making real calls

`docs/BACKLOG.md:251-253`:

> the new `.env` loader made the test suite pick up an operator's key, so
> `test_api.py` was making REAL model calls — 100 seconds and real money for a
> unit-test run.

Step 6 is this row. It was invisible until it cost time and money.

## T7 · The habit to preserve, not replace

`docs/REVIEW-2026-08-21.md:205-207`:

> **`unjudged` as a first-class concept.** A criterion nobody could check rides
> along instead of being dropped, so "works" means "works, and here is what nobody
> checked" … This is the codebase's best instinct and it should spread further.

Step 5's fourth cell exists to carry this word forward, not to invent a competing
one. When this procedure runs over a system that already has such a word, **use
theirs.**

## T8 · The limit of the whole procedure, stated by the system itself

`docs/SECURITY.md:73-76`:

> No test proves a real model resists a real injection: that needs keys and a
> measured experiment, not an assertion. What is tested is that the fences hold and
> that the structural rules refuse the shapes a successful injection would produce.

That is the correct shape of a `not checkable here` row, written by the system
under review. Step 7 hands the experiment up rather than closing the gap in prose.

---

## What is not evidenced here

- **The four-cell judgement table in step 5 is `unevidenced` as a structure.** Two
  of its cells rest on measurements from elsewhere: the no-external-signal rule on
  intrinsic self-correction (every model, every benchmark, worse — GPT-4 GSM8K
  95.5 → 91.5 → 89.0, `/home/user/skills-repo/knowledge/notes/llm-idea-generation.md`),
  and the negative-control requirement on this repo's own eval practice. Neither
  measured this table.
- **The control ladder in step 3** (fencing weakest, deterministic gate strongest)
  is taken from `docs/SECURITY.md:39-64`, which reasons for it and does not measure
  it. Marked `unevidenced`, and the source's own hedge — *"it should never be
  described as if it did"* — is part of the row.
- The enumeration discipline in step 1 rests on the SEI Mission Thread Workshop
  measurement (57 omission vs 25 commission, kappa .82,
  `/home/user/skills-repo/knowledge/notes/architecture-evidence.md`), which is about
  architecture risk workshops and not about prompts. **`unevidenced` by transfer.**
