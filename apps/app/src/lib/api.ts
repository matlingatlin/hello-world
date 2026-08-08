import type { CreateProjectRequest, ProjectListResponse, ProjectResponse } from "@scio/shared";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
  get unauthorized() {
    return this.status === 401;
  }
}

export type GetToken = () => Promise<string | null>;

/** Typed client for the Scio API. Attaches the Clerk session JWT per request. */
export function createApi(getToken: GetToken, baseUrl?: string) {
  const base = (baseUrl ?? import.meta.env.VITE_API_URL ?? "http://localhost:3000").replace(
    /\/$/,
    "",
  );

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await getToken();
    let res: Response;
    try {
      res = await fetch(`${base}${path}`, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(init?.headers ?? {}),
        },
      });
    } catch {
      throw new ApiError(0, "Can't reach the Scio API — is the backend running?");
    }
    if (!res.ok) {
      let message = res.statusText || `Request failed (${res.status})`;
      try {
        const body = await res.json();
        const m = body?.message;
        message = Array.isArray(m) ? m.join(", ") : (m ?? message);
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(res.status, message);
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }

  return {
    listProjects: () => request<ProjectListResponse>("/projects"),
    createProject: (body: CreateProjectRequest) =>
      request<ProjectResponse>("/projects", { method: "POST", body: JSON.stringify(body) }),
  };
}

export type Api = ReturnType<typeof createApi>;
