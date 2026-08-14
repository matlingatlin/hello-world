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

/** In-memory scope with the same tenant semantics as the Prisma extension. */
class FakeScope {
  projects: any[] = [];
  messages: any[] = [];
  specVersions: any[] = [];
  private seq = 0;

  private next() {
    return new Date(2026, 0, 1, 0, 0, this.seq++);
  }

  forWorkspace(workspaceId: string) {
    const store = this;
    const ownsProject = (projectId: string) =>
      store.projects.some((p) => p.id === projectId && p.workspaceId === workspaceId);

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
      message: {
        async create({ data }: any) {
          // The scope reaches messages through their project, so a message can
          // never be written into another tenant's conversation.
          if (!ownsProject(data.projectId)) throw new Error("cross-tenant write");
          const row = { id: randomUUID(), ...data, createdAt: store.next() };
          store.messages.push(row);
          return row;
        },
        async findMany({ where }: any) {
          if (!ownsProject(where.projectId)) return [];
          return store.messages
            .filter((m) => m.projectId === where.projectId)
            .sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime());
        },
      },
      specVersion: {
        async create({ data }: any) {
          if (!ownsProject(data.projectId)) throw new Error("cross-tenant write");
          const row = { id: randomUUID(), ...data, createdAt: store.next() };
          store.specVersions.push(row);
          return row;
        },
        async findMany({ where }: any) {
          if (!ownsProject(where.projectId)) return [];
          return store.specVersions
            .filter((s) => s.projectId === where.projectId)
            .sort((a, b) => b.number - a.number);
        },
        async update({ where, data }: any) {
          const row = store.specVersions.find((s) => s.id === where.id);
          if (!row) throw new Error("record not found");
          Object.assign(row, data);
          return row;
        },
      },
    };
  }
}

const QUESTION = {
  field: "users_and_roles",
  text: "Who will be using it?",
  example: "Guests, and staff who see today's list.",
  about: "field" as const,
  written_by: "model" as const,
};

function specWith(fields: Record<string, unknown>) {
  return {
    purpose: { value: "Guests book a table.", source: "stated", confidence: "high", provenance: [] },
    platform: { value: "responsive web app", source: "default", confidence: "medium", provenance: [] },
    look: { value: "Scio default", source: "default", confidence: "medium", provenance: [] },
    ...fields,
  };
}

/** A scriptable engine: each call shifts the next scripted reply. */
class FakeEngine {
  steps: any[] = [];
  // The real shape: Layer B's whole is an object, not a string (verified against
  // the running engine — a string mock here would hide a null on the review screen).
  architectureReply: any = {
    whole: {
      narrative: "You're building a table-booking app.",
      assumptions: ["platform", "look"],
      grounding: {},
      models_used: [],
      generated: false,
    },
    architecture: { nodes: [] },
  };
  planReply: any = { plan: { packages: [{ id: "pkg_foundation" }, { id: "pkg_schema" }] } };
  seen: any[] = [];
  failIntake = false;

  async intakeStep(body: any) {
    this.seen.push(body);
    if (this.failIntake) throw new EngineUnavailableError("/intake/step: connection refused");
    return (
      this.steps.shift() ?? {
        updated_spec: specWith({}),
        buildable: false,
        next_question: QUESTION,
        contradictions: [],
        gate: { buildable: false, missing_core: ["users_and_roles"], unresolved_conditionals: [], contradictions: [] },
        triggered: [],
        extraction: {},
      }
    );
  }
  async architecture() {
    return this.architectureReply;
  }
  async plan() {
    return this.planReply;
  }
}

describe("Gate 1 (e2e): wizard turn + spec freeze", () => {
  let app: INestApplication;
  let http: any;
  let scope: FakeScope;
  let engine: FakeEngine;

  const w1 = { Authorization: "Bearer w1-token" };
  const w2 = { Authorization: "Bearer w2-token" };
  let projectId: string;

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
      { id: "p1", workspaceId: "w1", name: "Bistro", type: "app", status: "draft", draftSpec: null, deletedAt: null },
    ];
    scope.messages = [];
    scope.specVersions = [];
    engine.steps = [];
    engine.seen = [];
    engine.failIntake = false;
    engine.architectureReply = {
      whole: {
        narrative: "You're building a table-booking app.",
        assumptions: ["platform", "look"],
        grounding: {},
        models_used: [],
        generated: false,
      },
      architecture: { nodes: [] },
    };
    projectId = "p1";
  });

  it("rejects unauthenticated turns (401)", async () => {
    await request(http).post(`/projects/${projectId}/intake/message`).send({ text: "hi" }).expect(401);
  });

  it("rejects empty messages (400)", async () => {
    await request(http).post(`/projects/${projectId}/intake/message`).set(w1).send({}).expect(400);
    await request(http).post(`/projects/${projectId}/intake/message`).set(w1).send({ text: "" }).expect(400);
  });

  it("is 404 for another workspace's project", async () => {
    await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w2)
      .send({ text: "hijack" })
      .expect(404);
    expect(scope.messages).toHaveLength(0);
  });

  it("persists the turn and answers with the next question", async () => {
    const res = await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w1)
      .send({ text: "A booking app for my restaurant." })
      .expect(201);

    expect(res.body.next_question.text).toBe(QUESTION.text);
    expect(res.body.next_question.example).toBe(QUESTION.example);
    expect(res.body.buildable).toBe(false);

    // Both turns are stored, in order, and Scio's carries the example.
    expect(scope.messages.map((m) => m.role)).toEqual(["user", "scio"]);
    expect(scope.messages[1].content).toContain("For example:");
    expect(res.body.messages).toHaveLength(2);
    expect(res.body.messages[1].example).toBe(QUESTION.example);

    // The working spec is persisted on the project, not frozen as a version.
    expect(scope.projects[0].draftSpec.purpose.value).toBe("Guests book a table.");
    expect(scope.specVersions).toHaveLength(0);
  });

  it("sends the engine the stored message ids, so provenance survives", async () => {
    await request(http).post(`/projects/${projectId}/intake/message`).set(w1).send({ text: "one" });
    await request(http).post(`/projects/${projectId}/intake/message`).set(w1).send({ text: "two" });

    const second = engine.seen[1];
    expect(second.messages.map((m: any) => m.id)).toEqual(scope.messages.slice(0, 3).map((m) => m.id));
    expect(second.messages.map((m: any) => m.role)).toEqual(["user", "assistant", "user"]);
    expect(second.spec).not.toBeNull(); // the spec from turn one came back in
  });

  it("surfaces a contradiction instead of resolving it", async () => {
    const conflict = {
      fields: ["sign_in", "users_and_roles"],
      description: "You said no sign-in, but also that there are several kinds of user.",
      resolved: false,
    };
    engine.steps = [
      {
        updated_spec: specWith({}),
        buildable: false,
        next_question: { ...QUESTION, about: "contradiction", field: "" },
        contradictions: [conflict],
        gate: { buildable: false, missing_core: [], unresolved_conditionals: [], contradictions: [conflict] },
        triggered: [],
        extraction: {},
      },
    ];

    const res = await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w1)
      .send({ text: "no sign-in, but staff too" })
      .expect(201);

    expect(res.body.contradictions).toHaveLength(1);
    expect(res.body.next_question.about).toBe("contradiction");
    expect(res.body.buildable).toBe(false);
  });

  it("fetches the confirmation and the priced plan once buildable", async () => {
    engine.steps = [buildableStep()];
    engine.planReply = {
      plan: { packages: [{ id: "pkg_foundation" }, { id: "pkg_feature_booking" }] },
      estimate: {
        cost_usd: { low: 0.78, high: 1.87 },
        minutes: { low: 6.1, high: 14.6 },
        composition: { parts_total: 2, assembled: 1, generated: 1 },
        model: "claude-sonnet-5",
        passes: 2,
        basis: "the base build, without changes",
      },
    };

    const res = await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w1)
      .send({ text: "that's everything" })
      .expect(201);

    expect(res.body.buildable).toBe(true);
    expect(res.body.next_question).toBeNull();
    expect(res.body.whole).toContain("table-booking app");
    expect(res.body.estimate.cost_usd).toEqual({ low: 0.78, high: 1.87 });
    expect(res.body.estimate.composition).toEqual({
      parts_total: 2,
      assembled: 1,
      generated: 1,
    });
    expect(res.body.estimate.basis).toBe("the base build, without changes");
    expect(res.body.engine.degraded).toBeUndefined();
  });

  it("falls back to the part count when the engine could not price the plan", async () => {
    // An unpriced plan must not take the review screen down with it: the user
    // can still read their spec and see how many parts it is.
    engine.steps = [buildableStep()];
    engine.planReply = {
      plan: { packages: [{ id: "pkg_foundation" }, { id: "pkg_schema" }] },
    };

    const res = await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w1)
      .send({ text: "that's everything" })
      .expect(201);

    expect(res.body.estimate.parts).toBe(2);
    expect(res.body.estimate.packages).toEqual(["pkg_foundation", "pkg_schema"]);
    expect(res.body.estimate.cost_usd).toBeNull();
    expect(res.body.estimate.minutes).toBeNull();
  });

  it("still returns the spec when Layer B is unavailable", async () => {
    engine.steps = [buildableStep()];
    engine.architectureReply = null; // the engine client degrades to null, never throws

    const res = await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w1)
      .send({ text: "that's everything" })
      .expect(201);

    expect(res.body.buildable).toBe(true);
    expect(res.body.whole).toBeNull();
    expect(res.body.estimate).toBeNull();
    expect(res.body.engine.degraded).toEqual(["architecture"]);
    expect(res.body.updated_spec.purpose.value).toBe("Guests book a table."); // still readable
  });

  it("reports an unreachable engine as 503 rather than a broken turn", async () => {
    engine.failIntake = true;

    const res = await request(http)
      .post(`/projects/${projectId}/intake/message`)
      .set(w1)
      .send({ text: "hello?" })
      .expect(503);

    expect(res.body.message).toContain("engine is not reachable");
  });

  it("returns the conversation so far", async () => {
    await request(http).post(`/projects/${projectId}/intake/message`).set(w1).send({ text: "one" });

    const res = await request(http).get(`/projects/${projectId}/intake`).set(w1).expect(200);
    expect(res.body.messages.map((m: any) => m.text)).toEqual(["one", expect.stringContaining(QUESTION.text)]);
    await request(http).get(`/projects/${projectId}/intake`).set(w2).expect(404);
  });
});

describe("Spec approval (e2e)", () => {
  let app: INestApplication;
  let http: any;
  let scope: FakeScope;

  const w1 = { Authorization: "Bearer w1-token" };
  const w2 = { Authorization: "Bearer w2-token" };

  beforeAll(async () => {
    scope = new FakeScope();
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(IDENTITY_VERIFIER)
      .useValue(fakeVerifier)
      .overrideProvider(ProvisioningService)
      .useValue(fakeProvisioning)
      .overrideProvider(WorkspaceScope)
      .useValue(scope)
      .overrideProvider(EngineClient)
      .useValue(new FakeEngine())
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
        status: "draft",
        draftSpec: specWith({}),
        deletedAt: null,
      },
    ];
    scope.specVersions = [];
    scope.messages = [];
  });

  it("freezes the working spec as version 1 and locks the project", async () => {
    const res = await request(http).post("/projects/p1/spec/approve").set(w1).expect(201);

    expect(res.body.specVersion).toMatchObject({ number: 1, isCurrent: true });
    expect(res.body.projectStatus).toBe("spec_locked");
    expect(scope.projects[0].status).toBe("spec_locked");
    expect(scope.specVersions[0].content.purpose.value).toBe("Guests book a table.");
    // The assumptions are recorded from the spec itself, not taken on trust.
    expect(scope.specVersions[0].assumptions.assumed).toEqual(["look", "platform"]);
  });

  it("a second approval is a new version; only the newest is current", async () => {
    await request(http).post("/projects/p1/spec/approve").set(w1).expect(201);
    const res = await request(http).post("/projects/p1/spec/approve").set(w1).expect(201);

    expect(res.body.specVersion.number).toBe(2);
    expect(scope.specVersions.find((s) => s.number === 1).isCurrent).toBe(false);
    expect(scope.specVersions.find((s) => s.number === 2).isCurrent).toBe(true);
  });

  it("refuses to freeze nothing", async () => {
    scope.projects[0].draftSpec = null;
    await request(http).post("/projects/p1/spec/approve").set(w1).expect(409);
  });

  it("is 404 across tenants, and writes nothing", async () => {
    await request(http).post("/projects/p1/spec/approve").set(w2).expect(404);
    expect(scope.specVersions).toHaveLength(0);
    expect(scope.projects[0].status).toBe("draft");
  });

  it("lists frozen versions newest first", async () => {
    await request(http).post("/projects/p1/spec/approve").set(w1).expect(201);
    await request(http).post("/projects/p1/spec/approve").set(w1).expect(201);

    const res = await request(http).get("/projects/p1/spec/versions").set(w1).expect(200);
    expect(res.body.specVersions.map((s: any) => s.number)).toEqual([2, 1]);
  });
});

function buildableStep() {
  return {
    updated_spec: specWith({
      users_and_roles: { value: ["guests"], source: "stated", confidence: "high", provenance: [] },
    }),
    buildable: true,
    next_question: null,
    contradictions: [],
    gate: { buildable: true, missing_core: [], unresolved_conditionals: [], contradictions: [] },
    triggered: [],
    extraction: {},
  };
}
