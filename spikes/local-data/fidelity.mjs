/** What this setup does NOT reproduce. Findings need the limits, not just the win. */
import { PGlite } from "@electric-sql/pglite";

const db = new PGlite("./.pgdata-fidelity");
await db.exec(`
  create table if not exists t (id serial primary key, owner text, secret text);
  alter table t enable row level security;
  drop policy if exists only_mine on t;
  create policy only_mine on t for select using (owner = current_setting('request.jwt.claim.sub', true));
`);
await db.query("insert into t (owner, secret) values ($1, $2)", ["alice", "alice-only"]);
await db.query("insert into t (owner, secret) values ($1, $2)", ["bob", "bob-only"]);

const all = await db.query("select * from t");
console.log("rows visible with a policy that should hide them:", all.rows.length);
const who = await db.query("select current_user, session_user");
console.log("running as:", who.rows[0]);
const su = await db.query("select rolsuper from pg_roles where rolname = current_user");
console.log("is superuser:", su.rows[0].rolsuper, "(superusers bypass RLS)");

// GoTrue / auth.uid()
try {
  await db.query("select auth.uid()");
  console.log("auth.uid(): available");
} catch (e) {
  console.log("auth.uid(): NOT available —", e.message.split("\n")[0]);
}
await db.close();
