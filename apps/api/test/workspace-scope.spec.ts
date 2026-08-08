import { describe, expect, it } from "vitest";
import { applyWorkspaceScope } from "../src/auth/workspace-scope";

describe("applyWorkspaceScope", () => {
  it("merges workspaceId into where on reads of scoped models", () => {
    const args = applyWorkspaceScope("Project", "findMany", { where: { deletedAt: null } }, "w1");
    expect(args.where).toEqual({ deletedAt: null, workspaceId: "w1" });
  });

  it("adds a where clause when none exists", () => {
    const args = applyWorkspaceScope("Project", "findMany", {}, "w1");
    expect(args.where).toEqual({ workspaceId: "w1" });
  });

  it("overrides a caller-supplied foreign workspaceId (no cross-tenant reads)", () => {
    const args = applyWorkspaceScope(
      "Project",
      "findMany",
      { where: { workspaceId: "other-tenant" } },
      "w1",
    );
    expect(args.where.workspaceId).toBe("w1");
  });

  it("stamps workspaceId into data on create", () => {
    const args = applyWorkspaceScope("Project", "create", { data: { name: "x" } }, "w1");
    expect(args.data).toEqual({ name: "x", workspaceId: "w1" });
  });

  it("scopes updates and deletes too", () => {
    const upd = applyWorkspaceScope("Project", "updateMany", { where: { id: "p1" } }, "w1");
    expect(upd.where).toEqual({ id: "p1", workspaceId: "w1" });
    const del = applyWorkspaceScope("Notification", "deleteMany", {}, "w1");
    expect(del.where).toEqual({ workspaceId: "w1" });
  });

  it("leaves non-scoped models untouched (scoped via project instead)", () => {
    const args = applyWorkspaceScope("SpecVersion", "findMany", { where: { projectId: "p1" } }, "w1");
    expect(args.where).toEqual({ projectId: "p1" });
  });
});
