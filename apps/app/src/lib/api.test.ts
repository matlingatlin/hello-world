import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createApi } from "./api";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  afterEach(() => vi.restoreAllMocks());

  it("attaches the Clerk token as a bearer header", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(200, { projects: [] }));
    const api = createApi(async () => "jwt-123", "http://api.test");

    await api.listProjects();

    const [url, init] = fetchMock.mock.calls[0];
    // Versioned, so the first breaking change has somewhere to go (B103).
    expect(url).toBe("http://api.test/v1/projects");
    expect((init?.headers as Record<string, string>).Authorization).toBe("Bearer jwt-123");
  });

  it("marks 401 responses as unauthorized", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(401, { message: "Missing bearer token" }),
    );
    const api = createApi(async () => null, "http://api.test");

    const err = await api.listProjects().catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(401);
    expect(err.unauthorized).toBe(true);
    expect(err.message).toBe("Missing bearer token");
  });

  it("joins validation error arrays into one message", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(400, { message: ["name should not be empty", "name must be a string"] }),
    );
    const api = createApi(async () => "jwt", "http://api.test");

    const err = await api.createProject({ name: "" }).catch((e) => e);
    expect(err.status).toBe(400);
    expect(err.message).toContain("name should not be empty");
  });

  it("posts create bodies as JSON", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(201, { project: { id: "p1" } }));
    const api = createApi(async () => "jwt", "http://api.test");

    await api.createProject({ name: "Bistro", type: "app" });

    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({ name: "Bistro", type: "app" });
  });

  it("wraps network failures as a reachable error (status 0)", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fetch failed"));
    const api = createApi(async () => "jwt", "http://api.test");

    const err = await api.listProjects().catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(0);
    expect(err.message).toMatch(/backend running/);
  });
});

describe("streams", () => {
  afterEach(() => vi.restoreAllMocks());

  /** An SSE response whose body is exactly these frames, then ends. */
  function sseResponse(frames: string[], { fail = false } = {}): Response {
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const frame of frames) controller.enqueue(new TextEncoder().encode(frame));
        if (fail) controller.error(new TypeError("network error"));
        else controller.close();
      },
    });
    return new Response(body, {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  it("delivers named events with their parsed data", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      sseResponse([
        'event: progress\ndata: {"done":1}\n\n',
        'event: finished\ndata: {"app_url":"http://x"}\n\n',
      ]),
    );
    const api = createApi(async () => "jwt", "http://api.test");
    const seen: Array<[string, unknown]> = [];

    await api.streamBuild("p1", (frame) => {
      seen.push([frame.event, frame.data]);
    });

    expect(seen).toEqual([
      ["progress", { done: 1 }],
      ["finished", { app_url: "http://x" }],
    ]);
  });

  it("ignores the keep-alive comments that hold a quiet build open", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      sseResponse([": keep-alive\n\n", ": keep-alive\n\n", 'event: finished\ndata: {}\n\n']),
    );
    const api = createApi(async () => "jwt", "http://api.test");
    const seen: string[] = [];

    await api.streamBuild("p1", (frame) => {
      seen.push(frame.event);
    });

    expect(seen).toEqual(["finished"]);
  });

  it("calls a stream that dies mid-flight a lost connection, not a failed build", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      sseResponse(['event: progress\ndata: {"done":1}\n\n'], { fail: true }),
    );
    const api = createApi(async () => "jwt", "http://api.test");

    const err = await api.streamBuild("p1", () => undefined).catch((e) => e);

    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(0);
  });

  it("treats a stream that ends without finished or error the same way", async () => {
    // This is the one that looked like success: the promise resolved, the page
    // had a half-drawn progress list, and nothing anywhere said why it stopped.
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      sseResponse(['event: progress\ndata: {"done":1}\n\n']),
    );
    const api = createApi(async () => "jwt", "http://api.test");

    const err = await api.streamBuild("p1", () => undefined).catch((e) => e);

    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(0);
  });

  it("does not mistake a page's own bug for a dead socket", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      sseResponse(['event: finished\ndata: {}\n\n']),
    );
    const api = createApi(async () => "jwt", "http://api.test");

    const err = await api
      .streamBuild("p1", () => {
        throw new Error("a render blew up");
      })
      .catch((e) => e);

    expect(err).not.toBeInstanceOf(ApiError);
    expect((err as Error).message).toBe("a render blew up");
  });
});
