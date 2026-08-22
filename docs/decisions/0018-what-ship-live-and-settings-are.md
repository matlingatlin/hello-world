# 0018. What "Ship", "Refine" and "Settings" actually are

- **Status:** Proposed — needs the planning chat
- **Date:** 2026-08-22
- **Phase:** PP8 (delivery) / PP9 (the account)

## Context

The reveal ends with three actions, and until today all three led to a screen
that said it was being ported from the prototype (B022, B084). One of them turned
out to need no decision at all and is already wired; the other two need one.

**"Open & refine" → the design window.** No decision required. Since ADR-0017 a
delivery build *promotes* the design workspace rather than rebuilding it, so the
app the user shaped and the app they were handed are the same files, with the
same history. Refining a delivered app is the design window pointed at it. Done.

**"Get the code"** now has an honest screen: the version, the commit, when it was
built, and a plain list of what is not built — downloading the repository,
pushing it to the user's own remote, publishing it. What each of those *should*
be is the open question.

**"Settings"** is still a placeholder, and B049 wants the model-passes control to
live there ("1 = same model twice; more = best → review → best"). That control is
real — `run_profile()` reads it — but it is read from the environment, which
makes it an operator setting, not a user one. Making it a user setting means
per-workspace persistence and a price consequence, which is a product decision.

## Decision

**Proposed**, for the planning chat to accept, amend or reject:

1. **"Get the code" means git, not a zip.** The product's claim is *you own the
   code, history included* — a zip is a snapshot and quietly drops the history
   that makes the claim true. The first implementation is "push this repository
   to a remote you own", authenticated with the user's own GitHub. A download
   remains a fallback for people who do not want to connect an account.
2. **"Publish" is out of scope until there is a hosting decision.** Its screen
   says so by name rather than by absence. ADR-0004/0005 chose Azure for *our*
   infrastructure; nothing has been decided about where a *user's* app runs, who
   pays for it, or what happens to it when they stop paying — and each of those
   is a commitment that is very hard to reverse once someone's app is live on it.
3. **Settings is an account screen, and the model profile does not go in it
   yet.** What belongs there first is what the user already has and cannot see:
   what they have spent, what is running, and how to stop it. Exposing "how hard
   should Scio work" to a user needs the pricing decision (B063) first — the
   whole point of the control is that it costs more.

## Consequences

- The reveal stops promising three things and delivering one. Two of its actions
  are real; the third is named as unbuilt on the screen itself, in one sentence,
  rather than found by clicking.
- Deciding (1) pulls in a GitHub OAuth scope and a token store — a real security
  surface, and one worth its own pass rather than a corner of this one.
- Deferring (2) leaves the product's final step manual for now. That is honest
  while the stack is one Codespace; it will not survive contact with a paying
  user, and it is the largest single gap between here and a sellable product.
- Deferring (3) keeps `SCIO_MODEL_PASSES` an operator knob, which is exactly what
  it is today.

## Alternatives considered

- **Build all three screens now, on assumptions.** The fastest way to have three
  screens nobody wants and a hosting bill nobody agreed to.
- **A zip download as "get the code".** Cheaper, and it makes the ownership claim
  smaller than it currently is. The history is the differentiator.
- **Leave the placeholders.** They read as "not finished" on the one screen whose
  subject is ownership. A sentence saying what is missing is worth more than a
  button that apologises.
