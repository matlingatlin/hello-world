import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The fence under the discipline.
 *
 * Tenant isolation here is application-layer: a Prisma `$extends` client stamps
 * and filters `workspace_id` on the scoped models. Child rows — spec, design and
 * build versions, messages, build jobs — are NOT scoped at the data layer. They
 * are safe because every service resolves the project through the scoped client
 * first, which throws for somebody else's project, and only then touches child
 * rows by `projectId`.
 *
 * That is a habit, not a wall. One future `buildVersion.findMany({ where: {
 * projectId } })` on the raw client reads across tenants with nothing to stop
 * it — an external reviewer named exactly this. Postgres RLS is the backstop we
 * do not have yet; until we do, this test is the fence: a service that reaches
 * for the raw client fails the suite and has to say why.
 */

const SRC = join(__dirname, "..", "src");

/** Where using the raw client is correct, and why. */
const ALLOWED = new Map<string, string>([
  [
    join("auth", "provisioning.service.ts"),
    "runs BEFORE any workspace context exists — it is what creates one",
  ],
  [
    join("auth", "workspace-scope.ts"),
    "is the scoping client itself",
  ],
  [
    join("prisma", "prisma.service.ts"),
    "is the client",
  ],
]);

// Not allow-listed and not an offender: health/health.controller.ts asks the
// database whether it is there with `$queryRaw`, which reads nobody's rows and
// which the pattern below already excludes.

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return sources(path);
    return path.endsWith(".ts") ? [path] : [];
  });
}

describe("tenant discipline", () => {
  it("no service reads rows through the unscoped Prisma client", () => {
    const offenders = sources(SRC)
      .filter((path) => {
        const relative = path.slice(SRC.length + 1);
        if (ALLOWED.has(relative)) return false;
        const body = readFileSync(path, "utf8");
        // `this.prisma.<model>.<operation>` — the shape that skips scoping.
        // `$transaction`/`$extends` on the raw client are not row reads.
        return /this\.prisma\.(?!\$)[a-zA-Z]+\s*\.\s*[a-zA-Z]/.test(body);
      })
      .map((path) => path.slice(SRC.length + 1));

    expect(
      offenders,
      "these read rows without workspace scoping — use scope.forWorkspace(workspaceId), " +
        "or add the file to ALLOWED with the reason it is safe",
    ).toEqual([]);
  });

  it("the allow-list names files that exist", () => {
    // An allow-list that has drifted is a hole with a comment over it.
    const present = new Set(sources(SRC).map((path) => path.slice(SRC.length + 1)));
    for (const file of ALLOWED.keys()) {
      expect(present.has(file), `${file} is allow-listed and not there`).toBe(true);
    }
  });
});
