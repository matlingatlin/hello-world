# @scio/app — the Scio web app

React + TypeScript + Vite + Tailwind, tokens from `docs/DESIGN.md`. Step 1 of porting
`prototype.html`: **Projects and Create are wired end-to-end** (Clerk sign-in → API →
Postgres); the other screens are placeholders until step 2 (B022). `prototype.html` in
this directory remains the exact visual reference.

## Run the full stack locally

```bash
# 1. Postgres (repo root)
docker compose up -d db

# 2. Backend
cd apps/api
cp .env.example .env          # set CLERK_SECRET_KEY from the Clerk dashboard
pnpm prisma:migrate && pnpm prisma:generate
pnpm dev                      # http://localhost:3000

# 3. Frontend
cd apps/app
cp .env.example .env          # set VITE_CLERK_PUBLISHABLE_KEY (same Clerk instance)
pnpm dev                      # http://localhost:5173
```

Sign in via Clerk, create a project, reload — it persists, scoped to your workspace.

Degraded modes (by design): without `VITE_CLERK_PUBLISHABLE_KEY` the app shows a
config notice instead of crashing; with auth but no backend, Projects shows a clear
"can't reach the API" error state with retry.

## Scripts

- `pnpm dev` / `pnpm build` / `pnpm preview`
- `pnpm test` — vitest (API client with mocked fetch + component render tests)
- `pnpm lint` — typecheck
