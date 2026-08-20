import { execFileSync } from "node:child_process";
import { readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Every source file must be committed — checked against git, not the disk.
 *
 * A .gitignore pattern is matched at every level unless it is anchored, so a
 * bare `build/` or `workspace/` meant for scratch directories also matches a
 * source directory with that name. It has happened twice: `build/` silently
 * excluded `src/modules/build`, and `workspace/` excluded `src/modules/workspace`
 * — three files that existed on the machine they were written on and nowhere
 * else. Nothing noticed, because every test and every dev run reads the working
 * tree, where the files are right there. The first machine to start from a clean
 * clone could not compile the api.
 *
 * This test is the one that reads what a clone would get.
 */
const ROOT = resolve(__dirname, "../../..");
const WATCHED = ["apps/api/src", "apps/app/src", "packages/shared/src"];

function sourcesOnDisk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(join(ROOT, dir))) {
    const rel = `${dir}/${entry}`;
    if (statSync(join(ROOT, rel)).isDirectory()) out.push(...sourcesOnDisk(rel));
    else if (/\.(ts|tsx)$/.test(entry)) out.push(rel);
  }
  return out;
}

describe("every source file a fresh clone needs", () => {
  it.each(WATCHED)("is committed under %s", (dir) => {
    const tracked = new Set(
      execFileSync("git", ["ls-files", dir], { cwd: ROOT, encoding: "utf8" })
        .split("\n")
        .filter(Boolean),
    );
    const untracked = sourcesOnDisk(dir).filter((file) => !tracked.has(file));
    expect(
      untracked,
      `these exist here but not in the repo — check .gitignore for an unanchored rule:\n  ${untracked.join("\n  ")}`,
    ).toEqual([]);
  });
});
