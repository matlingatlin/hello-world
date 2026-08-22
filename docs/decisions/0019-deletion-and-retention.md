# 0019. What deletion deletes, and what survives it

- **Status:** Proposed — the retention windows need the planning chat
- **Date:** 2026-08-22
- **Phase:** PP9

## Context

"Delete" meant `deleted_at = now()` on a project row (B100). The workspace, its
git history and its screenshots stayed on disk indefinitely; the preview kept
answering on its port. A deleted project was a *hidden* one, which is not what
the word means to the person who clicked it. `user.deleted` did nothing at all.

Some of this is now fixed and needed no decision: deleting a project stops its
app and removes its workspace, and the row is marked deleted whether or not the
files went — a directory that will not delete must not keep the project alive,
but it is logged rather than reported as success, because the failure to avoid is
telling someone their code is gone while it sits on our disk.

What is left is genuinely a decision, because it trades two real obligations
against each other: a person's right to have their data removed, and the
requirement to keep an auditable record of what they were charged for.

## Decision

**Proposed**, for the planning chat:

1. **Billing records survive project deletion.** `usage_event` says what was
   spent from a workspace's allowance; a charge that vanishes when its project
   does is not a ledger. It is already implemented this way. What it must not
   keep is anything about *what the app was* — the rows hold a project id, a
   kind, a cost and a token count, and nothing else. That is what makes keeping
   them defensible.

2. **Project deletion is immediate, not deferred.** No trash, no 30-day window.
   A window is a promise to keep someone's code after they asked us not to, and
   it needs a restore path to be worth anything — which is a feature, not a
   default. Until "undelete" exists as something a user can see and use, the
   honest behaviour is to delete when asked.

3. **Account deletion cascades to projects and stops there.** Every project is
   deleted as above; the workspace row, the user row and the billing history are
   retained for the statutory record-keeping period (proposed: **7 years**, the
   usual accounting requirement — needs confirmation for the jurisdiction we
   actually operate in), with everything that identifies the person removed at
   deletion time rather than at the end of it.

4. **The library keeps what it learned.** A contributed component is generalised
   before it is stored (ADR-0016) — project terms removed, values blanked — so
   what is in the catalog is not the user's app. Withdrawing it on deletion would
   also mean withdrawing it from every app that has since been built on it. What
   must be checked before this is settled is whether the generalisation is
   *actually* thorough enough to say that, on real contributed entries rather
   than fixtures.

## Consequences

- (2) means a mis-click is unrecoverable. That is a real cost, and the reason to
  build an explicit undelete rather than a silent grace period.
- (3) needs a legal answer, not an engineering one. The 7 years above is the
  common default and should not be treated as researched.
- (4) is the one with a hidden dependency: if generalisation leaks, deletion
  cannot be honoured, and we would not find out from this ADR. It needs its own
  check against real entries.
- None of this is enforceable until account deletion exists at all — `user.deleted`
  is still a column nothing writes to.

## Alternatives considered

- **Soft-delete everything forever.** What we had. Cheap, and it makes the word
  "delete" a lie.
- **A 30-day trash.** Familiar, and it is what most products do. It is also a
  promise to hold code after being asked not to, and without a restore button it
  buys the user nothing at all.
- **Erase the billing rows too.** Clean for the user, and it removes our own
  record of what we charged them — which protects neither side in a dispute.
