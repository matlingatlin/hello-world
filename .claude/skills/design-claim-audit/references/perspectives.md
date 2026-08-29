# The perspectives — pick exactly one per pass

Opened by step 1 of `design-claim-audit`.

These are **not** buckets to sort findings into. A set of categories swept in one
pass is the *checklist* condition, measured no more effective than reviewing with no
procedure at all. What outperformed ad hoc review by ~35% was different readers
running **different procedures hunting different fault classes** — one each, in
separate passes.

Two limits worth knowing before you trust the number: the effect was weakest on
material the reader already knew, with several subjects reporting they *"fell back to
their usual technique"*, and one of the two replications was not significant
(21%, p = 0.21) while the other was (30%, p = 0.0019). Reviewing a system you have
already read is exactly the weak condition. Following the procedure literally, and
recording its artefacts, is what stops the fallback.

**Why one per pass.** On this system, two independent reviews shared most of their
infrastructure findings and diverged on correctness under concurrency and tenancy —
which is where one looked and the other did not. The single most serious finding in
the set appeared in one review only. Redundancy across passes is the point, not
waste.

---

## P1 · Tenancy and identity

**Hunts:** a path that returns or writes another workspace's data.

**Procedure.** Enumerate every read and write in the surface under audit. For each,
name the column or predicate that scopes it. Then look specifically at the paths that
run *before* the scope check: idempotency replay, caches, retries, webhooks,
background jobs, and anything keyed by a client-supplied id. Check that the table
being replayed from carries the tenant column at all.

**Forces:** a table of `operation · scoping predicate · file:line`, and a list of
paths that resolve before scoping.

**Why this one exists:** the worst finding on this system was a replay that ran
before the ownership guard, on a table with no tenant column.

---

## P2 · Failure handling

**Hunts:** an error that is signalled explicitly and then handled wrongly.

**Procedure.** Find every place an error is caught, logged, swallowed or converted.
For each, ask what the caller now believes. Look for: empty catch blocks, catches
that log and continue, warn-and-continue where the process should not have started,
retries with no cap, and handlers with no test.

**Forces:** one row per handler — `file:line · what it catches · what the caller now
believes · is there a test naming it`.

**Why this one exists:** across 198 sampled failures in five distributed systems,
**92%** of catastrophic failures came from incorrect handling of explicitly signalled
errors, and **58%** were catchable by simple testing of the handler. Measured. This
system has a service that logs *"DATABASE_URL not set — running without a database"*
and continues.

---

## P3 · Lifecycle and reachable state

**Hunts:** a state the system can enter and not leave, or declares and never reaches.

**Procedure.** For each status, flag or phase in the surface, find the code that
sets it and the code that clears it. A status with a setter and no reader is dead. A
status with a reader and no setter is unreachable. Then check shutdown, restart,
timeout and cancellation paths: what is left behind, and who reaps it.

**Forces:** a state table — `state · set at file:line · read at file:line ·
reachable? · cleared by what`.

**Why this one exists:** more than half of studied metastable failures were sustained
by retry-induced load. On this system `BuildJob.status = "queued"` is unreachable
because the queue and worker are absent.

---

## P4 · Claim versus artefact

**Hunts:** a document that says something the code refutes.

**Procedure.** Take the document — an ADR, a layer document, the PRD, a README — and
extract its assertions one at a time. Check each against the code, and check each
claim *about another document* by opening that document. Pay particular attention to
summaries and indexes: they are written last, from memory, and go stale first.

**Forces:** one row per assertion — `quote · asserting file:line · artefact checked ·
verdict`.

**Why this one exists:** a blind test of this repository's own index with a fresh
agent failed on two stale claims. A reconciliation document everyone cited turned out
to contain zero references to the things it supposedly reconciled.

---

## P5 · Absence

**Hunts:** what is not there.

**Procedure.** Do not read for what is present. Take each capability the system
claims — deploy, observability, egress policy, secret scanning, signature
verification, shutdown hooks, headers — and grep for the *absence* of its mechanism
by name across the whole tree. A zero-count query is a finding. Then take each
document that promises a list of things and check the list is complete against the
code.

**Forces:** one row per capability — `capability · query run · count · verdict`.
Zero counts are the yield.

**Why this one exists:** in a structured risk-discovery workshop, **57 of 82 risks
were risks of omission versus 25 of commission** (two raters, kappa .82) — and there
was **no relationship** between the business goals stated up front and the risks
actually found, so a goals list will not surface them. Measured. On this system a
review promising nine reveal items shipped a fraction of them, and the unimplemented
endpoint surface was twice as wide as either review reported.

---

## Choosing

If the request names a fault class, take the matching perspective. If it does not,
take **P5 · Absence** first: it has the highest measured yield and it is the one a
reader of a familiar system is least likely to run unprompted.

Then say which of the other four were not run. That sentence is the deliverable's
honesty and it is required by step 1.
