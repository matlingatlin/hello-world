# Budget and degradation — the recorded failures

Every row is a real, recorded run in this repository, written by somebody other
than this skill's author, dated before this skill existed. Cite the `file:line`,
not this file.

**No price, limit or per-token figure appears here.** Those move; step 1 fetches
them. A number in this file would be correct on the day it was written and
unverifiable thereafter.

---

## B1 · A ceiling that was plumbed and never set

`docs/REVIEW-2026-08-21.md:20-33`:

> `budget_usd` is plumbed and never set … The relay enforces a budget
> (`execution/relay.py:214`) and `BuildOptions` carries the field
> (`builder/loop.py:254`) — but the only construction on the real path,
> `builder/pipeline.py:234`, leaves it `None`.
>
> … a build estimated $1.05–$2.51 spent **$2.69** and nothing intervened.

Note the shape: the enforcement code *existed*. What was missing was the **who** —
nobody set the value on the real path. Step 4's "who compares against it" cell is
this row.

The same review names the correct outcome shape:

> surface exceeding it as a first-class outcome — "stopped at your ceiling, here is
> what was built" — not an exception.

## B2 · The ceiling missing at three levels

`docs/REVIEW-PRODUCTION-READINESS.md:220-226`:

> **No spend ceiling on any build** … Add: **no per-workspace quota** and **no rate
> limit**, so the ceiling is missing at three levels — the build, the workspace,
> and the request.

And `docs/REVIEW-PRODUCTION-READINESS.md:196-198`:

> Every expensive path — intake (a model call per message), preview builds,
> `/design/change` — is reachable by an authenticated user in a loop. With no spend
> ceiling this is not merely a DoS surface, it is an **unbounded bill**.

Step 4's three-level table is this row.

## B3 · A value computed and dropped

`docs/REVIEW-2026-08-21.md:36-45`:

> `usageEvent.create` exists in exactly one place … The data is *right there* and
> dropped: `DesignChangeResult.total_cost_usd` (`design/change.py:77`) is returned
> by the engine and never read by the api; the preview build's `finished` event
> carries `total_cost_usd` and only `app_url`, `manifest`, `whole` and `git_sha`
> are kept.
>
> Billing built on this ledger would undercount the majority of spend.

Recorded independently as the **system's default failure class**, four confirmed
instances — `.claude/agents/architect.md:117-119`:

> The system's default failure is computing an honest signal and dropping it before
> anyone sees it. Four confirmed instances. Check every value you design for its
> consumer.

Step 5 is this row.

## B4 · A job-class call inside a request

`docs/REVIEW-PRODUCTION-READINESS.md:44-49`:

> A 46-minute job lives inside one HTTP request. There is **no job id, no queue, no
> cancellation, no resumability** … If the api restarts, the engine keeps burning
> money on work whose result nobody will receive.

And the intent was already written down and unbuilt — the code's own comment says
the path is *"ignorant of HTTP so the same path can later be driven by a queue
worker"* (`build.service.ts:135`). A written intention is not a transport ruling.

Step 3 is this row.

## B5 · Slow and absent indistinguishable, to the user

`docs/REVIEW-2026-08-21.md:98-107`:

> `DesignPage.tsx:152` and the build screen report a network failure as *"The build
> stopped"* / *"The preview could not be built."* — about a build the server is
> still running. The build screen one line above promises "You can leave this page
> — the build keeps running", and then contradicts itself.
>
> **Fix:** distinguish "we lost the connection" from "the build failed", and
> reconnect rather than declare.

Hit live, in a real session. Step 6's `slow` cell is this row.

## B6 · A cost lever that grew while it went unpulled

`docs/REVIEW-2026-08-21.md:112-119`:

> `grep` finds no `cache_control` anywhere in the engine … Every build-package
> prompt carries a large static prefix — playbook, house rules, architecture slice,
> canonical vocabulary — and B076's chunking, plus today's split, multiply how many
> times that prefix is sent. A package emitted in three chunks pays for the same
> prefix three times. **The lever grew while it went unpulled.**

Step 2's "calls per user action" multiplier is this row.

## B7 · No record of any call

`docs/REVIEW-PRODUCTION-READINESS.md:232-235`:

> Zero occurrences of `import logging` or `logger.` across 17,000 lines. The engine
> runs 46-minute jobs costing dollars and emits nothing but uvicorn's access lines.

And the consequence, `:241-244`:

> There is no way to answer, in production: how many builds ran today, what did
> they cost, which package fails most often, how long does Layer B take, how many
> builds died mid-stream … the estimate model (B077) was calibrated from **two**
> builds because two is all the data there is.

Step 7 is this row. The estimate that resulted: 14–33 minutes predicted against 46
actual (`docs/BACKLOG.md:127`, B077).

## B8 · The artefact that should hold the model, still a heading list

`docs/COSTS.md:1-13` is four headings and parenthetical "(Phase 2)" placeholders,
unchanged as of 2026-08-29 — eight days after
`docs/REVIEW-PRODUCTION-READINESS.md:226-227`:

> For a product whose wedge is *"know the cost up front"*, cost is currently the
> least-enforced thing in the system.

This is why every step above ends in a filled cell rather than a consideration. A
consideration that was raised and not written down did not land — subjects given a
pruned fault tree assigned **.140** where the normative answer was **.468**, and
reached only **.217** when attention was explicitly directed at what was missing.

---

## What is not evidenced here

- **The three latency classes and their thresholds are `unevidenced`.** "Under ~1 s
  is interactive" is a convention, not a measurement. What *is* recorded is the
  consequence of the mismatch (B4), not the boundary between classes.
- **The ledger field list in step 7 is `unevidenced`** — it is derived from the
  five questions B7 says could not be answered, which is a reasonable derivation
  and not a measured one.
- There is **no note in `/home/user/skills-repo/knowledge/notes/` carrying a
  per-claim MEASURED verdict on model-call cost or latency.** The base was ruled
  `thin` for this domain (`docs/agent-spec-llm-component-architect.md` §1b).
  `architecture-evidence.md` carries measured failure modes for distributed systems
  — retry-induced load sustaining metastable failure in **>50%** of studied cases,
  and request **queuing time** rather than CPU as the right overload signal
  (~50% better than CoDel over five years in production) — both of which bear on
  step 6 and neither of which was measured on a model call. Cite them as what they
  are.
