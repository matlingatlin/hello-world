import { PGlite } from "@electric-sql/pglite";
const db = new PGlite("./.pgdata-rls2");
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

// SET LOCAL only applies inside a transaction — exactly how PostgREST does it.
await db.exec("begin; set local role authenticated; set local request.jwt.claim.sub = 'alice';");
const mine = await db.query("select owner from t");
console.log("inside tx as authenticated, sub=alice ->", mine.rows.map((r) => r.owner));
await db.exec("commit;");

const all = await db.query("select owner from t");
console.log("outside tx as superuser               ->", all.rows.map((r) => r.owner));
await db.close();
