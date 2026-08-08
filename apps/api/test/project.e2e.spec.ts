import { randomUUID } from "node:crypto";
import { UnauthorizedException, ValidationPipe } from "@nestjs/common";
import type { INestApplication } from "@nestjs/common";
import { Test } from "@nestjs/testing";
import request from "supertest";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { AppModule } from "../src/app.module";
import { IDENTITY_VERIFIER } from "../src/auth/identity-verifier";
import { ProvisioningService } from "../src/auth/provisioning.service";
import { WorkspaceScope } from "../src/auth/workspace-scope";

/** Fake identity: token "w1-token" → workspace w1, "w2-token" → w2. */
const fakeVerifier = {
  async verify(token: string) {
    if (token === "w1-token") return { externalId: "c1", email: "one@example.com" };
    if (token === "w2-token") return { externalId: "c2", email: "two@example.com" };
    throw new UnauthorizedException("bad token");
  },
};
const fakeProvisioning = {
  async getOrCreate(identity: { externalId: string }) {
    return identity.externalId === "c1"
      ? { userId: "u1", workspaceId: "w1" }
      : { userId: "u2", workspaceId: "w2" };
  },
};

/** In-memory WorkspaceScope with the same semantics as the Prisma extension. */
class FakeScope {
  rows: any[] = [];
  private seq = 0;

  forWorkspace(workspaceId: string) {
    const store = this;
    return {
      project: {
        async create({ data }: any) {
          const row = {
            id: randomUUID(),
            workspaceId, // stamped by the scope, caller can't override
            name: data.name,
            type: data.type ?? "app",
            status: "draft",
            deletedAt: null,
            createdAt: new Date(2026, 0, 1, 0, 0, store.seq++),
            updatedAt: new Date(),
          };
          store.rows.push(row);
          return row;
        },
        async findMany({ where }: any) {
          return store.rows
            .filter(
              (r) =>
                r.workspaceId === workspaceId &&
                (where?.deletedAt === undefined || r.deletedAt === where.deletedAt),
            )
            .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
        },
        async findFirst({ where }: any) {
          return (
            store.rows.find(
              (r) =>
                r.workspaceId === workspaceId &&
                r.id === where.id &&
                (where?.deletedAt === undefined || r.deletedAt === where.deletedAt),
            ) ?? null
          );
        },
        async update({ where, data }: any) {
          const row = store.rows.find((r) => r.workspaceId === workspaceId && r.id === where.id);
          if (!row) throw new Error("record not found");
          Object.assign(row, data, { updatedAt: new Date() });
          return row;
        },
      },
    };
  }
}

describe("Project CRUD (e2e, workspace-scoped)", () => {
  let app: INestApplication;
  let http: any;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(IDENTITY_VERIFIER)
      .useValue(fakeVerifier)
      .overrideProvider(ProvisioningService)
      .useValue(fakeProvisioning)
      .overrideProvider(WorkspaceScope)
      .useValue(new FakeScope())
      .compile();
    app = moduleRef.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    await app.init();
    http = app.getHttpServer();
  });

  afterAll(async () => {
    await app.close();
  });

  const w1 = { Authorization: "Bearer w1-token" };
  const w2 = { Authorization: "Bearer w2-token" };
  let projectId: string;

  it("rejects unauthenticated requests (401)", async () => {
    await request(http).get("/projects").expect(401);
  });

  it("rejects invalid bodies (400)", async () => {
    await request(http).post("/projects").set(w1).send({}).expect(400);
    await request(http).post("/projects").set(w1).send({ name: "" }).expect(400);
    await request(http).post("/projects").set(w1).send({ name: "x", type: "bogus" }).expect(400);
  });

  it("creates a project (draft, type defaults to app)", async () => {
    const res = await request(http).post("/projects").set(w1).send({ name: "Bistro" }).expect(201);
    expect(res.body.project).toMatchObject({
      name: "Bistro",
      type: "app",
      status: "draft",
      workspaceId: "w1",
    });
    projectId = res.body.project.id;
  });

  it("lists only the caller's workspace, newest first", async () => {
    await request(http).post("/projects").set(w1).send({ name: "Second" }).expect(201);
    const res = await request(http).get("/projects").set(w1).expect(200);
    expect(res.body.projects.map((p: any) => p.name)).toEqual(["Second", "Bistro"]);

    const other = await request(http).get("/projects").set(w2).expect(200);
    expect(other.body.projects).toEqual([]);
  });

  it("gets one project; cross-tenant reads are 404", async () => {
    const res = await request(http).get(`/projects/${projectId}`).set(w1).expect(200);
    expect(res.body.project.id).toBe(projectId);
    await request(http).get(`/projects/${projectId}`).set(w2).expect(404);
  });

  it("updates name and status; cross-tenant updates are 404", async () => {
    const res = await request(http)
      .patch(`/projects/${projectId}`)
      .set(w1)
      .send({ name: "Bistro Nord", status: "ready" })
      .expect(200);
    expect(res.body.project).toMatchObject({ name: "Bistro Nord", status: "ready" });
    await request(http).patch(`/projects/${projectId}`).set(w2).send({ name: "hijack" }).expect(404);
    await request(http)
      .patch(`/projects/${projectId}`)
      .set(w1)
      .send({ status: "not-a-status" })
      .expect(400);
  });

  it("soft-deletes; excluded from list; cross-tenant deletes are 404", async () => {
    await request(http).delete(`/projects/${projectId}`).set(w2).expect(404);
    await request(http).delete(`/projects/${projectId}`).set(w1).expect(204);
    await request(http).get(`/projects/${projectId}`).set(w1).expect(404);
    const res = await request(http).get("/projects").set(w1).expect(200);
    expect(res.body.projects.map((p: any) => p.name)).toEqual(["Second"]);
    // idempotence: deleting again is 404 (already gone from the caller's view)
    await request(http).delete(`/projects/${projectId}`).set(w1).expect(404);
  });
});
