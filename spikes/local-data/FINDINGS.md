# Spike: can a generated app run WITH DATA in this sandbox, without Docker?

**Date:** 2026-08-12 · **Status:** answered · **Verdict: YES — approach A works.**

A generated booking app persisted a real booking through its own UI, against an
in-process PostgreSQL, inside the Claude Code sandbox, with no Docker, no daemon
and no external Supabase project. The row survived both a page reload and a full
process restart.

```
1. the list starts empty (nothing seeded)
     rows before: 0
2. fill the real form and submit it
  PASS  the app confirms the booking — Your booking is confirmed.
3. RELOAD a different page — is it still there?
  PASS  the list grew by one — 0 -> 1
  PASS  the booking is visible after reload
4. is it actually in the DATABASE, not just the page?
  PASS  the row exists in Postgres — id=2855b218-ecde-4639-a891-f6c3724e3656
  PASS  the values round-tripped — party_size=4
  PASS  no console errors from the app

VERDICT: persistence verified
```

## What was actually run

- **The fixture is the real thing.** `app/` holds the booking blueprint's code,
  emitted by the engine's own `CatalogEntry.adapt("booking")` — the same files a
  build assembles. Not a hand-written mock of it.
- **The app code is unchanged.** It still calls
  `getSupabaseClient().from("bookings").select(...)`. One module was swapped:
  `lib/supabase.ts` returns a pglite-backed client with the same
  `{ data, error }` shape (approach A).
- **Nothing was seeded.** The row was created by filling the form and pressing
  the button, driven headless by Playwright through the app's own server action.
- **The database was inspected directly** (`/api/spike/rows`, spike-only) so the
  evidence is "the row is in Postgres", not "the page says so".

## What works

| | |
|---|---|
| `@electric-sql/pglite` in this sandbox | ✅ PostgreSQL **18.3** compiled to WASM, in-process |
| Install cost | ✅ one npm package, ~2s, no native build |
| The app's SQL | ✅ `uuid` PKs, `gen_random_uuid()`, `timestamptz`, `check` constraints, `create policy` — all accepted unchanged |
| Persistence across a page reload | ✅ |
| Persistence across a **process restart** | ✅ file-backed `PGDATA` (~39 MB on disk) |
| Insert / select / update via the shim | ✅ the surface the blueprint uses |
| Playwright driving the real form | ✅ using the sandbox's own Chromium |

## The fidelity gap — what this does NOT reproduce

**1. RLS is not enforced by default, but CAN be.** pglite connects as `postgres`,
a superuser, and superusers bypass row-level security. Measured: a policy that
should have hidden one of two rows hid neither.

The fix is the same thing PostgREST does per request, and it works here:

```sql
begin;
set local role authenticated;
set local request.jwt.claim.sub = 'alice';
-- select now returns only alice's rows
commit;
```

Measured: `inside tx as authenticated, sub=alice -> ['alice']`. Note `SET LOCAL`
is a no-op outside a transaction — the first attempt silently changed nothing and
looked like "RLS cannot work here". It can.

**2. There is no GoTrue / `auth` schema.** `select auth.uid()` fails with
`schema "auth" does not exist`. Any generated policy written as
`using (user_id = auth.uid())` — the Supabase idiom — will not even parse a
policy check until an `auth` schema with a `uid()` shim exists. That is a small
piece of SQL, not a wall.

**3. This is not PostgREST.** The shim implements the calls the booking blueprint
makes (`select/is/order`, `insert/select/single`, `update/eq`) and throws loudly
on anything else. A different generated app using `.in()`, `.gte()`, `.rpc()` or
embedded resource selects (`select("*, guest(*)")`) would hit an unimplemented
method. Approach B (pglite + the PostgREST binary) removes that ceiling entirely
and was not needed for this question.

**4. Single writer.** pglite is one instance per process. Two Node processes
pointed at one `PGDATA` is not supported, and the failure is ugly rather than
loud. Seen in this spike: deleting the data directory under a running server left
the process serving stale rows while new writes went nowhere — the insert
reported success and the row was gone. **Verification must own the lifecycle:**
create the directory, start the app, run, then stop and discard.

## What to carry into B060

1. **Build B060 on this.** The premise holds: interactive verification with real
   persistence is possible in Claude Code. It does not need Docker and does not
   need a Supabase project.
2. **Ship the shim as a "verification client" in the library**, not as app code.
   The generated app must keep importing `@/lib/supabase`; verification swaps the
   module (env-gated), so what ships to the user is unchanged and what is verified
   is the user's real code.
3. **Enforce RLS in verification.** Run app queries inside a transaction as a
   non-superuser role with the claim GUCs set. Then "a guest cannot read another
   guest's booking" becomes a *testable* criterion instead of an `unobservable`
   one — which is exactly the class of acceptance criteria B054 had to scope out.
4. **Add an `auth` schema shim** (`auth.uid()` reading the claim GUC) so generated
   Supabase-idiom policies run as written.
5. **Own the database lifecycle per build**, one process, fresh directory. Treat
   `PGDATA` as build output; never share it between processes.
6. **Watch the size.** ~39 MB per database. Per-project, per-build, this needs a
   cleanup policy alongside the workspace and dev-server cleanup already noted in
   the runbook.
7. **Keep approach B in the back pocket.** The moment a generated app uses a
   PostgREST feature the shim lacks, swapping in the real PostgREST binary against
   the same pglite instance is the escape hatch — the database layer does not
   change.

## Reproducing

```bash
cd spikes/local-data/app
npm install
rm -rf .next .pgdata                 # order matters: never clear under a running server
npm run dev -- --port 45002 &
cd .. && SPIKE_BASE=http://127.0.0.1:45002 node verify.mjs
```

`fidelity3.mjs` reproduces the RLS result; `fidelity.mjs` reproduces the
superuser-bypass and missing-`auth`-schema findings.

**Not production.** Everything here is a fixture. Nothing in `spikes/` is wired
into `apps/`, and the shim is deliberately incomplete.
