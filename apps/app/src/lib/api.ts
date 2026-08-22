import type {
  AmendSpecRequest,
  AmendSpecResponse,
  ApplyDesignChangeRequest,
  ApplyDesignChangeResponse,
  BuildEvent,
  BuildJobResponse,
  ApproveSpecResponse,
  CorrectSpecFieldRequest,
  CorrectSpecFieldResponse,
  CreateProjectRequest,
  DesignPreviewEvent,
  DesignPreviewResponse,
  DesignVersionListResponse,
  IntakeStepResponse,
  LatestBuildResponse,
  ProjectListResponse,
  ProjectResponse,
  RestoreDesignVersionResponse,
} from "@scio/shared";

/**
 * What the client says when the connection, rather than the work, went away.
 *
 * Carried as status 0 — no server ever answered — so a caller can tell "we
 * stopped hearing about the build" from "the build failed", which the build
 * screen owes the user: it promises the build keeps running when you leave.
 */
export const CONNECTION_LOST = "The connection dropped — the work is still running on the server.";

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

/**
 * Did we lose the connection, or did the work fail?
 *
 * Status 0 is what this client raises when nothing answered, and anything that
 * is not an `ApiError` never reached the server to begin with. Everything else
 * is a real answer from the api and belongs to whoever asked for it.
 */
export function lostConnection(err: unknown): boolean {
  return !(err instanceof ApiError) || err.status === 0;
}

/**
 * The key that names one build request, kept for as long as it is unanswered.
 *
 * Minted per project and remembered in `sessionStorage`, so a reload, a
 * reconnect or an impatient second click all ask for the SAME build rather than
 * a second one — and if that build finished while nobody was listening, the api
 * replays it instead of rebuilding the app (B103).
 *
 * `clearBuildKey` is called once a build is known to have finished, so the next
 * deliberate build is a new request rather than a replay of the old one.
 * Storage that is unavailable (private mode, a locked-down browser) simply
 * yields a fresh key: worse deduplication, never a crash.
 */
const BUILD_KEY = (projectId: string) => `scio.build-key.${projectId}`;

export function buildKey(projectId: string): string {
  const fresh = crypto.randomUUID();
  try {
    const existing = sessionStorage.getItem(BUILD_KEY(projectId));
    if (existing) return existing;
    sessionStorage.setItem(BUILD_KEY(projectId), fresh);
  } catch {
    /* no storage: the key still names this request, just not the next one */
  }
  return fresh;
}

export function clearBuildKey(projectId: string): void {
  try {
    sessionStorage.removeItem(BUILD_KEY(projectId));
  } catch {
    /* nothing to clear */
  }
}

export type GetToken = () => Promise<string | null>;

/** Typed client for the Scio API. Attaches the Clerk session JWT per request. */
export function createApi(getToken: GetToken, baseUrl?: string) {
  // Every route the app calls is versioned (B103); `/health` is not, because
  // nothing here calls it.
  const base = `${(baseUrl ?? import.meta.env.VITE_API_URL ?? "http://localhost:3000").replace(
    /\/$/,
    "",
  )}/v1`;

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
      onEvent: (event: DesignPreviewEvent) => void,
      signal?: AbortSignal,
    ) =>
      streamSse<DesignPreviewEvent>(`/projects/${projectId}/design/preview`, onEvent, signal),
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
    /** What is building right now, or `null`. Empty object means nothing. */
    currentBuildJob: (projectId: string) =>
      request<BuildJobResponse | Record<string, never>>(`/projects/${projectId}/build/job`),
    /** Stop the build. It ends at the next part, where the workspace is whole. */
    cancelBuild: (projectId: string) =>
      request<{ cancelled: boolean }>(`/projects/${projectId}/build`, { method: "DELETE" }),
    /**
     * Run the build, streamed.
     *
     * Carries an idempotency key so a retry — a reload, a dropped stream, a
     * second click — replays the build it already asked for instead of starting
     * (and paying for) another one (B103).
     */
    streamBuild: (
      projectId: string,
      onEvent: (event: BuildEvent) => void,
      signal?: AbortSignal,
    ) =>
      streamSse<BuildEvent>(`/projects/${projectId}/build`, onEvent, signal, {
        "Idempotency-Key": buildKey(projectId),
      }),
  };

  /**
   * SSE over fetch, not EventSource.
   *
   * EventSource cannot send an Authorization header, and the build stream is
   * workspace-scoped — so it is read off the response body instead, which also
   * lets a POST start the build.
   */
  async function streamSse<E extends { event: string; data: unknown }>(
    path: string,
    onEvent: (event: E) => void,
    signal?: AbortSignal,
    extraHeaders: Record<string, string> = {},
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
          ...extraHeaders,
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
    // Every Scio stream ends with `finished` or `error`: the api emits one on
    // each path out of the handler. So a stream that ends with neither did not
    // end — the connection did, and the difference is invisible to `await`.
    let terminal = false;
    while (true) {
      let chunk: ReadableStreamReadResult<Uint8Array>;
      try {
        // Scoped to the read alone: an exception from `onEvent` below is the
        // page's bug, not a dead socket, and must not be reported as one.
        chunk = await reader.read();
      } catch {
        throw new ApiError(0, CONNECTION_LOST);
      }
      if (chunk.done) break;
      buffer += decoder.decode(chunk.value, { stream: true });
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
        let payload: unknown;
        try {
          payload = JSON.parse(raw);
        } catch {
          continue; // a frame we cannot read is dropped, never guessed at
        }
        if (name === "finished" || name === "error") terminal = true;
        // The one unchecked cast in the stream, and it is here on purpose: this
        // is the wire, where a claim about the shape of someone else's JSON is
        // unavoidable. Everywhere downstream switches on `event` and gets the
        // right `data` from the compiler instead of casting again (B089).
        onEvent({ event: name, data: payload } as E);
      }
    }
    if (!terminal) throw new ApiError(0, CONNECTION_LOST);
  }
}

export type Api = ReturnType<typeof createApi>;
