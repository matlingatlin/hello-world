---
name: model-call-budget
description: Use when a model call's cost, latency or failure behaviour has to be designed rather than discovered — "what will this cost per request", "how long does this take and what does the user see", "what happens when the model is slow or down", "who stops the bill", "can we cap spend on this". Fetches the price and limits live, sizes each call in tokens, rules its latency class against the transport carrying it, names who enforces a ceiling at the request, tenant and job levels, traces every value the call returns to a consumer, and states what the user sees when the call is wrong, slow or absent. Emits the budget and degradation rows of the call table. NOT for deciding whether the call should exist, NOT for what may enter the prompt or who judges the output, NOT for implementing a ledger or a router, NOT for stack, tenancy or seam work (use architect).
---

# Model-call budget and degradation

Rules what each retained model call costs and what the system does when it does not
work. The idea holding it together: **a number that nobody enforces and a value
that nobody reads are the same failure.** In the recorded baseline a spend ceiling
was plumbed through the code and never set — a build estimated at $1.05–$2.51 spent
$2.69 and nothing intervened — while, one layer away, the cost the engine computed
was returned and dropped before anything read it. Both were written down as
intentions. Neither had an enforcer or a consumer.

So every row this procedure emits names a **who**: who enforces the ceiling, who
reads the value, who is told when the call fails.

Open `references/budget-rows.md` at step 3. Prices and limits are **never** in this
file or that one — they move, and they are fetched at step 1.

## 1 · Fetch the price and the limits, and record when

Never write a price, a context window, a rate limit or a per-token figure from
memory or from a cached file. `WebFetch` them at the time of the ruling:

- `https://platform.claude.com/docs/en/pricing.md` — input and output price per
  million tokens
- `https://platform.claude.com/docs/en/about-claude/models/overview.md` — model
  ids, context windows
- `https://platform.claude.com/docs/en/api/rate-limits.md` — limits by tier
- `https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md` — what
  a cache read costs relative to an input token

If a local cache of these URLs is available (a bundled `claude-api` skill ships
one under `shared/live-sources.md`), treat it as an index of URLs, not as a source
of numbers: its copy is pinned to a version and a session path.

**Artefact:** a provenance block at the head of section B — each number, its URL,
and the date fetched. A number with no `fetched:` date has no cell in the table.
If a fetch fails, say so and mark every dependent cell `not priced`; do not
substitute a remembered figure.

## 2 · Size each call

Per call: input tokens (system prompt + static prefix + variable payload + tool
definitions) and output tokens, as an **estimate with its basis stated** —
characters ÷ 4, or a measured figure from the system's own logs if it has any.

Then the multiplier that people forget: **how many times does this call happen per
user action?** Retries, per-chunk repeats of a static prefix, a loop over N items,
a double-mounted client. The recorded baseline has a case where a static prefix was
paid for three times because one package was emitted in three chunks.

**Artefact:** per call — input tokens, output tokens, calls per user action, and
money = tokens × the price from step 1. Show the arithmetic.

**Handed up, not faked:** an exact count needs a key. Print the command in section
D — `POST /v1/messages/count_tokens` against the assembled prompt, or the `ant` CLI
equivalent — naming the file it would run against. Your table says `estimated`;
the caller's run says `counted`.

## 3 · Rule the latency class against the transport

Open `references/budget-rows.md`. Classify each call:

| Class | Rule |
|---|---|
| interactive | under ~1 s. May sit on a request path |
| slow-interactive | seconds. Needs a stated in-flight state the user can see, and a reconnect |
| job | tens of seconds or minutes. **Must not live inside one HTTP request.** It needs an id, a queue, a state machine, cancellation and resumability |

Then check the transport actually carrying it. A `job`-class call inside a request
is a finding regardless of how well the request is written: in the baseline a
46-minute build lived in one HTTP request with no job id, and a restart both lost
the result and kept spending money on it.

**Artefact:** per call — the class, the transport at `file:line`, and `matches /
does not match` with the consequence named concretely.

## 4 · Name who enforces a ceiling, at three levels

A ceiling that exists in a variable is not a ceiling. For each call, fill all
three:

| Level | The question | A blank cell is a finding |
|---|---|---|
| the call or job | what is the maximum spend for one run, **who compares against it**, and what happens at the limit | yes |
| the tenant | what is the per-workspace quota, and who reads it | yes |
| the request | what rate limit stops the same authenticated user looping this path | yes |

"What happens at the limit" must be a first-class outcome, not an exception —
*"stopped at your ceiling, here is what was built"*. An unhandled limit that
surfaces as a 500 after the money is spent is the worst of both.

**Artefact:** three cells per call, each naming a file and a line or the word
`absent`.

## 5 · Trace every value the call returns to a consumer

For each field the model call's result carries — cost, token counts, duration,
confidence, a status — name the consumer at `file:line`. A field with no consumer
is computed and dropped, which is this system's recorded default failure with four
confirmed instances.

**Artefact:** one row per returned field: field, producer `file:line`, consumer
`file:line` or `dropped`.

## 6 · State what happens when the call is wrong, slow or absent

Three cells, per call, each answering *what the system does* and *what the user
sees*. Not "handle errors gracefully".

| Condition | Must name |
|---|---|
| **wrong** | what checks the output before it is believed, and what the user is shown when the check fails |
| **slow** | the timeout, what is shown while waiting, and whether a lost connection is distinguishable from a failed call. In the baseline it was not — a dropped connection read as "The build stopped" one line under a promise that it would keep running |
| **absent** | the fallback path, whether it is a degraded answer or a refusal, and whether the system says which. A silent fallback that looks like a success is worse than an outage |

**Artefact:** three filled cells per call. `unknown` is an allowed value and is a
finding; blank is not.

## 7 · Say what one ledger row must carry

You are not building the ledger — the library's `llm-call-ledger` owns that. You
are ruling **what must be recorded** so the questions in steps 2–6 are answerable
next time. In the baseline, the engine ran 46-minute jobs costing dollars across
17,000 lines with zero logging, which is why its own time estimate was calibrated
from two builds.

Name the fields: call id, job id, model id, input and output tokens, cost,
duration, outcome, and the caller.

**Artefact:** the field list, and the five questions it makes answerable, written
as questions.

## When this does not apply

- **The call may not need to exist.** Run `model-call-placement` first — budgeting
  a call you are about to delete is wasted work.
- **The question is what enters the prompt or who judges the output.** That is
  `model-trust-boundary`.
- **You are being asked to implement the routing, the ledger or the cap.** The
  library owns those: `cost-aware-model-routing` for tier and budget routing,
  `llm-call-ledger` for the per-call record, `abstention-threshold-design` for
  where a refusal cut goes. Name the file and the line; hand it over.
- **The system has no model call on the path in question.** Nothing to budget.
- **There is no price to fetch** — an offline or self-hosted model with no
  published figure. Then every money cell is `not priced` and the procedure yields
  only the latency and degradation halves. Say which half you produced.
