# Product Requirements (PRD)

> Status: Phase 1 in progress. Decided so far: wedge, positioning, problem,
> differentiator, and the core product flow (below). Still open: feature brainstorm &
> prioritisation, MVP scope, non-goals, success metrics.

## 1. Vision
An AI app builder for people building software they intend to run and grow — turning a
guided conversation into a working app whose code developers actually approve.

## 2. Target users & positioning
**Wedge:** founders and small teams building for real, not throwaway MVPs.

**Positioning:** between Lovable (non-technical, "build anything", but quality and
security degrade as the app grows) and Cursor (an editor for professional developers).
We attack Lovable's weak flank with developer-grade output. Developers are a
credibility signal and an escape hatch, not the primary user.

**One-liner:** "The AI app builder for people building for real — code your developers
actually approve."

**Later audiences (not now):** developers as a primary user, internal-tools teams,
specific verticals.

See ADR 0001 for the full rationale and alternatives.

## 3. Problem
Blank-prompt "vibe" builders let the model guess what the user meant. Output is fast
but degrades: insecure defaults, no tests, accumulating technical debt, and —
critically — lost context as the app grows, so later builds drift from and contradict
earlier decisions. People who build for real either fear the resulting spaghetti or
outgrow the tool. We solve this with three things: requirements captured before
generation, the project's whole kept as a permanent anchor, and developer-grade,
reviewable, secure output.

## 4. Core product flow (decided)
**Entry:** install -> "Create" -> choose a type: app / website / automation / … (each
type has its own rules throughout).

**Step 1 — Requirements wizard.** A rule-driven but dynamic conversation, with its own
rules per type. It always covers the same core fields (consistency), but each next
question depends on prior answers (dynamic — skips the irrelevant, drills deeper where
needed). Every answer is classified and extracted into typed fields — a structured spec
object, not a chat blob — and validated for gaps and contradictions. Alongside the
fields, the system holds the **whole** as its own persistent object (the north star).
Output: a **refined confirmation** — the user's whole, articulated better than they
stated it — behind a yes/no gate. "No" opens a clarification loop and repeats.

**Gate 1 — spec / whole approved** -> triggers Step 2.

**Step 2 — Generation & design.** The approved spec is prompt-built holistically; an
engine routes to the best LLM per category. Output: a design shown in a GUI preview
with tools — draw lines, mark up, annotate — interpreted directly. Iterated in the GUI
until approved.

**Gate 2 — design approved** -> triggers the build.

**Step 3 — Build.** The engine plus the self-testing vision loop (generate -> render ->
screenshot + console -> critique -> fix) run behind the scenes, evaluating the build
against **two approved contracts**: the spec/whole and the design — not just "does this
look plausible" but "does the build match both what we agreed and the design we
approved."

**Order:** spec gate -> design gate -> build (confirmed).

**Involvement levels:** the design stage and its gate are optional. The user chooses
after the spec gate — Level 1 (wizard only): spec gate -> build; Level 2 (wizard +
design): spec gate -> design gate -> build. Regardless of level, feedback on the running
app uses the same numbered-annotation model. The full customer journey is specified in
docs/UX-FLOW.md.

### Two load-bearing principles
1. **The whole is never fragmented or lost.** Categorisation must not shatter the
   vision into loose fields. The whole is a permanent anchor that every step and every
   later change is checked against, so change #47 never silently contradicts the vision
   or an earlier decision.
2. **Confirmations refine intent, not parrot words.** "If I understood correctly…" is a
   better-formed version of what the user meant — organising scattered thoughts, filling
   obvious gaps with reasonable interpretation, making the unspoken explicit. It must be
   grounded (derived from what they said plus sensible defaults), clearly mark
   assumption vs stated, and be easy to correct. The yes/no gate is the safety valve.

## 5. Differentiator & MVP scope
**Differentiator (decided):** developer-grade code (see ADR 0001).

**MVP scope (open):** PM lean is to ship one type — app — first, with website and
automation as later modes; depth of the annotation interpretation in the MVP to be
decided. Not yet locked.

## 6. Non-goals
Decided so far: not a professional-developer IDE / Cursor competitor; not optimising
for throwaway MVPs as the core case; public launch, live billing, and full hardening
are out of scope until after a testable alpha. Remainder: Phase 1 continues.

## 7. Success metrics
Phase 1 continues — not yet defined.

## Open decisions (to resolve as Phase 1 continues)
- MVP on one type (app) first — lean, not locked.
- How deep the annotation / mark-up interpretation is in the MVP.
- Model routing ("best LLM per task") — treated as a Phase 2 optimisation; start with
  one strong model.
- Fixed vs learning category schema (designed per type, or expands over time).
- How large an interpretation leap the refined confirmation may take on its own.
