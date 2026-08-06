# 0001. Wedge and differentiator

- **Status:** Accepted
- **Date:** 2026-08-06
- **Phase:** 1

## Context
We are building a competitor to Lovable and must choose a beachhead. Lovable owns the
non-technical generalist market (~$200M ARR; ~4 in 5 users non-technical; positioned
horizontally as "anyone with an idea — build anything, without code"). Its weak flank
is code quality, security, and maintainability as an app grows (a public security
incident with default row-level-security gaps; technical debt accumulating in
vibe-coded apps). Cursor owns professional developers. The internal-tools / team
segment is getting crowded. A small new entrant rarely wins by meeting the leader
head-on in its stronghold.

## Decision
- **Wedge:** founders and small teams building software they intend to run and grow —
  not throwaway MVPs.
- **Differentiator:** developer-grade output — clean, reviewable, tested,
  secure-by-default, git-native code that the user owns, with a smooth handoff to a
  real IDE. In short: so good that even developers choose it.
- **Developers are a credibility signal and an escape hatch, not the primary audience**
  (Path A). We are explicitly NOT building a Cursor competitor (Path B).
- **Positioning line:** "The AI app builder for people building for real — code your
  developers actually approve."

## Consequences
- Wedge and differentiator reinforce each other: quality/security/maintainability is
  the buy-reason for exactly this segment (abstract for throwaway builders, acute from
  day one for people building for real).
- We attack Lovable's weak flank rather than its strength.
- Quality, security, and maintainability become first-class product constraints from
  day one, not bolted on. This raises our own engineering bar (secure defaults, tests,
  reviewable output).
- We keep the same product shape (prompt -> generate -> preview -> deploy) and avoid
  the integration/permission complexity an internal-tools pivot would demand.
- Risk: "developer-grade" is a high promise; under-delivering on it breaks trust
  (cf. the trust damage Lovable took from its security incident). It is the core
  promise, so it must actually hold.

## Alternatives considered
- **Non-technical generalists** (Lovable's bullseye) — rejected: head-on with the
  leader plus v0, Bolt, Replit.
- **Developers as the primary user** (a Cursor competitor, Path B) — rejected: Cursor
  owns the segment; it pulls the product toward "control / see the code" and away from
  the "magic" non-technical users want; developers are the pickiest customers and can
  already build themselves.
- **Internal tools / teams** — deferred: crowding, and a materially different product
  (integrations, permissions). Recorded as a later audience.
- **A specific vertical layered on the wedge** — deferred pending whether the founder
  has deep domain expertise in one. If such a vertical exists, "developer-grade + that
  vertical" is a stronger wedge (domain depth is whitespace); to be revisited.
