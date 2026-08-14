/** Can RLS be ENFORCED in pglite by mimicking what PostgREST does? */
import { PGlite } from "@electric-sql/pglite";

const db = new PGlite("./.pgdata-rls");
await db.exec(`
  create table if not exists t (id serial primary key, owner text, secret text);
  alter table t enable row level security;
  drop policy if exists only_mine on t;
  create policy only_mine on t for select
    using (owner = current_setting('request.jwt.claim.sub', true));
  do $$ begin
    if not exists (select 1 from pg_roles where rolname = 'authenticated') then
      create role authenticated nologin;
    end if;
  end $$;
  grant select on t to authenticated;
`);
await db.query("insert into t (owner, secret) values ('alice','alice-only'), ('bob','bob-only')");

// This is what PostgREST does per request: assume the role, set the claims.
await db.exec(`set local role authenticated; set local request.jwt.claim.sub = 'alice';`);
const mine = await db.query("select owner from t");
console.log("as 'authenticated' with sub=alice ->", mine.rows.map((r) => r.owner));
await db.exec("reset role;");
const all = await db.query("select owner from t");
console.log("back as superuser              ->", all.rows.map((r) => r.owner));
await db.close();
