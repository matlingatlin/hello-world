# Customer Journey (UX Flow)

> Status: Phase 1. The frontend / customer-facing journey is specified end to end
> (steps 1-7). The engine and everything "behind the scenes" (LLM routing, sandbox,
> vision-loop internals, deploy infra) are deliberately parked for Phase 2 — see the
> carried-in principles near the end for constraints this design imposes.
>
> This is the detailed companion to PRD section 4. Where they differ, this document is
> the more specific source for the customer journey.

## Involvement levels
The user chooses how much they steer, offered AFTER the spec gate (step 3), once the
system understands the project (and it may suggest a level based on complexity):

- Level 1 — wizard only. Wizard -> spec gate -> build directly. No design stage before
  the build.
- Level 2 — wizard + design. Wizard -> spec gate -> design stage with numbered
  annotation -> design gate -> build.

Regardless of level, the user lands in the running app with the SAME numbered-annotation
feedback model (steps 6-7). Level 1 does not remove control — it moves shaping to AFTER
the build (on the running app) instead of BEFORE it (on a preview). The UI should make
this clear so Level 1 does not read as the lesser path.

A possible third, lighter level (pure prompt, no wizard) is out of scope — that is
Lovable's model, not ours.

## Step 1 — Opening / onboarding
- Home -> "Create" -> choose a type: app / website / automation / ...
- Hybrid type selection: a warm opening line ("What do you want to build?") that reads
  free text and suggests the type, plus clear type cards for those who prefer to point.
  A wrong choice is gently steered right.
- MVP: only "app" is active; other types are visible but greyed ("coming soon"). The
  intake is built for multiple types from day one so we do not paint ourselves in.
- Choosing a type initialises a fresh wholeness anchor and the right rule/schema set for
  that type — the first point where a choice parameterises everything downstream.
- Defaults (Phase-2-confirmed, not locked): desktop app; project-first home; only
  "Create" in MVP (repo import is a later escape hatch).

## Step 2 — Requirements wizard (guided conversation)
- Guided conversation: short questions, one at a time, each with a concrete example
  ("Ex: ...") that lowers the barrier, shows what a good answer looks like, and keeps
  answers short. (This replaces an earlier "open with a long free-text description"
  idea, which is dropped.)
- Gap-driven: never asks about what earlier answers already covered; asks only what is
  missing or contradictory; drills into important gaps, fills unimportant ones with a
  reasonable default AND flags it as an assumption.
- Live wholeness panel beside the chat: the whole grows visibly as answers come in;
  anything captured is editable early, so the user corrects as they go rather than
  discovering issues at the gate.
- Quality decisions are first-class here: auth, data ownership, who-sees-what — asked in
  plain language or set to secure defaults. The differentiator starts in the input,
  exactly where Lovable lets it slide.
- Stop at "buildable enough," not "all fields filled" — momentum over form fatigue; the
  rest defaults and is adjusted later.
- If the user gets stuck -> offer concrete choices/examples, not a re-ask.
- Answers are structured into typed fields behind the scenes; the user just talks.

## Step 3 — Spec gate
- The wizard signals it has enough and mirrors back the whole as a COHERENT NARRATIVE —
  the vision told back, organised, gaps reasonably filled, the unspoken made explicit —
  better-formed than the user stated it. Not a field dump.
- Assumptions are marked visibly and separately from what was said; each interpretation
  leap can be accepted, changed, or removed. This is the safety valve against
  over-interpretation — the refinement is reviewable, not silent.
- "No" is surgical, not a restart: it updates only the affected part of the spec/whole
  and re-confirms.
- "Yes" freezes a versioned contract — "approved spec/whole v1" — the contract the build
  and the vision-loop are later measured against. Later changes are diffed against the
  same contract, so the whole is never lost.
- Expectation set: what you approve here is the INTENT; next you react to a DESIGN
  (Level 2) or to the built app (Level 1). Different gates, different things.

## Steps 4-5 — Design preview & annotation (Level 2 only)
- After "yes" on the spec -> a short "thinking" + preview generation step, which includes
  a FEASIBILITY CHECK (is this actually buildable?).
- During generation: calm, smart info texts ("this is only a preview," tips) so the wait
  sets the right expectation.
- Preview opens in the design tool: the preview in the main area, a PROMPT FIELD on the
  right, and TOOLS (draw a line, mark, point, note).
- Numbered annotations: every time a tool is used, that marking gets a NUMBER (1, 2,
  3, ...) on the design.
- The numbers are listed under the prompt field (right); next to each number the user
  writes what they want changed (2: "make this smaller", 3: "move here"). Free prompt
  text and numbered markings coexist; the list is editable before sending.
- "Update" regenerates with all numbered changes + any free prompt AT ONCE — a BATCH
  model (not live per-mark interpretation). Fewer expensive runs; the user sees their
  full change list before it is sent.
- Design is NOT the finished build — expectation set clearly: this is the shape and
  feel, shown cheaply so you can steer direction before the build.
- A marking that contradicts the approved spec is FLAGGED, not silently applied ("this
  changes X you agreed — update the spec too?"). No silent drift; the whole stays intact.
- Iterate until approved; the design gate freezes "approved design v1" — the second
  contract. Errors caught here are cheap, which is the whole point.

## Step 5 (customer side) — Build view
- Design gate passed (or, in Level 1, straight from the spec gate) -> the generation
  window again, now the REAL build.
- This takes time (it may be a large app) — expected, not an error.
- A calm, nice graphic — no technical logs in the user's face.
- Non-blocking: the user can do other things or leave the view while it runs.
- The build runs in the BACKGROUND and sends a NOTIFICATION when done — matching "do
  other things meanwhile" and fitting the wedge (people building for real do not watch a
  spinner).

## Step 6 — Result & reveal
- The graphic gives way to "your app is ready."
- The real, RUNNING app is front and centre — clickable immediately (not a mockup). This
  is the payoff.
- A short, human "what you built," mirrored against the two contracts (it does what you
  agreed; it looks like what you approved) — so the whole visibly arrives.
- A plain-language TRUST RECEIPT: built properly, tested, checks passed, secure defaults
  in place — no logs, no code wall. The vision-loop's work was invisible during the
  build; here it becomes visible as a result.
- HONEST STATUS at reveal: because the vision-loop has a cap (for cost reasons), it
  sometimes reaches the finish with known remainders. We show them honestly — "this
  works; this still needs a look" — grounded, with the remainder/assumption clearly
  marked. Hiding a known flaw is what breaks trust (the lesson from Lovable's security
  incident).
- Orientation, not overwhelming: clear next-step paths (try / change / publish / get
  code) without dumping everything at once.

## Step 7 — Live feedback, versions, ownership, publish

### Live feedback
- The built app opens RUNNING INSIDE our app — fully clickable; the user tests real
  flows.
- Feedback uses the SAME numbered-annotation model as the design stage, now on the
  running app -> "update" -> directed regeneration + the vision-loop again.
- ONE editing model everywhere (intake gate -> design markings -> live markings): mark,
  describe, update in a directed way, preserve the rest, verify. Consistent for the
  user, simpler for us.
- Annotation happens directly on top of the running app, in the state the user is in
  (what you see is what you fix).
- Changes are measured against the two contracts; a contradiction is flagged. Delivery
  is a LOOP, not an endpoint — iterate until satisfied.

### Versions
- Every "update" is a version. A plain-language TIMELINE — each entry human-described and
  linked to the feedback that caused it ("you asked for X -> I changed Y").
- Preview any version live; SAFE ROLLBACK (non-destructive — rollback creates a new
  state, it does not delete forward history).
- MVP: a linear timeline + safe rollback. Branches / "duplicate to experiment" are later.
- Under the hood these are real git commits — so "you own the code" is true for the
  history too; take the code, take the whole history.

### Ownership & export (the differentiator's surface)
- The code always exists and is always yours: a real, clean, readable repo — no locked
  black box.
- "Get your code" = push to your own GitHub (zip as a backup). Desktop + git-native means
  the project is already a local repo.
- Clean handoff package ("hand over to a human dev") — a repo a real developer can pick
  up.
- A living spec/architecture doc that travels with the code — self-documenting, always
  current: take the app, get an up-to-date description of WHAT it is and WHY.
- Deliberately the opposite of Lovable's hosted lock-in.

### Publish
- A "Publish" button -> live on a URL immediately (a non-technical founder must see it
  live in seconds), AND a first-class option to publish to your own infra/domain.
- Throughline: versions, rollback, and publishing are all measured against the two
  contracts + the honest status; publishing a version with known remainders -> an honest
  flag, never silent.

## Behind-the-scenes principles carried in from this design (for Phase 2)
Product-derived constraints the engine must honour. Not the architecture itself (that is
Phase 2), but locked as requirements.

- Directed, incremental update. The system holds ALL of the current app's code (full
  state). Each visual marking (1, 2, 3, ...) maps to exactly the code it touches.
  "Update" regenerates only what should change and keeps everything else untouched. This
  gives: no regressions, fast/cheap runs, and predictable changes — and it is what makes
  the vision-loop tractable (it need only verify what changed against what was, not
  re-judge the whole app each time).
- Two approved contracts. The build and every later change are verified against the
  approved spec/whole and the approved design (Level 2) — "does this match what we agreed
  and what we approved," not just "does this look plausible."
- The whole is never lost, down to the code. Marking -> code coupling -> directed
  regeneration -> the rest preserved, mirroring the intake principle at code level.

## Open decisions (parked)
Recorded so they are not lost; to resolve later.

- Involvement: whether the system suggests a level or leaves it fully open; whether the
  user can change their mind ("build directly" -> still see a design first); whether a
  third lighter level ever exists (likely not — that is Lovable).
- Wizard: exact field-schema per type (ties to the open "fixed vs learning schema");
  wholeness-panel editing UX; what counts as "buildable enough" (the threshold — ties to
  "right number of questions").
- Spec gate: exact confirmation layout (running summary vs "vision + assumptions");
  inline edit vs back-in-chat; pure yes/no vs "approve / adjust."
- Design stage: preview resolution (wireframe vs styled mockup vs light interactive
  prototype — lean: representative and styled but clearly "preview"); which gestures ship
  in MVP (line / ring / note / point — ties to "annotation depth in MVP"); one design
  direction vs a couple of variants; canvas/whiteboard feel vs structured
  screen-by-screen.
- Build view: pure graphic vs a discrete calm status line (lean: minimal, no logs);
  building multiple projects at once; exact "done" transition (auto-open vs "your app is
  ready -> open").
- Reveal: how much "what you built" shows (a sentence vs points against the spec);
  whether the trust receipt expands for the curious (lean: yes, collapsed by default).
- Live feedback / versions: the "use app" vs "mark app" toggle (lean: yes, a clear mode);
  marking anywhere in the flow vs screen-by-screen; auto-label vs custom version names
  (lean: auto, optional rename); compare-two-versions (lean: yes, maybe not MVP); own
  domain in MVP (lean: URL first, domain later); "Publish" and "Get code" as one or two
  surfaces (lean: two clear actions).
- Behind the scenes (Phase 2): how marking->code coupling is held (stable element IDs /
  AST mapping); granularity (component vs element vs row); how a change that must touch
  many places is handled (e.g., "make it all dark theme").
