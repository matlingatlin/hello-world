# Placement — the recorded failures this procedure exists to prevent

Every row is a real, recorded run in this repository, written by somebody other
than the author of this skill, and dated before this skill existed. Cite the
`file:line`, not this file, when a ruling rests on one.

**Provenance note.** These rows are `MEASURED` in the weak sense that they were
observed and written down with numbers, in one system. They are **not** a study.
The general principles in the procedure that do not trace to a row here are marked
`unevidenced` below, and there is no note in
`/home/user/skills-repo/knowledge/notes/` carrying a per-claim MEASURED verdict on
model-call placement — that base was ruled `thin` for this domain
(`docs/agent-spec-llm-component-architect.md` §1b).

---

## P1 · A model call on a read path — the coverage failure

`docs/BACKLOG.md:121` (B071):

> The whole + estimate are recomputed on every GET /intake: ~12s and a real Layer
> B+C model call per page load

The fix, with both numbers recorded — `docs/BACKLOG.md:243-245`:

> `GET /intake` went from **12.7s to 0.008s** and now makes no model call at all —
> the whole and the estimate are stored with the spec that produced them.

And re-measured at `docs/BACKLOG.md:226`:

> `GET /intake` answers in **7–16 ms** and makes no model call.

**The deterministic mechanism was "stored value".** Roughly 1,500× on latency and
the whole per-request cost, from moving one call off a read path.

**Why the procedure enumerates first.** This system's instinct about determinism
was *good* — `docs/REVIEW-2026-08-21.md:201-204` calls the deterministic gates
"real", and `docs/SECURITY.md:56-60` explains why code "cannot be talked out of its
opinion". The call survived anyway because nobody had listed the paths that made
one. Enumeration, not persuasion.

## P2 · The same failure with a multiplier

`docs/BACKLOG.md:125` (B075):

> The app fetches /intake twice per page load (React StrictMode double-mount) —
> free now, but it doubled the old cost

A misplaced call's cost is multiplied by every caller you did not enumerate. Step
1's hit count exists for this.

## P3 · A model call with no boundary of its own

`docs/REVIEW-2026-08-21.md:151-158`:

> `build_package` (**226 lines**, `builder/loop.py:527`) … holds the attempt loop,
> the snapshot/rollback, five gates, the critique call, remainder collection and
> persistence — six responsibilities in one scope. That is where the last three
> bugs lived … Not a coincidence.

The critique call cannot be timed, stubbed, substituted or failed over
independently, because it does not exist as a separate thing. Step 4's
`isolated: yes / no` cell is this row.

## P4 · A ruling done right — the negative control

`docs/BACKLOG.md:96` (B046):

> Cost estimate (deterministic, from plan + library hits) — **done**

This is a step that could plausibly have been a model call and correctly is not.
**When this procedure runs over this repo, B046 must come back `keep as
deterministic` with no finding.** A procedure that flags it has produced noise.

Note the split: the *money* estimate is deterministic and fine; the *time*
estimate was miscalibrated — 14–33 minutes predicted against 46 actual
(`docs/BACKLOG.md:127`, B077). That is a budget row, not a placement row, and it
belongs to `model-call-budget`.

---

## What is not evidenced here

- The candidate list in step 2 (stored value, lookup table, parser, rules engine,
  gate, cache, earlier step, human) is **`unevidenced`** — it is an enumeration we
  find useful, not a measured taxonomy.
- The claim that reading a justification before naming an alternative degrades the
  alternative rests on the design-fixation measurement (self-generated concept
  0.32 vs provided example 0.24,
  `/home/user/skills-repo/knowledge/notes/design-fixation-and-anchoring.md`) which
  is about *design concepts*, not about model-call placement. The transfer is an
  argument, not a measurement. Marked **`unevidenced` by transfer**.
- The `keep / replace / hybrid / unstated` vocabulary is ours. No measurement says
  four categories beat three.
