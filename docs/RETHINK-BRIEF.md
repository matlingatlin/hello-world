# The re-think — brief for a fresh session

**Purpose.** Scio is ~26,000 lines across four workspaces and three external
reviews deep. The risk at this point is not that we build badly; it is that the
architecture is now driven by *what already exists* rather than by what the
product is for.

**How this brief is built, and why.** An earlier draft of this document did the
exact thing it warned against: it told the blank-slate pass what the answer was
(that the differentiator is verification), listed which parts "must survive any
rewrite", and pre-rejected tools based on the current stack — in a document
whose job is to question the current stack. A blank slate handed a conclusion is
not a blank slate.

So the order below is deliberate and the first step is not negotiable:

> **Write Pass A before opening the codebase, before reading the reviews, and
> before reading the appendix of this file.** Everything you learn afterwards
> makes it impossible to write honestly.

---

## Step 1 — Pass A: the blank slate. Do this first, cold.

You know nothing about how Scio is built. Do not look. Answer from the problem:

- **Who is this for?** Someone who wants software and cannot write it. What do
  they have at the end that they could not get any other way?
- **What is the hard part?** Not "generating code" — models do that. What is the
  part that actually fails, that a person would pay to have solved?
- **What would the flow be?** From "I have an idea" to "I have the thing". How
  many steps, and what is each one *for*? Where would a person lose trust, and
  what has to be true at that moment for them not to?
- **What would you refuse to build?** Non-goals are the half of scope that never
  gets written down.
- **How would you know it worked?** Name the measure before you know what is
  measurable with the current code.

Write it out. It does not need to be long, but it must be *yours* — a position
someone could disagree with, not a summary of options.

`docs/PRD.md` and **B005 (MVP scope, non-goals, metrics)** are still open. This
is Phase 1's unfinished artifact, and every ad hoc scope argument since has
stood in for it. Pass A is the chance to finish it honestly, which is only
possible before the codebase makes some answers feel inevitable.

## Step 2 — The tooling

Configured already and travels with the clone (commit `8e571eb`) — verify rather
than re-do:

- `.claude/settings.json` enables **`typescript-lsp`** and **`pyright-lsp`**.
  `.devcontainer/post-create.sh` installs the language server binaries; the
  plugins do not, and without them on PATH the config loads and does nothing.
  Check the `/plugin` **Errors** tab.
- `/checkpoint` and `/suites` are real commands in `.claude/commands/`.
- The `PostToolUse` hook applies `ruff check --fix` and deliberately does not
  format: measured 2026-08-26, 59 of the engine's 125 Python files and 48
  TypeScript files disagree with `ruff format` / `prettier` as the repo stands.

**Candidates, with facts rather than verdicts.** What is worth installing
depends on what Pass A says we are building, so these are costs and capabilities
to weigh, not a list someone else has already filtered:

| | What it does | What it costs / needs |
|---|---|---|
| `chrome-devtools-mcp` | Console, network, performance traces | 49.7k ★, active |
| `graphify` | Local knowledge graph over the codebase, tree-sitter | 110k ★; adds a PreToolUse hook |
| `sentry` (official plugin) | Error tracking; B123 is untouched | Needs a Sentry account |
| `security-guidance` (official plugin) | Reviews each change for vulnerabilities | First-party |
| `playwright-mcp` | Browser control | Overlaps chrome-devtools-mcp; pick one |
| Prisma MCP | Migrations, schema, queries, Studio | Built into Prisma CLI **from v6.6.0**; this repo is on **5.22.0**, so it needs a major upgrade first |
| Postgres MCP (`crystaldba`) | Query plans, health checks, index tuning | No commit since Jan 2026; open issues from Apr 2025. The old official reference server is deprecated |

One constraint that is not a preference: every MCP server widens what an agent
reaches, this repo has a real key in `apps/engine/.env`, and B104 (prompt
injection) is open. Add them one at a time.

## Step 3 — Read the repo

Start where the product's shape lives, not with a file tree:

1. `CLAUDE.md`, then the per-workspace `CLAUDE.md` in `apps/api`, `apps/app`,
   `apps/engine`.
2. `docs/PRODUCT-OVERVIEW.md`, `docs/UX-FLOW.md` — the seven steps as built.
3. `docs/ARCHITECTURE.md`, `docs/LAYER-B.md`, `docs/LAYER-C.md`,
   `docs/LIBRARY.md` — the A→B→C brain and the component library.
4. `docs/decisions/` — every ADR, in order. The reasoning lives here.
5. `docs/BACKLOG.md` — grouped by what each open item waits on.

Then write **Pass B: what we have.** What is real, what is claimed but not real,
what exists in the wrong shape. Describe, do not yet judge against Pass A.

## Step 4 — The reviews, verified

- `PRODUCTION_READINESS_REVIEW.GPT.md` (2026-08-24, 18 findings, P1×5)
- `PRODUCTION_READINESS_REVIEW_CLAUDE.md`
- `docs/REVIEW-CONSULTANT-2026-08-22.md`
- `PRODUCTION_READINESS_DIFF.md` reconciles the first two — read it last.

**Verify every finding against current code before accepting it.** The reviews
are dated and the code moved under them. Two checked on 2026-08-26, one in each
direction:

- **F-17** (project cards are clickable `div`s without keyboard semantics) is
  marked "Verifierat" and is **already fixed** — they have been `<button>`
  elements with labels and a status-aware resume since `4ccef44`.
- **F-04** (an active build can be reaped during legitimate silence) is
  **confirmed live**. `parseFrame()` in `apps/api/src/engine/engine.client.ts`
  returns `null` for any frame without a `data:` line — exactly what an SSE
  keepalive comment is — so `onEvent` never fires for it and `heartbeatAt` goes
  stale while the transport is healthy. Layer B/C runs before the first
  `started` event, the reap cutoff is 15 minutes, and a real build has taken 46.

Produce a table: finding → still true / already fixed / partly → evidence at
`file:line`. A finding accepted without that check sends someone to fix code
that is already correct, and buries the ones that can destroy a paid build.

## Step 5 — Reconcile

Now put Pass A beside Pass B. For each difference:

- Is the codebase wiser than the blank slate? Sometimes it is — the current
  design may encode a constraint the blank slate did not know about. Say so
  plainly when that is the case.
- Is the blank slate right, and what does moving cost?
- Is the difference simply unfinished work rather than a disagreement?

Only here does the appendix below become safe to read.

## What to produce

1. Pass A, unedited from step 1. Do not retrofit it.
2. Pass B, and the verified findings table.
3. The reconciliation: what changes, what stays, what is explicitly parked.
4. ADRs for anything the re-think decides. Per `CLAUDE.md` the feature set, the
   differentiator and the stack are **not** to be settled silently — propose,
   do not assume.
5. A `/checkpoint`.

---

## Appendix — one session's opinions, formed before the re-think

**Do not read this until step 5.** These are conclusions from the session that
wrote this brief (2026-08-26). They are arguments, not findings, and they exist
here rather than in the steps above so they cannot pass themselves off as the
starting position. If Pass A contradicts them, Pass A is the one that was
written without a stake in the existing code.

- The parts most easily destroyed by a refactor, because their value is not
  visible in their shape: the gates (instrumentation verifier, console
  classifier, critique, app-wide typecheck, does-it-work-with-real-data,
  can-a-guest-read-another's-row); the `Contract` that makes library matching
  decidable rather than a judgment call; the honest-status vocabulary including
  `unjudged`; the build-scoped rather than per-call spend ceiling.
- An argument that the differentiator is *verification* — that the product tells
  you honestly what works. Supporting figure: an AppSec study of 534 samples
  from the six largest models found confirmed OWASP Top 10 vulnerabilities in
  25.1%, with 1.7× the defect rate of human-written code and design-level flaws
  up 153%. Counter-pressure: Totalum now markets "a real Next.js codebase,
  driveable by API and MCP", so ownership and export is contested ground.
- An argument that shadcn's registry spec is a *distribution format* while our
  `Entry` is a *trust and matching model* — `Contract`,
  `Requirement{module, symbols}` and `Quality` have no counterpart there and all
  fit the spec's free-form `meta` — so emitting registry-item JSON would be an
  export rather than a fork. Importing the other way is real work: entries
  arrive without a contract and `generalize`/`gate` would have to derive one.
