# The seven ways architectures fail

Opened by `architecture-decision` step 4. Each row is a failure mode with a
measured source and an artefact it demands. This is not a quality checklist:
generic checklists measured no better than undirected review, and every entry
here overrides something a competent practitioner does naturally.

Step 4's output is seven rows. `none in scope` is a row; an omitted row is not.

## 1 · Mishandled signalled errors

Yuan et al. (OSDI 2014) traced 198 randomly-sampled failures across five
distributed systems: **92% of catastrophic failures came from incorrect handling
of errors that were explicitly signalled in software**, and **58% of those were
catchable by simple testing of the handler**. The error was not missed; the
handler was wrong.

**Ask:** which error paths does this option create, and does any of them
log-and-continue, catch-all, or `TODO`?

**Artefact:** each new error path with its handler named. A path with no named
handler is a finding.

## 2 · Metastable failure

Huang et al. (OSDI 2022): **retry-induced work is the sustaining effect in over
half of studied metastable failures.** Load returns to normal and the system
stays down, because the retries have become the load.

**Ask:** what retries here, how many times, with what backoff, and with what cap?

**Artefact:** the retry policy in numbers, or an explicit "no retries".

## 3 · The wrong overload signal

WeChat's DAGOR, five years in production: the signal that works is **request
queuing time**, not CPU or memory, and it shed load **~50% better than CoDel**.

**Ask:** when this is overloaded, what does it measure to know, and what does it
drop first?

**Artefact:** the signal, the threshold, and what gets dropped.

## 4 · Dormant code reactivated

Knight Capital repurposed a flag that a dead 8-year-old code path still read,
deployed to 7 of 8 servers, and lost **$460M in 45 minutes**.

**Ask:** does this option reuse a name, flag, column, route or constant that
something else still reads?

**Artefact:** the grep you ran, and its result.

## 5 · Quadratic resource growth

AWS Kinesis, Nov 2020: per-peer threads meant fleet-wide thread count grew with
the **square** of the fleet; a small capacity addition crossed an OS thread
limit; **~17 hours** down.

**Ask:** what in this option grows faster than linearly in tenants, peers, files
or fleet size?

**Artefact:** the term, and the limit it hits first.

## 6 · Boundary crossed the wrong way

The dependency points from the stable thing to the volatile one, or from a lower
layer upward.

Note the strength of the evidence: stable-dependencies as a *principle* is
widely repeated and, as far as these sources go, **never measured against
outcomes**. Run the check because it is cheap and mechanical, not because the
principle is proven. What *was* mechanical here: of 5,173 nodes and 12,054 links
across 276 files, six links violated layer direction, and both sites were seams
an independent review had already named.

**Artefact:** the arrow, and the module names at both ends.

## 7 · The computed signal nobody sees

A value the system honestly computes and then drops before it reaches a person.

This one is not generic — it is the most repeated pattern in this codebase's own
as-built analysis: `validate_plan` produces nine rule ids and returns them to
nothing; `checks_passed` is computed, typed, transmitted and never rendered;
`/usage/allowance` has no consumer; five curation endpoints have no UI. That
document's conclusion: *a rebuild which only surfaced what is already computed
would deliver most of the claimed differentiator without inventing anything.*

**Assume this system's default failure is computing the truth and dropping it.**

**Ask:** what does this option compute that no consumer reads?

**Artefact:** the value, and either its consumer or a backlog item.

## Provenance warning on modes 6 and 7

The instances quoted above are traced to `file:line` in `docs/as-built/`. **That
directory is not present in the working tree as of 2026-08-28** (see
`docs/BACKLOG.md` B128). Two of the four findings it carries forward were
themselves taken on another document's word (F-17, F-04, backlog B127). When you
cite one of these instances in an ADR, mark it `unverified` unless you have just
confirmed it against the code yourself.
