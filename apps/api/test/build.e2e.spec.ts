import { randomUUID } from "node:crypto";
import { UnauthorizedException, ValidationPipe } from "@nestjs/common";
import type { INestApplication } from "@nestjs/common";
import { Test } from "@nestjs/testing";
import request from "supertest";
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { AppModule } from "../src/app.module";
import { IDENTITY_VERIFIER } from "../src/auth/identity-verifier";
import { ProvisioningService } from "../src/auth/provisioning.service";
import { WorkspaceScope } from "../src/auth/workspace-scope";
import { EngineClient, EngineUnavailableError } from "../src/engine/engine.client";

/**
 * The build path: a frozen spec in, progress relayed out, a version persisted.
 * The engine is faked, but the *stream* is real — the events are delivered one
 * at a time, in order, exactly as the engine emits them.
 */

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

class FakeScope {
  projects: any[] = [];
  specVersions: any[] = [];
  buildVersions: any[] = [];
  usageEvents: any[] = [];
  messages: any[] = [];
  private seq = 0;

  forWorkspace(workspaceId: string) {
    const store = this;
    const owns = (projectId: string) =>
      store.projects.some((p) => p.id === projectId && p.workspaceId === workspaceId);

    const collection = (rows: any[], sort: (a: any, b: any) => number) => ({
      async create({ data }: any) {
        if (!owns(data.projectId)) throw new Error("cross-tenant write");
        const row = { id: randomUUID(), ...data, createdAt: new Date(2026, 0, 1, 0, 0, store.seq++) };
        rows.push(row);
        return row;
      },
      async findMany({ where }: any) {
        if (!owns(where.projectId)) return [];
        return rows.filter((r) => r.projectId === where.projectId).sort(sort);
      },
      async update({ where, data }: any) {
        const row = rows.find((r) => r.id === where.id);
        if (!row) throw new Error("record not found");
        Object.assign(row, data);
        return row;
      },
    });

    return {
      project: {
        async findFirst({ where }: any) {
          return (
            store.projects.find(
              (p) =>
                p.workspaceId === workspaceId &&
                p.id === where.id &&
                (where.deletedAt === undefined || p.deletedAt === where.deletedAt),
            ) ?? null
          );
        },
        async update({ where, data }: any) {
          const row = store.projects.find((p) => p.workspaceId === workspaceId && p.id === where.id);
          if (!row) throw new Error("record not found");
          Object.assign(row, data);
          return row;
        },
      },
      message: collection(store.messages, (a, b) => a.createdAt - b.createdAt),
      specVersion: collection(store.specVersions, (a, b) => b.number - a.number),
      buildVersion: collection(store.buildVersions, (a, b) => b.number - a.number),
      // Metering. Scoped by workspace in the real client (auth/workspace-scope),
      // so it is here too: a build's cost must not be readable across tenants.
      usageEvent: {
        async create({ data }: any) {
          const row = { id: randomUUID(), ...data, createdAt: new Date(2026, 0, 1, 0, 0, store.seq++) };
          store.usageEvents.push(row);
          return row;
        },
        async findMany({ where }: any) {
          return store.usageEvents
            .filter(
              (u) =>
                u.workspaceId === workspaceId &&
                (where?.projectId === undefined || u.projectId === where.projectId) &&
                (where?.kind === undefined || u.kind === where.kind),
            )
            .sort((a, b) => b.createdAt - a.createdAt);
        },
      },
    };
  }
}

const FINISHED = {
  project_id: "p1",
  app_url: "http://127.0.0.1:41234",
  build_version: 1,
  git_sha: "3a28a30d9de2aaaa",
  whole: "You're building a table-booking app.",
  summary: "4 of 5 parts work. 1 need a look.\npkg_feature_menu: needs a look — no date field",
  works: false,
  parts_working: ["pkg_foundation", "pkg_schema", "pkg_design_tokens", "pkg_auth"],
  parts_needing_a_look: ["pkg_feature_menu"],
  parts_blocked: [],
  parts_failed: [],
  remainders: ["pkg_feature_menu: needs a look — no date field"],
  element_count: 13,
  files: ["app/page.tsx"],
  total_cost_usd: 0.83,
  total_tokens: 41234,
  model: "claude-sonnet-5",
  standin: true,
};

class FakeEngine {
  events: Array<[string, Record<string, unknown>]> = [];
  failWith: Error | null = null;
  seen: any[] = [];

  async streamBuild(body: any, onEvent: (e: string, d: Record<string, unknown>) => Promise<void>) {
    this.seen.push(body);
    if (this.failWith) throw this.failWith;
    for (const [event, data] of this.events) await onEvent(event, data);
  }
  async intakeStep() {
    return {} as never;
  }
  async architecture() {
    return null;
  }
  async plan() {
    return null;
  }
}

function frames(body: string) {
  return body
    .split("\n\n")
    .filter(Boolean)
    .map((frame) => {
      const event = /event: (.*)/.exec(frame)?.[1] ?? "";
      const data = /data: (.*)/.exec(frame)?.[1] ?? "{}";
      return { event, data: JSON.parse(data) };
    });
}

describe("Build (e2e): stream + persistence", () => {
  let app: INestApplication;
  let http: any;
  let scope: FakeScope;
  let engine: FakeEngine;

  const w1 = { Authorization: "Bearer w1-token" };
  const w2 = { Authorization: "Bearer w2-token" };

  beforeAll(async () => {
    scope = new FakeScope();
    engine = new FakeEngine();
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(IDENTITY_VERIFIER)
      .useValue(fakeVerifier)
      .overrideProvider(ProvisioningService)
      .useValue(fakeProvisioning)
      .overrideProvider(WorkspaceScope)
      .useValue(scope)
      .overrideProvider(EngineClient)
      .useValue(engine)
      .compile();
    app = moduleRef.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
    await app.init();
    http = app.getHttpServer();
  });

  afterAll(async () => {
    await app.close();
  });

  beforeEach(() => {
    scope.projects = [
      {
        id: "p1",
        workspaceId: "w1",
        name: "Bistro",
        type: "app",
        status: "spec_locked",
        draftSpec: {},
        previewUrl: null,
        deletedAt: null,
      },
    ];
    scope.specVersions = [
      {
        id: "s1",
        projectId: "p1",
        number: 1,
        content: { purpose: { value: "Guests book a table.", source: "stated" } },
        assumptions: { assumed: ["look"], whole: "You're building a table-booking app." },
        isCurrent: true,
        createdAt: new Date(2026, 0, 1),
      },
    ];
    scope.buildVersions = [];
    scope.usageEvents = [];
    engine.events = [
      ["started", { project_id: "p1", whole: "…", packages: ["pkg_foundation"], total: 1, workspace: "/tmp/p1" }],
      ["progress", { package_id: "pkg_foundation", index: 1, total: 1, done: 1, status: "passed", message: "works" }],
      ["finished", FINISHED],
    ];
    engine.failWith = null;
    engine.seen = [];
  });

  it("rejects unauthenticated builds (401)", async () => {
    await request(http).post("/projects/p1/build").expect(401);
  });

  it("is 404 for another workspace's project, and builds nothing", async () => {
    const res = await request(http).post("/projects/p1/build").set(w2).expect(200);
    // The stream is already open, so the refusal arrives as an event in it.
    expect(frames(res.text)[0].event).toBe("error");
    expect(frames(res.text)[0].data.type).toBe("not_found");
    expect(engine.seen).toHaveLength(0);
    expect(scope.buildVersions).toHaveLength(0);
  });

  it("relays every engine event, in order", async () => {
    const res = await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(frames(res.text).map((f) => f.event)).toEqual(["started", "progress", "finished"]);
    expect(frames(res.text)[1].data.done).toBe(1);
  });

  it("builds the frozen spec, not the working draft", async () => {
    scope.projects[0].draftSpec = { purpose: { value: "something else", source: "stated" } };

    await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(engine.seen[0].spec.purpose.value).toBe("Guests book a table.");
    expect(engine.seen[0].build_version).toBe(1);
  });

  it("persists a build version with the honest status and the preview URL", async () => {
    await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(scope.buildVersions).toHaveLength(1);
    const version = scope.buildVersions[0];
    expect(version).toMatchObject({ number: 1, gitSha: "3a28a30d9de2aaaa", isCurrent: true, specVersionId: "s1" });
    // Not just the good news: what needs a look is part of the record.
    expect(version.honestStatus.works).toBe(false);
    expect(version.honestStatus.needs_look).toEqual(["pkg_feature_menu"]);
    expect(version.honestStatus.standin).toBe(true);
    expect(scope.projects[0].status).toBe("ready");
    expect(scope.projects[0].previewUrl).toBe("http://127.0.0.1:41234");
  });

  it("a second build is version 2, and only the newest is current", async () => {
    await request(http).post("/projects/p1/build").set(w1).expect(200);
    engine.events = [...engine.events];
    await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(scope.buildVersions.map((b) => b.number).sort()).toEqual([1, 2]);
    expect(scope.buildVersions.find((b) => b.number === 1).isCurrent).toBe(false);
    expect(scope.buildVersions.find((b) => b.number === 2).isCurrent).toBe(true);
    expect(engine.seen[1].build_version).toBe(2);
  });

  it("refuses to build without a frozen spec", async () => {
    scope.specVersions = [];
    const res = await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(frames(res.text)[0].event).toBe("error");
    expect(String(frames(res.text)[0].data.message)).toContain("Approve a spec first");
    expect(scope.buildVersions).toHaveLength(0);
  });

  it("marks the project as errored when the engine never finishes", async () => {
    engine.failWith = new EngineUnavailableError("/build: connection refused");

    const res = await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(frames(res.text).some((f) => f.event === "error")).toBe(true);
    expect(scope.projects[0].status).toBe("error"); // never left "building"
    expect(scope.buildVersions).toHaveLength(0);
  });

  it("does not persist a version when the engine reports a build error", async () => {
    engine.events = [
      ["started", { project_id: "p1", whole: "", packages: [], total: 0, workspace: "" }],
      ["error", { type: "workspace_unavailable", message: "No app scaffold available." }],
    ];

    await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(scope.buildVersions).toHaveLength(0);
    expect(scope.projects[0].status).toBe("error");
  });

  it("the build's own record carries what it cost", async () => {
    // usage_event is the per-workspace metering ledger; a build_version is the
    // record of ONE build and should be readable on its own without a join.
    await request(http).post("/projects/p1/build").set(w1).expect(200);

    const version = scope.buildVersions[0];
    expect(Number(version.costUsd)).toBe(0.83);
    expect(version.tokens).toBe(41234);

    const res = await request(http).get("/projects/p1/build/latest").set(w1).expect(200);
    expect(res.body.buildVersion.costUsd).toBe(0.83);
    expect(res.body.buildVersion.tokens).toBe(41234);
  });

  it("the reveal can compare spend against the estimate that was approved", async () => {
    // Against the estimate the user approved AGAINST — frozen with the spec —
    // not whatever the draft says by the time the build finishes.
    scope.specVersions[0].assumptions = {
      assumed: [],
      whole: "You're building a table-booking app.",
      estimate: { parts: 5, cost_usd: { low: 0.4, high: 1.1 }, minutes: { low: 8, high: 20 } },
    };
    await request(http).post("/projects/p1/build").set(w1).expect(200);

    const res = await request(http).get("/projects/p1/build/latest").set(w1).expect(200);

    expect(res.body.estimate.cost_usd).toEqual({ low: 0.4, high: 1.1 });
    expect(res.body.spend.costUsd).toBe(0.83);
  });

  it("records what the build actually cost", async () => {
    // Until this existed the engine computed a cost, the api passed it to the
    // browser, and it was dropped there — so the product could predict a cost
    // and never say what it spent. usage_event has existed since ADR-0009 and
    // nothing had ever written to it.
    await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(scope.usageEvents).toHaveLength(1);
    const metered = scope.usageEvents[0];
    expect(metered.kind).toBe("generation");
    expect(Number(metered.cost)).toBe(0.83);
    // Tokens, not "one build": a cost with no quantity cannot be re-priced.
    expect(Number(metered.amount)).toBe(41234);
    expect(metered.model).toBe("claude-sonnet-5");
    expect(metered.workspaceId).toBe("w1");

    const res = await request(http).get("/projects/p1/build/latest").set(w1).expect(200);
    expect(res.body.spend).toMatchObject({ costUsd: 0.83, tokens: 41234, model: "claude-sonnet-5" });
  });

  it("a build that spent nothing writes no metering row", async () => {
    // Assembling every part from the library is free. A $0.00 row would read as
    // a measurement; no row is the honest answer.
    engine.events = engine.events.map(([name, data]) =>
      name === "finished" ? [name, { ...data, total_cost_usd: 0, total_tokens: 0 }] : [name, data],
    );

    await request(http).post("/projects/p1/build").set(w1).expect(200);

    expect(scope.usageEvents).toHaveLength(0);
    const res = await request(http).get("/projects/p1/build/latest").set(w1).expect(200);
    expect(res.body.spend).toBeNull();
  });

  it("reads the build back for the reveal", async () => {
    await request(http).post("/projects/p1/build").set(w1).expect(200);

    const res = await request(http).get("/projects/p1/build/latest").set(w1).expect(200);
    expect(res.body.previewUrl).toBe("http://127.0.0.1:41234");
    expect(res.body.buildVersion.number).toBe(1);
    expect(res.body.honestStatus.needs_look).toEqual(["pkg_feature_menu"]);
    expect(res.body.whole).toBe("You're building a table-booking app."); // from the approved spec
    expect(res.body.projectStatus).toBe("ready");

    await request(http).get("/projects/p1/build/latest").set(w2).expect(404);
  });

  it("reports no build yet rather than failing", async () => {
    const res = await request(http).get("/projects/p1/build/latest").set(w1).expect(200);
    expect(res.body.buildVersion).toBeNull();
    expect(res.body.honestStatus).toBeNull();
  });
});
