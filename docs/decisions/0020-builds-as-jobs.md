# 0020. Builds are jobs, not requests

- **Status:** Proposed — needs the planning chat
- **Date:** 2026-08-22
- **Phase:** PP10

## Context

A build is currently an HTTP request that happens to take forty minutes. The
browser posts, the api calls the engine, the engine builds, and the whole thing
exists only as a stack frame in one api process and one engine process. There is
no build id, no queue, no cancellation, and no resume (B094).

What that costs today, in order of how likely each is to be met:

- **A restart loses every build in flight.** Deploy the api, or let the container
  be reclaimed, and a forty-minute build that has spent real money is gone with no
  record of how far it got. The project is left saying `building` until the lock
  ages out.
- **Nobody can cancel.** A build heading somewhere wrong runs to completion and
  bills for it. The only stop is a ceiling that is not a decision anyone made in
  the moment.
- **The api is the queue.** Concurrency is whatever arrives; there is no
  admission control, so the machine's limit is discovered rather than declared.
- **Progress lives only in the stream.** Reconnecting cannot replay what already
  happened, which is why a reconnect (B086) has to re-read the *result* instead of
  rejoining the build.

Three things already blunt the edges, and are worth naming so this is not
oversold: a project-level lock refuses a second concurrent build (and ages out
after 90 minutes, so a crashed build does not lock the project forever); an
idempotency key means a retry replays rather than rebuilds (B103); and a
promotion means the common second build costs nothing at all (ADR-0017). None of
those survive a restart, because none of them are a record of a *build in
progress*.

## Decision

**Proposed**, for the planning chat:

1. **A `build_job` row is created before any work starts**, carrying its own id,
   the project, the spec version, the idempotency key, a status
   (`queued` → `running` → `succeeded` / `failed` / `cancelled`), a heartbeat
   timestamp, and the last progress event. The stream becomes a *view* of the
   job rather than the job itself.
2. **The engine takes a job id and reports against it.** Progress events are
   written to the job as they happen, so a reconnecting client can be handed
   what it missed instead of only the ending.
3. **A worker takes jobs off the queue**, one API process no longer being the
   thing that owns a forty-minute unit of work. What the queue *is* — a table
   with `SELECT … FOR UPDATE SKIP LOCKED`, or a broker — is deliberately left
   open here; the table is the cheaper first answer and it is enough to buy
   restart-safety.
4. **Cancellation is a status transition**, checked by the builder between
   packages. Between packages, not mid-package: a half-written package is worse
   than a finished one nobody wanted, and the loop's natural boundary is where
   the workspace is consistent.
5. **A job whose heartbeat goes stale is reaped and marked failed**, with what it
   had reached recorded. Today's 90-minute project lock is the crude version of
   exactly this, and it should be deleted when this lands rather than left beside
   it.

## Consequences

- Restart-safety, cancellation and admission control all follow from (1) and (3).
  They are not separable features; each one needs the row.
- The api gets simpler, not more complex: it stops owning long work.
- **Metering has to move onto the job.** A cancelled build still spent money, and
  that spend must be recorded — a cancellation that quietly forgives the cost is
  a hole, and worse, an exploitable one.
- Streaming becomes a read of the job's event log, which is what makes a
  reconnect able to rejoin rather than re-read. B086's "Check on it" would become
  "carry on watching".
- Cost: a migration, a worker process, and a real change to how the engine is
  called. This is the largest single piece of work left in the backlog, and it is
  a prerequisite for anything resembling production traffic — the current design
  does not survive a deploy.

## Alternatives considered

- **Keep the request-scoped build and lengthen the timeouts.** Where we are. It
  works on one machine with one user and fails the first time anything restarts.
- **Persist only progress, not the job.** Fixes the display and none of the
  causes: still no cancellation, no queue, no resume.
- **A broker (Service Bus, Redis) from the start.** More moving parts than the
  first version needs, and it can replace the table later without changing
  anything the api or the engine sees.
