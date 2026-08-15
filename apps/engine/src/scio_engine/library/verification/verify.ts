/**
 * VERIFICATION ONLY — what the harness may ask the app about its own database.
 *
 * Framework-free on purpose. The Next route is a four-line wrapper around this
 * file, so the thing the tests drive is the thing the build runs; a route that
 * could only be exercised inside Next would be the one piece of the evidence
 * chain nothing ever checked.
 *
 * ?table=booking&match={"guest_name":"Ada"}  -> { count }
 * ?actor=<uuid>                             -> { actor }
 */
import { setVerificationActor, verificationQuery } from "./client.ts";

function identifier(name: string): string {
  if (!/^[a-z_][a-z0-9_]*$/i.test(name)) throw new Error(`unsafe identifier: ${name}`);
  return `"${name}"`;
}

/**
 * The harness asks about an ENTITY ("booking"); the migration named a RELATION,
 * and whether that is `booking` or `bookings` is the builder's choice — the
 * architecture is singular, the seed catalog's data layer is plural. Resolving
 * it here keeps that one ambiguity in one place instead of making every derived
 * script guess, and an unresolvable name comes back as a named error rather
 * than as a count of zero that would read as "it was not saved".
 */
export async function resolveTable(name: string): Promise<string> {
  const singular = name.replace(/s$/, "");
  const candidates = [...new Set([name, `${name}s`, singular, `${singular}s`, `${singular}es`])];
  const rows = (await verificationQuery(
    `select table_name from information_schema.tables
      where table_schema = 'public'
        and table_name in (${candidates.map((_, i) => `$${i + 1}`).join(", ")})`,
    candidates,
  )) as { table_name: string }[];

  if (rows.length === 1) return rows[0].table_name;
  if (rows.length === 0) throw new Error(`no table for '${name}' (tried ${candidates.join(", ")})`);
  // Both `booking` and `bookings` exist: say so rather than picking one.
  throw new Error(`'${name}' is ambiguous: ${rows.map((r) => r.table_name).join(", ")} both exist`);
}

/**
 * Counts rows WITHOUT row-level security — deliberately.
 *
 * This answers "did it really reach Postgres", which is a different question
 * from "may this user see it". Isolation is checked through the app's own
 * pages, where the policies actually apply; asking this endpoint would only
 * tell us whether our own shim filters, which proves nothing about the build.
 */
export async function answer(params: URLSearchParams): Promise<Record<string, unknown>> {
  const actor = params.get("actor");
  if (actor !== null) {
    setVerificationActor(actor);
    return { actor };
  }

  const table = params.get("table") ?? "";
  const match = JSON.parse(params.get("match") ?? "{}") as Record<string, string>;
  try {
    const relation = await resolveTable(table);
    const columns = Object.keys(match);
    const where = columns.length
      ? " where " + columns.map((c, i) => `${identifier(c)}::text = $${i + 1}`).join(" and ")
      : "";
    const rows = (await verificationQuery(
      `select count(*)::int as n from ${identifier(relation)}${where}`,
      columns.map((c) => match[c]),
    )) as { n: number }[];
    return { count: rows[0]?.n ?? 0 };
  } catch (error) {
    return { error: (error as Error).message };
  }
}
