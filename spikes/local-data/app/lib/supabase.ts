/**
 * VERIFICATION MODE ONLY — the app's Supabase client, backed by in-process Postgres.
 *
 * This is the whole trick of the spike. The generated app code is UNCHANGED: it
 * still calls `getSupabaseClient().from("bookings").select(...)`. Only this one
 * module is swapped, and it answers the same shape supabase-js answers with —
 * `{ data, error }` — from a real PostgreSQL running as WASM inside the Node
 * process (pglite), with no Docker, no daemon and no external project.
 *
 * What is implemented is exactly the surface the booking blueprint uses, and no
 * more. That is deliberate: the point is to learn whether persistence can be
 * verified in this sandbox, not to reimplement PostgREST. Anything the app calls
 * that is not here throws loudly rather than silently returning nothing — a shim
 * that quietly answers "no rows" would make a broken app look empty.
 */

import { PGlite } from "@electric-sql/pglite";

const DATA_DIR = process.env.SPIKE_PGDATA ?? "./.pgdata";

export const SCHEMA_SQL = `
create table if not exists bookings (
  id uuid primary key default gen_random_uuid(),
  guest_name text not null,
  phone text not null,
  starts_at timestamptz not null,
  party_size integer not null check (party_size between 1 and 20),
  created_at timestamptz not null default now(),
  cancelled_at timestamptz
);

-- The real migration enables row-level security. It is applied here so the SQL
-- is identical, but see FINDINGS.md: pglite runs everything as the superuser,
-- so RLS is NOT enforced. This verifies persistence, not authorization.
alter table bookings enable row level security;

drop policy if exists bookings_read on bookings;
create policy bookings_read on bookings for select using (true);
`;

let instance: Promise<PGlite> | null = null;

/**
 * One database per process, created on first use and kept.
 *
 * A file-backed directory rather than memory, so the data survives a dev-server
 * restart — which is what makes "reload and it is still there" a claim about
 * persistence rather than about one process's heap.
 */
function database(): Promise<PGlite> {
  if (!instance) {
    instance = (async () => {
      const db = new PGlite(DATA_DIR);
      await db.exec(SCHEMA_SQL);
      return db;
    })();
  }
  return instance;
}

type Row = Record<string, unknown>;
type Result<T> = { data: T; error: { message: string } | null };

function quote(identifier: string): string {
  if (!/^[a-z_][a-z0-9_]*$/i.test(identifier)) {
    throw new Error(`unsafe identifier: ${identifier}`);
  }
  return `"${identifier}"`;
}

/**
 * A thenable query builder: the app chains filters and then awaits, exactly as
 * with supabase-js. Building the SQL only when awaited is what lets `.select()`,
 * `.is()`, `.order()` and `.single()` arrive in any order.
 */
class Query implements PromiseLike<Result<unknown>> {
  private wheres: string[] = [];
  private params: unknown[] = [];
  private orderBy = "";
  private wantsSingle = false;
  private returning = false;

  constructor(
    private table: string,
    private kind: "select" | "insert" | "update",
    private payload?: Row,
  ) {}

  select(_columns = "*") {
    this.returning = true;
    return this;
  }

  is(column: string, value: null) {
    if (value !== null) throw new Error("the shim only implements .is(col, null)");
    this.wheres.push(`${quote(column)} is null`);
    return this;
  }

  eq(column: string, value: unknown) {
    this.params.push(value);
    this.wheres.push(`${quote(column)} = $${this.params.length}`);
    return this;
  }

  order(column: string, options?: { ascending?: boolean }) {
    this.orderBy = ` order by ${quote(column)} ${options?.ascending === false ? "desc" : "asc"}`;
    return this;
  }

  single() {
    this.wantsSingle = true;
    return this;
  }

  private sql(): { text: string; values: unknown[] } {
    const where = this.wheres.length ? ` where ${this.wheres.join(" and ")}` : "";

    if (this.kind === "select") {
      return { text: `select * from ${quote(this.table)}${where}${this.orderBy}`, values: this.params };
    }

    if (this.kind === "insert") {
      const columns = Object.keys(this.payload ?? {});
      const values = columns.map((_, i) => `$${i + 1}`);
      return {
        text:
          `insert into ${quote(this.table)} (${columns.map(quote).join(", ")}) ` +
          `values (${values.join(", ")})${this.returning ? " returning *" : ""}`,
        values: columns.map((c) => (this.payload as Row)[c]),
      };
    }

    const columns = Object.keys(this.payload ?? {});
    // Update parameters come first, then whatever the filters already bound.
    const sets = columns.map((c, i) => `${quote(c)} = $${i + 1}`);
    const shifted = this.wheres.map((clause) =>
      clause.replace(/\$(\d+)/g, (_, n) => `$${Number(n) + columns.length}`),
    );
    const updateWhere = shifted.length ? ` where ${shifted.join(" and ")}` : "";
    return {
      text: `update ${quote(this.table)} set ${sets.join(", ")}${updateWhere}${this.returning ? " returning *" : ""}`,
      values: [...columns.map((c) => (this.payload as Row)[c]), ...this.params],
    };
  }

  async run(): Promise<Result<unknown>> {
    try {
      const db = await database();
      const { text, values } = this.sql();
      const result = await db.query(text, values as never[]);
      const rows = (result.rows ?? []) as Row[];

      if (this.wantsSingle) {
        if (rows.length !== 1) {
          return { data: null, error: { message: `expected exactly one row, got ${rows.length}` } };
        }
        return { data: rows[0], error: null };
      }
      return { data: rows, error: null };
    } catch (error) {
      // Same shape supabase-js uses: the app's own error handling is exercised.
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
  constructor(private name: string) {}

  select(columns = "*") {
    return new Query(this.name, "select").select(columns);
  }

  insert(payload: Row) {
    return new Query(this.name, "insert", payload);
  }

  update(payload: Row) {
    return new Query(this.name, "update", payload);
  }
}

export function getSupabaseClient() {
  return {
    from(table: string) {
      return new Table(table);
    },
  };
}

/** Exported for the harness: prove a row is in the DATABASE, not just on screen. */
export async function rawQuery(text: string, values: unknown[] = []) {
  const db = await database();
  return (await db.query(text, values as never[])).rows;
}
