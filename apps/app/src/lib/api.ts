import type {
  AmendSpecRequest,
  AmendSpecResponse,
  ApplyDesignChangeRequest,
  ApplyDesignChangeResponse,
  ApproveSpecResponse,
  CorrectSpecFieldRequest,
  CorrectSpecFieldResponse,
  CreateProjectRequest,
  DesignPreviewResponse,
  DesignVersionListResponse,
  IntakeStepResponse,
  LatestBuildResponse,
  ProjectListResponse,
  ProjectResponse,
  RestoreDesignVersionResponse,
} from "@scio/shared";

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
    getProject: (id: string) => request<ProjectResponse>(`/projects/${id}`),
    createProject: (body: CreateProjectRequest) =>
      request<ProjectResponse>("/projects", { method: "POST", body: JSON.stringify(body) }),

    // --- gate 1 ---
    getIntake: (projectId: string) => request<IntakeStepResponse>(`/projects/${projectId}/intake`),
    sendIntakeMessage: (projectId: string, text: string) =>
      request<IntakeStepResponse>(`/projects/${projectId}/intake/message`, {
        method: "POST",
        body: JSON.stringify({ text }),
      }),
    /**
     * Correct a field the wizard filed wrongly.
     *
     * Returns a whole turn, not a diff: the narrative, the assumptions and the
     * estimate all follow from the spec, so the review screen re-renders from
     * this rather than patching the row it just edited.
     */
    correctSpecField: (projectId: string, body: CorrectSpecFieldRequest) =>
      request<CorrectSpecFieldResponse>(`/projects/${projectId}/draft-spec/field`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    approveSpec: (projectId: string, whole?: string) =>
      request<ApproveSpecResponse>(`/projects/${projectId}/spec/approve`, {
        method: "POST",
        body: JSON.stringify({ whole }),
      }),

    // --- gate 2: the design window ---
    getDesign: (projectId: string) =>
      request<DesignPreviewResponse>(`/projects/${projectId}/design`),
    /** Build the preview the window embeds. Streamed: it takes minutes, and the
     *  progress is only honest if it comes from parts actually finishing. */
    streamDesignPreview: (
      projectId: string,
      onEvent: (event: string, data: Record<string, unknown>) => void,
      signal?: AbortSignal,
    ) => streamSse(`/projects/${projectId}/design/preview`, onEvent, signal),
    applyDesignChange: (projectId: string, body: ApplyDesignChangeRequest) =>
      request<ApplyDesignChangeResponse>(`/projects/${projectId}/design/change`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    listDesignVersions: (projectId: string) =>
      request<DesignVersionListResponse>(`/projects/${projectId}/design-versions`),
    restoreDesignVersion: (projectId: string, versionId: string) =>
      request<RestoreDesignVersionResponse>(
        `/projects/${projectId}/design-versions/${versionId}/restore`,
        { method: "POST" },
      ),
    /** Answer a conflict by changing the approved spec. A new spec version. */
    amendSpec: (projectId: string, body: AmendSpecRequest) =>
      request<AmendSpecResponse>(`/projects/${projectId}/spec/amend`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    // --- the build ---
    latestBuild: (projectId: string) =>
      request<LatestBuildResponse>(`/projects/${projectId}/build/latest`),
    streamBuild: (
      projectId: string,
      onEvent: (event: string, data: Record<string, unknown>) => void,
      signal?: AbortSignal,
    ) => streamSse(`/projects/${projectId}/build`, onEvent, signal),
  };

  /**
   * SSE over fetch, not EventSource.
   *
   * EventSource cannot send an Authorization header, and the build stream is
   * workspace-scoped — so it is read off the response body instead, which also
   * lets a POST start the build.
   */
  async function streamSse(
    path: string,
    onEvent: (event: string, data: Record<string, unknown>) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const token = await getToken();
    let res: Response;
    try {
      res = await fetch(`${base}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        signal,
      });
    } catch {
      throw new ApiError(0, "Can't reach the Scio API — is the backend running?");
    }
    if (!res.ok || !res.body) {
      throw new ApiError(res.status, res.statusText || "The build could not start");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        let name = "message";
        let raw = "";
        for (const line of frame.split("\n")) {
          if (line.startsWith("event: ")) name = line.slice(7).trim();
          else if (line.startsWith("data: ")) raw += line.slice(6);
        }
        if (!raw) continue;
        try {
          onEvent(name, JSON.parse(raw) as Record<string, unknown>);
        } catch {
          /* a frame we cannot read is dropped, never guessed at */
        }
      }
    }
  }
}

export type Api = ReturnType<typeof createApi>;
