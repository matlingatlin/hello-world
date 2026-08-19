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
import { EngineClient } from "../src/engine/engine.client";

/**
 * Level 2: generate a preview, mark things in it, apply a batch.
 *
 * The engine is faked; what is under test is the api's half — that a preview
 * build is asked for as a PREVIEW (so it carries the marking bridge), that the
 * batch reaches the engine in the shape the bridge produces, that a conflict is
 * relayed rather than smoothed over, and that a design version is written for
 * every change that actually changed something.
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
  designVersions: any[] = [];
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
      async findFirst({ where }: any) {
        if (!owns(where.projectId)) return null;
        return rows.find((r) => r.id === where.id && r.projectId === where.projectId) ?? null;
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
      specVersion: collection(store.specVersions, (a, b) => b.number - a.number),
      designVersion: collection(store.designVersions, (a, b) => b.number - a.number),
    };
  }
}

const MANIFEST = {
  version: 1,
  elements: {
    "booking-form-submit": {
      package: "pkg_feature_booking",
      file: "components/booking-form.tsx",
      line: 7,
    },
  },
  packages: { pkg_feature_booking: ["components/booking-form.tsx"] },
};

const PREVIEW_FINISHED = {
  project_id: "p1",
  app_url: "http://127.0.0.1:41234",
  build_version: 1,
  git_sha: "3a28a30d9de2",
  whole: "You're building a table-booking app.",
  summary: "5 of 5 parts work.",
  works: true,
  parts_working: ["pkg_foundation", "pkg_feature_booking"],
  parts_needing_a_look: [],
  parts_blocked: [],
  parts_failed: [],
  remainders: [],
  element_count: 13,
  files: ["components/booking-form.tsx"],
  total_cost_usd: 0,
  standin: true,
  workspace: "/tmp/scio/p1",
  preview: true,
  manifest: MANIFEST,
  package_files: { pkg_feature_booking: ["components/booking-form.tsx"] },
};

const APPLIED = {
  applied: true,
  conflicts: [],
  packages: [
    {
      package: "pkg_feature_booking",
      edited_files: ["components/booking-form.tsx"],
      unchanged_files: 6,
      isolated: true,
      accepted: true,
      rejection: "",
    },
  ],
  unaddressable: [],
  manifest: MANIFEST,
  total_cost_usd: 0.02,
  description: "booking-form-submit: say Reserve",
};

const CONFLICTED = {
  applied: false,
  conflicts: [
    {
      kind: "non_goal",
      scio_id: "booking-form-submit",
      note: "add payments here",
      spec_says: "no payments for now",
      question: "This asks to add something you deliberately left out: “no payments for now”. Do you want it after all?",
    },
  ],
  packages: [],
  unaddressable: [],
  manifest: null,
  total_cost_usd: 0,
  description: "booking-form-submit: add payments here",
};

const RESTORED = {
  restored: true,
  git_sha: "aaaaaaaaaaaa",
  head: "cccccccccccc",
  manifest: MANIFEST,
  error: "",
};

class FakeEngine {
  events: Array<[string, Record<string, unknown>]> = [];
  changeReply: any = APPLIED;
  restoreReply: any = RESTORED;
  seen: any[] = [];
  changes: any[] = [];
  restores: any[] = [];

  async streamBuild(body: any, onEvent: (e: string, d: Record<string, unknown>) => Promise<void>) {
    this.seen.push(body);
    for (const [event, data] of this.events) await onEvent(event, data);
  }
  async designChange(body: any) {
    this.changes.push(body);
    return this.changeReply;
  }
  async designRestore(body: any) {
    this.restores.push(body);
    return this.restoreReply;
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
  async validate() {
    return null;
  }
}

describe("Design window (e2e): preview + directed change", () => {
  let app: INestApplication;
  let http: any;
  let scope: FakeScope;
  let engine: FakeEngine;

  const w1 = { Authorization: "Bearer w1-token" };
  const w2 = { Authorization: "Bearer w2-token" };

  beforeAll(async () => {
    // The design window's origin. Without it a preview would be built with no
    // bridge, so the service refuses rather than producing a dead window.
    process.env.APP_ORIGIN = "http://127.0.0.1:5173";
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
      { id: "p1", workspaceId: "w1", name: "Bistro", type: "app", status: "draft", deletedAt: null },
    ];
    scope.specVersions = [
      { id: "s1", projectId: "p1", number: 1, content: { purpose: {} }, isCurrent: true },
    ];
    scope.designVersions = [];
    engine.events = [["finished", PREVIEW_FINISHED]];
    engine.changeReply = APPLIED;
    engine.restoreReply = RESTORED;
    engine.seen = [];
    engine.changes = [];
    engine.restores = [];
  });

  const generate = () => request(http).post("/projects/p1/design/preview").set(w1);
  const change = (body: unknown) =>
    request(http).post("/projects/p1/design/change").set(w1).send(body);

  // ------------------------------------------------------------------
  // The preview
  // ------------------------------------------------------------------

  it("asks the engine for a PREVIEW build, not a delivery build", async () => {
    await generate().expect(201);

    // shell_origin is the whole difference: with it the app carries the marking
    // bridge; without it, no bridge is built at all.
    expect(engine.seen[0].shell_origin).toBeTruthy();
    expect(engine.seen[0].spec).toEqual({ purpose: {} });
  });

  it("records the preview as a design version, with what the window needs", async () => {
    await generate().expect(201);

    expect(scope.designVersions).toHaveLength(1);
    const ref = JSON.parse(scope.designVersions[0].ref);
    expect(ref.previewUrl).toBe("http://127.0.0.1:41234");
    expect(ref.workspace).toBe("/tmp/scio/p1");
    // The manifest travels with the version: markings resolve against it, and a
    // manifest re-derived later could have drifted from the code.
    expect(ref.manifest).toEqual(MANIFEST);
  });

  it("serves the current preview to a window that just opened", async () => {
    await generate().expect(201);

    const res = await request(http).get("/projects/p1/design").set(w1).expect(200);

    expect(res.body.previewUrl).toBe("http://127.0.0.1:41234");
    expect(res.body.manifest.elements["booking-form-submit"].package).toBe("pkg_feature_booking");
    expect(res.body.designVersion.number).toBe(1);
  });

  it("refuses to design against a spec nobody approved", async () => {
    scope.specVersions = [];

    // The stream opens (headers are already out), and nothing is built.
    await generate();
    expect(engine.seen).toHaveLength(0);
  });

  it("refuses to build a preview with no origin for the bridge to talk to", async () => {
    // Otherwise the window embeds an app that cannot report a single click, and
    // nothing anywhere says why.
    const origin = process.env.APP_ORIGIN;
    delete process.env.APP_ORIGIN;
    try {
      await generate();
      expect(engine.seen).toHaveLength(0);
    } finally {
      process.env.APP_ORIGIN = origin;
    }
  });

  // ------------------------------------------------------------------
  // The change
  // ------------------------------------------------------------------

  it("sends the batch in the shape the in-preview bridge produces", async () => {
    await generate().expect(201);

    await change({
      markings: [
        {
          scioId: "booking-form-submit",
          scioPackage: "pkg_feature_booking",
          tag: "button",
          ancestorId: "booking-form",
          note: "say Reserve our table",
        },
      ],
      prompt: "warmer wording",
    }).expect(201);

    const sent = engine.changes[0];
    expect(sent.app_dir).toBe("/tmp/scio/p1");
    expect(sent.batch.prompt).toBe("warmer wording");
    expect(sent.batch.markings[0]).toMatchObject({
      scio_id: "booking-form-submit",
      scio_package: "pkg_feature_booking",
      // The ancestor travels so a refusal can name it — never as a fallback target.
      ancestor_id: "booking-form",
      note: "say Reserve our table",
    });
  });

  it("returns the isolation proof for an applied change", async () => {
    await generate().expect(201);

    const res = await change({ markings: [{ scioId: "booking-form-submit", note: "say Reserve" }] })
      .expect(201);

    expect(res.body.applied).toBe(true);
    expect(res.body.packages[0]).toMatchObject({
      package: "pkg_feature_booking",
      unchangedFiles: 6,
      isolated: true,
    });
    expect(res.body.previewUrl).toBe("http://127.0.0.1:41234");
  });

  it("an applied change is a new design version", async () => {
    await generate().expect(201);

    const res = await change({ markings: [{ scioId: "booking-form-submit", note: "say Reserve" }] })
      .expect(201);

    expect(scope.designVersions).toHaveLength(2);
    expect(res.body.designVersion.number).toBe(2);
    const newest = scope.designVersions.find((d) => d.number === 2);
    expect(JSON.parse(newest.ref).change).toContain("say Reserve");
    // Exactly one current, so "the preview you are looking at" is never ambiguous.
    expect(scope.designVersions.filter((d) => d.isCurrent)).toHaveLength(1);
  });

  it("a conflict is relayed as a question and does NOT make a version", async () => {
    await generate().expect(201);
    engine.changeReply = CONFLICTED;

    const res = await change({
      markings: [{ scioId: "booking-form-submit", note: "add payments here" }],
    }).expect(201);

    expect(res.body.applied).toBe(false);
    expect(res.body.conflicts[0].specSays).toBe("no payments for now");
    expect(res.body.conflicts[0].question).toContain("Do you want it");
    expect(res.body.summary).toContain("need your call");
    // Nothing was built, so nothing was versioned.
    expect(scope.designVersions).toHaveLength(1);
  });

  it("a marking that could not be addressed is named, not swallowed", async () => {
    await generate().expect(201);
    engine.changeReply = {
      ...APPLIED,
      unaddressable: [
        {
          marking: { scio_id: null, note: "this bit" },
          error: "The element you marked (<div>) has no data-scio-id.",
        },
      ],
    };

    const res = await change({ markings: [{ scioId: null, note: "this bit" }] }).expect(201);

    expect(res.body.applied).toBe(true);
    expect(res.body.skipped[0].error).toContain("no data-scio-id");
    expect(res.body.summary).toContain("could not be addressed");
  });

  it("refuses a change before there is a preview to change", async () => {
    await change({ markings: [{ scioId: "booking-form-submit", note: "say Reserve" }] }).expect(409);
    expect(engine.changes).toHaveLength(0);
  });

  // ------------------------------------------------------------------
  // Scoping
  // ------------------------------------------------------------------

  it("is 404 for another workspace's project, and touches nothing", async () => {
    await generate().expect(201);

    await request(http).get("/projects/p1/design").set(w2).expect(404);
    await request(http)
      .post("/projects/p1/design/change")
      .set(w2)
      .send({ markings: [{ scioId: "booking-form-submit", note: "hijack" }] })
      .expect(404);

    expect(engine.changes).toHaveLength(0);
  });

  it("rejects unauthenticated callers", async () => {
    await request(http).get("/projects/p1/design").expect(401);
    await request(http).post("/projects/p1/design/change").send({ markings: [] }).expect(401);
  });

  it("lists design versions newest first", async () => {
    await generate().expect(201);
    await change({ markings: [{ scioId: "booking-form-submit", note: "say Reserve" }] }).expect(201);

    const res = await request(http).get("/projects/p1/design-versions").set(w1).expect(200);

    expect(res.body.designVersions.map((d: { number: number }) => d.number)).toEqual([2, 1]);
  });

  // ------------------------------------------------------------------
  // Answering a conflict, and going back
  // ------------------------------------------------------------------

  const amend = (body: unknown) =>
    request(http).post("/projects/p1/spec/amend").set(w1).send(body);

  it("drops a non-goal from the spec when the user says they want it after all", async () => {
    scope.specVersions = [
      {
        id: "s1",
        projectId: "p1",
        number: 1,
        content: {
          purpose: {},
          non_goals: { value: ["no payments for now", "no mobile app"], source: "user", provenance: [] },
        },
        assumptions: {},
        isCurrent: true,
      },
    ];

    const res = await amend({ kind: "non_goal", specSays: "no payments for now" }).expect(201);

    expect(res.body.removedNonGoal).toBe("no payments for now");
    expect(res.body.specVersion.number).toBe(2);
    const frozen = scope.specVersions.find((v) => v.number === 2);
    expect(frozen.content.non_goals.value).toEqual(["no mobile app"]);
    // The old version is still readable — a build points at it.
    expect(scope.specVersions.find((v) => v.number === 1).content.non_goals.value).toHaveLength(2);
  });

  it("records a security decision as an ALLOWANCE, leaving the posture alone", async () => {
    const res = await amend({
      kind: "access",
      specSays: "personal data, with row-level security on",
      note: "make the bookings public",
    }).expect(201);

    expect(res.body.allowances).toEqual(["personal data, with row-level security on"]);
    expect(res.body.removedNonGoal).toBeNull();
    const frozen = scope.specVersions.find((v) => v.number === 2);
    // The spec still says what it said. What changed is the record of what the
    // user was asked and permitted — ADR-0001's wedge stays intact.
    expect(frozen.content).toEqual({ purpose: {} });
    expect(frozen.assumptions.amendments[0]).toMatchObject({
      kind: "access",
      note: "make the bookings public",
    });
  });

  it("tells the engine which questions have already been answered", async () => {
    await generate().expect(201);
    await amend({ kind: "auth", specSays: "sign-in via supabase-auth" }).expect(201);

    await change({ markings: [{ scioId: "booking-form-submit", note: "remove the login" }] }).expect(
      201,
    );

    expect(engine.changes[0].allowances).toEqual(["sign-in via supabase-auth"]);
  });

  it("does not fail when the same conflict is answered twice", async () => {
    await amend({ kind: "auth", specSays: "sign-in via supabase-auth" }).expect(201);
    const res = await amend({ kind: "auth", specSays: "sign-in via supabase-auth" }).expect(201);

    expect(res.body.allowances).toEqual(["sign-in via supabase-auth"]);
  });

  it("returns to an earlier version by its commit, and records the return", async () => {
    await generate().expect(201);
    await change({ markings: [{ scioId: "booking-form-submit", note: "say Reserve" }] }).expect(201);
    const first = scope.designVersions.find((d) => d.number === 1);

    const res = await request(http)
      .post(`/projects/p1/design-versions/${first.id}/restore`)
      .set(w1)
      .expect(201);

    expect(res.body.restored).toBe(true);
    expect(engine.restores[0]).toMatchObject({
      app_dir: "/tmp/scio/p1",
      git_sha: "3a28a30d9de2",
    });
    // Forward, not backward: going back is itself a version, so changing your
    // mind twice still works.
    expect(scope.designVersions).toHaveLength(3);
    expect(JSON.parse(scope.designVersions.find((d) => d.number === 3).ref).change).toBe(
      "returned to version 1",
    );
  });

  it("says why a version cannot be returned to, rather than failing", async () => {
    await generate().expect(201);
    engine.restoreReply = { ...RESTORED, restored: false, error: "that version no longer verifies" };
    const first = scope.designVersions.find((d) => d.number === 1);

    const res = await request(http)
      .post(`/projects/p1/design-versions/${first.id}/restore`)
      .set(w1)
      .expect(201);

    expect(res.body.restored).toBe(false);
    expect(res.body.error).toContain("no longer verifies");
    expect(scope.designVersions).toHaveLength(1);
  });

  it("never restores across tenants", async () => {
    await generate().expect(201);
    const first = scope.designVersions.find((d) => d.number === 1);

    await request(http).post(`/projects/p1/design-versions/${first.id}/restore`).set(w2).expect(404);

    expect(engine.restores).toHaveLength(0);
  });
});

