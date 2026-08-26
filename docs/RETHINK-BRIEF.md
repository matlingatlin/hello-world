# The re-think — brief for a fresh session

**Purpose.** Scio is ~26,000 lines across four workspaces and three external
reviews deep. The risk at this point is not that we build badly; it is that the
architecture is now driven by *what already exists* rather than by what the
product is for. This brief exists so one session can hold both thoughts at once:
an honest audit of what we have, and an independent blank-slate answer to what
we are actually trying to solve — so the second is not quietly deformed by the
first.

Run the four steps in order. Do not skip to step 4: its whole value is that the
person doing it has just read everything.

---

## Step 1 — The tooling

Most of this is already configured and travels with the clone
(commit `8e571eb`). Verify rather than re-do:

- `.claude/settings.json` enables **`typescript-lsp`** and **`pyright-lsp`**.
  `.devcontainer/post-create.sh` installs the language server binaries — the
  plugins do not install them, and without them on PATH the config loads and
  does nothing. Check the `/plugin` **Errors** tab.
- `/checkpoint` and `/suites` are real commands in `.claude/commands/`.
- The `PostToolUse` hook applies `ruff check --fix` only. It deliberately does
  not format: 59 of the engine's 125 Python files and 48 TypeScript files
  disagree with `ruff format` / `prettier` as the repo stands, so formatting on
  edit would rewrite untouched files and bury real diffs.

Worth adding, in this order, one at a time — each MCP server widens what an
agent reaches, and this repo has a real key in `apps/engine/.env`:

| | Why here |
|---|---|
| `chrome-devtools-mcp` | Every real bug in this product was found by a browser, not a suite |
| `graphify` | A knowledge graph over three language boundaries and the A→B→C brain |
| `sentry` (official plugin) | B123 is the one review finding nothing has touched |
| `security-guidance` (official plugin) | We ship code other people run |

Deliberately **not** recommended: a Postgres MCP (the reference server is
deprecated, `crystaldba` has been stale since January 2026, and `psql` already
works), and the Prisma MCP (built into the CLI from v6.6.0 — this repo is on
5.22.0, so it needs a major upgrade first).

## Step 2 — Read the repo

Start where the product's shape actually lives, not with a file tree:

1. `CLAUDE.md`, then the per-workspace `CLAUDE.md` in `apps/api`, `apps/app`,
   `apps/engine` — each carries what is true only there.
2. `docs/PRODUCT-OVERVIEW.md` and `docs/UX-FLOW.md` — the seven steps a customer
   walks through.
3. `docs/ARCHITECTURE.md`, `docs/LAYER-B.md`, `docs/LAYER-C.md`,
   `docs/LIBRARY.md` — the A→B→C brain and the component library.
4. `docs/decisions/` — every ADR, in order. This is where the reasoning is.
5. `docs/BACKLOG.md` — grouped by what each open item is *waiting on*: a
   decision, a real run with a key, or infrastructure.

## Step 3 — Read the three reviews, and verify them

- `PRODUCTION_READINESS_REVIEW.GPT.md` (2026-08-24, 18 findings, P1×5)
- `PRODUCTION_READINESS_REVIEW_CLAUDE.md`
- `docs/REVIEW-CONSULTANT-2026-08-22.md`
- `PRODUCTION_READINESS_DIFF.md` reconciles the first two — read it last.

**The discipline that makes this step worth doing: verify every finding against
current code before accepting it.** These reviews are dated, and the code moved
under them. Two examples checked on 2026-08-26:

- **F-17** (project cards are clickable `div`s without keyboard semantics) is
  marked "Verifierat" and is **already fixed** — they are `<button>` elements
  with labels and a status-aware resume, since commit `4ccef44`.
- **F-04** (an active build can be reaped during legitimate silence) is
  **confirmed live**. `parseFrame()` in `apps/api/src/engine/engine.client.ts`
  returns `null` for any frame without a `data:` line — which is exactly what an
  SSE keepalive comment is — so `onEvent` never fires for it and the persistent
  `heartbeatAt` goes stale while the transport is perfectly healthy. Layer B/C
  runs before the first `started` event, the reap cutoff is 15 minutes, and a
  real build has taken 46. This is not theoretical.

Produce a reconciled table: finding → still true / already fixed / partly →
evidence at `file:line`. A finding accepted without that check is a finding that
sends someone to fix code that is already correct.

## Step 4 — The re-think itself

Two passes. Keep them separate, and do the blank-slate one **second but
independently** — write it without looking at the module list, then compare.

**Pass A — what we have.** What is genuinely good and must survive any rewrite;
what exists but is the wrong shape; what is claimed in docs but not real. Be
specific about the parts that are ahead of the field, because they are the ones
most easily thrown away by a refactor: the gates (instrumentation verifier,
console classifier, critique, typecheck, does-it-work-with-data, can-a-guest-
read-another's-row), the `Contract` that makes library matching decidable, the
honest-status vocabulary including `unjudged`, the build-scoped spend ceiling.

**Pass B — blank slate.** Ignore the codebase. Answer, from the problem:

- Who is this for, and what do they have at the end that they could not get
  otherwise? (`docs/PRD.md` and B005 — MVP scope — are still open. This is the
  Phase 1 artifact that was never finished, and everything downstream inherits
  its absence.)
- What is the one thing Scio does that Lovable, v0, Bolt and Dyad do not? The
  current answer is *verification* — the product tells you honestly what works.
  Note that AI-generated code carries confirmed OWASP vulnerabilities in ~25% of
  samples and 1.7× the defects of human code; the market case for gates is
  strong and is not currently stated anywhere in the PRD.
  Note also that Totalum now markets "a real Next.js codebase, driveable by API
  and MCP" — ownership and export is contested ground, not ours by default.
- If you were building it today, what would the pipeline be? Where does the
  current seven-step flow add ceremony rather than confidence?

**Then, and only then, reconcile.** For each difference between A and B: is it
worth changing, and what does it cost? Some differences are the codebase being
wiser than the blank slate — say so when that is the case.

## What to produce

1. The reconciled findings table from step 3.
2. Pass A and Pass B written out, unmerged.
3. A short reconciliation: what changes, what stays, what is explicitly parked.
4. ADRs for anything the re-think actually decides. Per `CLAUDE.md`, the feature
   set, the differentiator and the stack are **not** to be settled silently —
   propose, do not assume.
5. A `/checkpoint` so all of it lands in the repo.

## Two open questions the re-think should not dodge

- **B005 — MVP scope, non-goals, metrics.** Phase 1's unfinished artifact. Every
  "is this in scope" argument since has been decided ad hoc because this does
  not exist.
- **The library as a standard, or as our garden.** shadcn's registry spec
  (`registry.json`, registry-item schema, composition since May 2026) is a
  *distribution format*; our `Entry` is a *trust and matching model* — its
  `Contract`, `Requirement{module, symbols}` and `Quality` have no counterpart
  there, and all three fit in the spec's free-form `meta`. So emitting
  registry-item JSON is an export, not a fork, and it would make our entries
  installable by any shadcn user. Importing the other way is real work: entries
  arrive without a contract, and `generalize`/`gate` would have to derive one.
