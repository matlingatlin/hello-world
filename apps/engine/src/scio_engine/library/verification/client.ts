/**
 * VERIFICATION ONLY — the app's data client, backed by in-process Postgres.
 *
 * This file NEVER ships. It is written into `.scio/verification/` and aliased
 * over `@/lib/supabase` by next.config.js, and only when SCIO_VERIFY_DATA=1.
 * The user's own `lib/supabase.ts` — which imports real @supabase/supabase-js —
 * is untouched on disk and in git. What we verify is the user's code; what the
 * user gets is the user's code.
 *
 * Why it exists: without data, a build can only be checked for "does it render".
 * "The booking actually saves" and "a guest cannot read another guest's booking"
 * were criteria Layer C had to scope out as unobservable (B054). With a real
 * PostgreSQL in-process (pglite, proven in spikes/local-data) they become
 * checkable, which is the point of the whole exercise.
 *
 * Two things make it faithful rather than merely convenient:
 *
 * 1. **RLS is enforced.** pglite connects as `postgres`, a superuser, and
 *    superusers bypass row-level security — so a naive setup would report every
 *    policy as working. Every app query therefore runs inside a transaction as
 *    the non-superuser `authenticated` role with the JWT claim GUCs set, which
 *    is exactly what PostgREST does per request. `SET LOCAL` outside a
 *    transaction is a silent no-op; that is why the transaction is not optional.
 *
 * 2. **It refuses what it does not implement.** An unimplemented filter throws
 *    rather than returning no rows: a shim that quietly answers "nothing found"
 *    would make a broken app look empty and a working app look broken.
 */

import { readFileSync } from "node:fs";
import { PGlite } from "@electric-sql/pglite";

const DATA_DIR = process.env.SCIO_VERIFY_PGDATA ?? "./.scio/verification/pgdata";
const SCHEMA_FILES = (process.env.SCIO_VERIFY_SCHEMA ?? "").split(":").filter(Boolean);

/** Who the current request is acting as. Empty = anonymous. */
const DEFAULT_ACTOR = process.env.SCIO_VERIFY_ACTOR ?? "";

/**
 * The Supabase surface a generated app expects from the database itself:
 * an `auth` schema whose `uid()` reads the request's claim. Generated policies
 * are written as `using (user_id = auth.uid())`, and without this they do not
 * even resolve.
 */
const AUTH_SHIM_SQL = `
create schema if not exists auth;

create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

create or replace function auth.role() returns text language sql stable as $$
  select coalesce(nullif(current_setting('request.jwt.claim.role', true), ''), 'anon')
$$;

create or replace function auth.email() returns text language sql stable as $$
  select nullif(current_setting('request.jwt.claim.email', true), '')
$$;

do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
end $$;
`;

/**
 * Grants run AFTER the app's schema, so tables that did not exist when the roles
 * were created are still reachable.
 *
 * Both roles get full table privileges on purpose — that is how Supabase itself
 * is set up, and it is the point: **the POLICY decides, not the grant.** A
 * tighter grant looks like RLS working and is not. It also breaks apps with no
 * accounts at all: the booking blueprint's guests are anonymous, and a
 * `grant select`-only anon could not insert the booking its own policy allows.
 */
const GRANTS_SQL = `
grant usage on schema public, auth to authenticated, anon;
grant all on all tables in schema public to authenticated, anon;
grant all on all sequences in schema public to authenticated, anon;
grant execute on all functions in schema auth to authenticated, anon;
`;

/**
 * The instance lives on globalThis, not in a module-level variable.
 *
 * Next bundles server components and server actions separately, so this module
 * is INSTANTIATED TWICE in one process — and a module-level singleton would give
 * each bundle its own PGlite on the same directory. pglite is single-writer: the
 * second one re-ran the schema and failed with "relation already exists", and
 * had it not failed the two would have been quietly corrupting each other.
 * One process, one database.
 */
const INSTANCE_KEY = Symbol.for("scio.verification.pglite");

/**
 * The acting user lives beside it, and for the same reason. The harness sets it
 * through an API route; the pages that must obey it are server components. Those
 * are different bundles, so a module-level `let` would leave the route setting an
 * actor nobody reads — and an isolation check that always ran as the same user
 * would pass whether or not the policies work.
 */
const ACTOR_KEY = Symbol.for("scio.verification.actor");

type Global = typeof globalThis & {
  [INSTANCE_KEY]?: Promise<PGlite>;
  [ACTOR_KEY]?: string;
};

function database(): Promise<PGlite> {
  const scope = globalThis as Global;
  if (!scope[INSTANCE_KEY]) {
    scope[INSTANCE_KEY] = (async () => {
      const db = new PGlite(DATA_DIR);
      await db.exec(AUTH_SHIM_SQL);
      for (const file of SCHEMA_FILES) {
        // The app's OWN migration, verbatim. Applied once per database; a
        // re-run against an existing one is not an error, because the database
        // outlives a dev-server recompile.
        try {
          await db.exec(readFileSync(file, "utf8"));
        } catch (error) {
          if (!/already exists/i.test((error as Error).message)) throw error;
        }
      }
      await db.exec(GRANTS_SQL);
      return db;
    })();
  }
  return scope[INSTANCE_KEY]!;
}

type Row = Record<string, unknown>;
type Result<T> = { data: T; error: { message: string } | null };

function quote(identifier: string): string {
  if (!/^[a-z_][a-z0-9_]*$/i.test(identifier)) {
    throw new Error(`unsafe identifier: ${identifier}`);
  }
  return `"${identifier}"`;
}

function literal(value: string): string {
  return `'${value.replace(/'/g, "''")}'`;
}

/** A thenable builder: filters chain, SQL is built when awaited. */
class Query implements PromiseLike<Result<unknown>> {
  private wheres: string[] = [];
  private params: unknown[] = [];
  private orderBy = "";
  private limitTo = "";
  private wantsSingle = false;
  private returning = false;

  // Declared explicitly rather than as constructor parameter properties: Node's
  // type-stripping mode refuses those, and this file has to be runnable by plain
  // `node` so the harness can drive it without a build step.
  private table: string;
  private kind: "select" | "insert" | "update" | "delete";
  private payload?: Row;

  constructor(table: string, kind: "select" | "insert" | "update" | "delete", payload?: Row) {
    this.table = table;
    this.kind = kind;
    this.payload = payload;
  }

  select(_columns = "*") {
    if (_columns.includes("(")) {
      // Embedded resources are a PostgREST feature, not SQL we can fake.
      throw new Error(
        `the verification client does not implement embedded selects (${_columns}). ` +
          "Run the real PostgREST against the same database if a generated app needs them.",
      );
    }
    this.returning = true;
    return this;
  }

  is(column: string, value: null) {
    if (value !== null) throw new Error("verification client: .is() only supports null");
    this.wheres.push(`${quote(column)} is null`);
    return this;
  }

  eq(column: string, value: unknown) {
    this.params.push(value);
    this.wheres.push(`${quote(column)} = $${this.params.length}`);
    return this;
  }

  neq(column: string, value: unknown) {
    this.params.push(value);
    this.wheres.push(`${quote(column)} <> $${this.params.length}`);
    return this;
  }

  gte(column: string, value: unknown) {
    this.params.push(value);
    this.wheres.push(`${quote(column)} >= $${this.params.length}`);
    return this;
  }

  lte(column: string, value: unknown) {
    this.params.push(value);
    this.wheres.push(`${quote(column)} <= $${this.params.length}`);
    return this;
  }

  order(column: string, options?: { ascending?: boolean }) {
    this.orderBy = ` order by ${quote(column)} ${options?.ascending === false ? "desc" : "asc"}`;
    return this;
  }

  limit(count: number) {
    this.limitTo = ` limit ${Number(count)}`;
    return this;
  }

  single() {
    this.wantsSingle = true;
    return this;
  }

  maybeSingle() {
    this.wantsSingle = true;
    return this;
  }

  private sql(): { text: string; values: unknown[] } {
    const where = this.wheres.length ? ` where ${this.wheres.join(" and ")}` : "";
    const table = quote(this.table);

    if (this.kind === "select") {
      return { text: `select * from ${table}${where}${this.orderBy}${this.limitTo}`, values: this.params };
    }

    if (this.kind === "delete") {
      return { text: `delete from ${table}${where}${this.returning ? " returning *" : ""}`, values: this.params };
    }

    const columns = Object.keys(this.payload ?? {});
    if (this.kind === "insert") {
      return {
        text:
          `insert into ${table} (${columns.map(quote).join(", ")}) ` +
          `values (${columns.map((_, i) => `$${i + 1}`).join(", ")})` +
          (this.returning ? " returning *" : ""),
        values: columns.map((c) => (this.payload as Row)[c]),
      };
    }

    // update: the SET params are bound first, so the filters' placeholders shift.
    const sets = columns.map((c, i) => `${quote(c)} = $${i + 1}`);
    const shifted = this.wheres.map((clause) =>
      clause.replace(/\$(\d+)/g, (_, n) => `$${Number(n) + columns.length}`),
    );
    return {
      text:
        `update ${table} set ${sets.join(", ")}` +
        (shifted.length ? ` where ${shifted.join(" and ")}` : "") +
        (this.returning ? " returning *" : ""),
      values: [...columns.map((c) => (this.payload as Row)[c]), ...this.params],
    };
  }

  async run(): Promise<Result<unknown>> {
    const db = await database();
    const { text, values } = this.sql();
    const actor = currentActor();

    try {
      // The transaction is what makes SET LOCAL bite, and the role is what makes
      // RLS apply at all. Both, every query — see the module docstring.
      await db.exec(
        `begin; set local role ${actor ? "authenticated" : "anon"}; ` +
          `set local request.jwt.claim.sub = ${literal(actor)}; ` +
          `set local request.jwt.claim.role = ${literal(actor ? "authenticated" : "anon")};`,
      );
      const result = await db.query(text, values as never[]);
      await db.exec("commit;");

      const rows = (result.rows ?? []) as Row[];
      if (this.wantsSingle) {
        if (rows.length !== 1) {
          return { data: null, error: { message: `expected one row, got ${rows.length}` } };
        }
        return { data: rows[0], error: null };
      }
      return { data: rows, error: null };
    } catch (error) {
      await db.exec("rollback;").catch(() => undefined);
      return { data: null, error: { message: (error as Error).message } };
    }
  }

  then<A, B>(
    onfulfilled?: ((value: Result<unknown>) => A | PromiseLike<A>) | null,
    onrejected?: ((reason: unknown) => B | PromiseLike<B>) | null,
  ): PromiseLike<A | B> {
    return this.run().then(onfulfilled, onrejected);
  }
}

class Table {
  private name: string;

  constructor(name: string) {
    this.name = name;
  }
  select(columns = "*") {
    return new Query(this.name, "select").select(columns);
  }
  insert(payload: Row) {
    return new Query(this.name, "insert", payload);
  }
  update(payload: Row) {
    return new Query(this.name, "update", payload);
  }
  delete() {
    return new Query(this.name, "delete");
  }
}

/** Who subsequent queries act as. The harness drives this to check isolation. */
export function setVerificationActor(id: string): void {
  (globalThis as Global)[ACTOR_KEY] = id;
}

export function currentActor(): string {
  return (globalThis as Global)[ACTOR_KEY] ?? DEFAULT_ACTOR;
}

export function getSupabaseClient() {
  return {
    from(table: string) {
      return new Table(table);
    },
    // Generated code sometimes reaches for auth. Say what is true rather than
    // pretending: verification has an actor, not a session.
    auth: {
      async getUser() {
        const who = currentActor();
        return who
          ? { data: { user: { id: who } }, error: null }
          : { data: { user: null }, error: null };
      },
    },
    rpc() {
      throw new Error(
        "the verification client does not implement .rpc(). Run the real PostgREST " +
          "against the same database if a generated app needs stored procedures.",
      );
    },
  };
}

/** Read the database directly. For the harness's evidence, never for app code. */
export async function verificationQuery(text: string, values: unknown[] = []) {
  const db = await database();
  return (await db.query(text, values as never[])).rows;
}
