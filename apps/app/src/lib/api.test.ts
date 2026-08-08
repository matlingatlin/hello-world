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
    expect(url).toBe("http://api.test/projects");
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
