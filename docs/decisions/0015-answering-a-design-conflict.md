# 0015. Answering a design conflict: inline, with allowances for security

- **Status:** Accepted
- **Date:** 2026-08-19
- **Phase:** PP6 (gate 2b — the design window)

## Context

Gate 2a made a marking that argues with the approved spec come back as a *question* rather
than a build: "you said no payments for now — do you want them after all?". It deliberately
stopped there. Somebody still has to answer, and gate 2b had to decide where and how.

Three kinds of conflict are detected, and they are not equally serious:

- `non_goal` — the marking asks for something the spec deliberately excluded.
- `auth` — the marking asks to remove sign-in the spec says the app needs.
- `access` — the marking asks to make data the spec marked sensitive public.

The forces pull in opposite directions. **Usability**: sending someone back through the
wizard to say "actually anyone should see the menu" is bad product, and a design window that
punishes you for changing your mind is one people stop marking things in. **The wedge**
(ADR-0001): Scio's differentiator is that the boring, invisible, correct things — sign-in,
row-level security, ownership — are *derived from the spec* and not left to whoever remembers
to ask for them. A side panel that can quietly delete those derivations undoes the wedge, and
it undoes it in the one place where nothing on screen would look different.

## Decision

**All three kinds are answered inline, in the design window, and never require a trip back to
the wizard.** Each conflict offers exactly two answers: *Keep it as-is*, which drops that one
marking and builds nothing, and *Change the plan*, which is a real amendment to the approved
spec (`POST /projects/:id/spec/amend`), frozen as a new `spec_version`.

**What "Change the plan" does differs by kind, because the acts differ:**

- `non_goal` → the non-goal is **removed from the spec**. Exact and complete: the architecture
  stops excluding it, so the conflict is genuinely gone.
- `auth` / `access` → a **second, distinct confirmation** that names the protection by the
  exact sentence the question quoted, and then an **allowance** is appended to the spec
  version. The security posture is *not* rewritten. The spec still says the data is sensitive,
  because it is; what is recorded is that the user was asked, in those words, and said yes.

An allowance silences exactly one question — matched on the `spec_says` string the question
used — and nothing else. It is the only mechanism by which a conflict stops being one.

## Consequences

- Changing your mind about scope costs two clicks, and the change is in the record where a
  future reader can see when and why the spec moved.
- A security decision cannot be reversed by accident, cannot be reversed silently, and cannot
  be reversed in bulk. Reversing one leaves a frozen, readable artefact naming what was
  allowed.
- **Known cost, and it is real:** an allowance lets the code and the posture drift. The
  architecture keeps deriving protections that the code was permitted to skip, so a later
  build can re-derive something the user thought they had removed. The window says as much —
  "if the app should work a different way altogether, change it in the wizard" — and the
  honest fix for a *structural* change is still gate 1.
- Detection stays deterministic and narrow (gate 2a's decision, unchanged). An allowance is a
  string match on a quoted sentence, not a judgment call, for the same reason.

## Alternatives considered

- **Send security conflicts back to the wizard.** Safest, and the reason it was rejected is
  that it makes the design window feel like it is punishing you: the marking is lost, the
  wizard reopens, and the user has to reconstruct what they were doing. It also spends the
  user's patience on the case where they are most likely right about their own product.
- **Let "Change the plan" rewrite the security posture.** Simplest to implement and the
  cleanest-looking outcome — the conflict disappears because the architecture genuinely no
  longer wants the protection. Rejected: derived security that a side panel can un-derive is
  not derived security, and the drift it avoids is worth less than the guarantee it destroys.
- **Treat all three kinds identically.** Fewer paths, but it makes "drop sign-in" feel exactly
  like "we do want payments after all", which is precisely the flattening this ADR exists to
  prevent.
