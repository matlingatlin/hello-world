import { BadRequestException, Injectable, Logger, ServiceUnavailableException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import type { IntakeSpec } from "@scio/shared";

/**
 * The API's one way in to the engine (ADR-0006: Node for the product surface,
 * Python for the engine). Everything crosses this boundary over HTTP, so the
 * engine can be scaled, restarted or run on a different machine without the API
 * knowing.
 *
 * Failures are separated on purpose. `intakeStep` is the turn itself — if it
 * fails the user gets nothing, so it throws. `architecture` and `plan` decorate
 * the review screen; if they fail the user should still see their spec, so those
 * return null and the caller reports the build as degraded rather than broken.
 */

export interface EngineIntakeStepRequest {
  messages: Array<{ id: string; role: string; text: string }>;
  spec: IntakeSpec | null;
  extraction_passes?: number;
  question_passes?: number;
}

export interface EngineIntakeStepResponse {
  updated_spec: IntakeSpec;
  buildable: boolean;
  next_question: {
    field: string;
    text: string;
    example: string;
    about: "field" | "contradiction";
    written_by: "model" | "guide";
  } | null;
  /** What this exchange cost. One relay call per user message, and the last
   *  spend in the product the ledger could not see. */
  cost_usd?: number;
  contradictions: Array<{ fields: string[]; description: string; resolved: boolean }>;
  gate: {
    buildable: boolean;
    missing_core: string[];
    unresolved_conditionals: string[];
    contradictions: Array<{ fields: string[]; description: string; resolved: boolean }>;
  };
  triggered: string[];
  extraction: Record<string, unknown>;
}

/** The gate verdict on its own, for a spec that is already stored. */
export interface EngineValidateResponse {
  result: {
    buildable: boolean;
    missing_core: string[];
    unresolved_conditionals: string[];
    contradictions: Array<{ fields: string[]; description: string; resolved: boolean }>;
  };
  triggered: string[];
  still_needed: string[];
}

export interface EngineCorrectRequest {
  spec: IntakeSpec;
  correction: { field: string; value: unknown; clear: string[] };
}

export interface EngineCorrectResponse {
  updated_spec: IntakeSpec;
  gate: EngineValidateResponse["result"];
  triggered: string[];
  still_needed: string[];
  newly_required: string[];
  changed: string[];
  cleared: string[];
}

/**
 * Layer B's "whole" is an object, not a string: the narrative plus the honest
 * bookkeeping around it. `generated` is false when the engine had no real model
 * and fell back to its deterministic narrative — plainer, but never wrong.
 */
export interface EngineWhole {
  narrative: string;
  assumptions: string[];
  grounding: Record<string, string>;
  models_used: string[];
  generated: boolean;
}

export interface EngineArchitectureResponse {
  whole?: EngineWhole;
  architecture?: Record<string, unknown>;
  validation?: Record<string, unknown>;
  [key: string]: unknown;
}

/**
 * The shared secret, when one is configured.
 *
 * The engine authenticated nobody until now. Unset here and there means the
 * local stack, where there is no secret to share; set it in both and every call
 * carries it.
 */
function engineAuth(): Record<string, string> {
  const token = process.env.SCIO_ENGINE_TOKEN ?? "";
  return token ? { "x-scio-engine-token": token } : {};
}

/** Promote an existing design workspace to the delivered build (B070). */
export interface EnginePromoteRequest {
  app_dir: string;
  project_id: string;
  build_version: number;
  budget_usd?: number;
}

export interface EngineBuildRequest {
  spec: IntakeSpec;
  project_id: string;
  build_version: number;
  max_attempts?: number;
  /** Level 2 only. Set it and the build carries the design window's marking
   *  bridge, pinned to this origin. Absent = a delivery build, with no bridge. */
  shell_origin?: string;
  /** The ceiling this build may spend, from the estimate the user approved
   *  against. The relay refuses the call that would cross it, so the build
   *  stops with what it has instead of running past what was agreed. */
  budget_usd?: number;
}

/** A batch of markings, on their way to the engine's directed change. */
export interface EngineDesignChangeRequest {
  app_dir: string;
  spec: IntakeSpec;
  batch: {
    markings: Array<Record<string, unknown>>;
    prompt: string;
  };
  package_files: Record<string, string[]>;
  passes?: number;
  /** What this batch may spend, across every package it touches. A directed
   *  change is the cheap, frequent interaction and had no ceiling at all. */
  budget_usd?: number;
  /** Conflicts the user has already answered yes to, quoted by the exact
   *  `spec_says` the question used. Frozen on the spec, not a request flag. */
  allowances?: string[];
}

/** Going back to an earlier design version. */
export interface EngineDesignRestoreRequest {
  app_dir: string;
  git_sha: string;
  package_files: Record<string, string[]>;
}

export interface EngineDesignRestoreResponse {
  restored: boolean;
  git_sha: string;
  head: string;
  manifest: Record<string, unknown> | null;
  error: string;
}

export interface EngineDesignChangeResponse {
  applied: boolean;
  conflicts: Array<{
    kind: string;
    scio_id: string;
    note: string;
    spec_says: string;
    question: string;
  }>;
  packages: Array<{
    package: string;
    edited_files: string[];
    unchanged_files: number;
    isolated: boolean;
    accepted: boolean;
    rejection: string;
  }>;
  unaddressable: Array<{
    marking: { scio_id: string | null; note: string };
    error: string;
  }>;
  manifest: Record<string, unknown> | null;
  total_cost_usd: number;
  description: string;
  /** The commit the change produced. Empty means it is on disk and cannot be
   *  returned to — `persistence_error` says why. */
  git_sha: string;
  persistence_error: string;
}

/** One `event:`/`data:` frame from an SSE stream. */
function parseFrame(frame: string): { event: string; data: Record<string, unknown> } | null {
  let event = "message";
  let raw = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event: ")) event = line.slice(7).trim();
    else if (line.startsWith("data: ")) raw += line.slice(6);
  }
  if (!raw) return null;
  try {
    return { event, data: JSON.parse(raw) as Record<string, unknown> };
  } catch {
    return null; // a frame we cannot read is dropped, not guessed at
  }
}

export interface EnginePlanResponse {
  plan?: { packages?: Array<{ id: string }>; order?: string[] };
  /** Deterministic, computed by the engine alongside the plan — no model call. */
  estimate?: {
    cost_usd?: { low: number; high: number };
    minutes?: { low: number; high: number };
    composition?: { parts_total: number; assembled: number; generated: number };
    model?: string;
    passes?: number;
    basis?: string;
  } | null;
  [key: string]: unknown;
}

export class EngineUnavailableError extends ServiceUnavailableException {
  constructor(detail: string) {
    super(`The Scio engine is not reachable (${detail}).`);
  }
}

/**
 * The engine answered, and said no.
 *
 * Kept apart from `EngineUnavailableError` because the two mean opposite things
 * to the person on the other end. "We could not reach the engine" invites a
 * retry; "that value is the wrong shape for that field" invites a fix, and
 * telling someone their typo is an outage is how a product stops being
 * believed. The engine's own message is passed through — it names the field.
 */
export class EngineRefusedError extends BadRequestException {
  constructor(detail: string) {
    super(detail);
  }
}

/** FastAPI puts the reason in `detail`; anything else is passed through as-is. */
function readDetail(body: string): string | null {
  try {
    const parsed = JSON.parse(body) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) return parsed.detail;
  } catch {
    /* not JSON — fall through */
  }
  return body.trim() ? body.slice(0, 300) : null;
}

@Injectable()
export class EngineClient {
  private readonly logger = new Logger(EngineClient.name);

  constructor(private readonly config: ConfigService) {}

  get baseUrl(): string {
    return (this.config.get<string>("ENGINE_URL") ?? "http://localhost:8000").replace(/\/$/, "");
  }

  private async post<T>(path: string, body: unknown, timeoutMs: number): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json",
        ...engineAuth() },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) {
        const detail = await res.text().catch(() => "");
        // A 4xx is a refusal with a reason, not an outage — see EngineRefusedError.
        if (res.status >= 400 && res.status < 500) {
          throw new EngineRefusedError(readDetail(detail) ?? `${path} returned ${res.status}`);
        }
        throw new EngineUnavailableError(`${path} returned ${res.status}: ${detail.slice(0, 300)}`);
      }
      return (await res.json()) as T;
    } catch (err) {
      if (err instanceof EngineUnavailableError || err instanceof EngineRefusedError) throw err;
      const reason = err instanceof Error ? err.message : String(err);
      throw new EngineUnavailableError(`${path}: ${reason}`);
    } finally {
      clearTimeout(timer);
    }
  }

  /** One wizard turn. Throws when the engine cannot answer — there is no turn without it. */
  intakeStep(body: EngineIntakeStepRequest): Promise<EngineIntakeStepResponse> {
    return this.post<EngineIntakeStepResponse>("/intake/step", body, 120_000);
  }

  /**
   * The gate verdict for a spec, with no conversation turn attached.
   *
   * Deterministic and free — no model runs — which is what lets a plain GET of
   * the wizard answer "how far along am I" instead of guessing. Null rather
   * than throwing: a reload that cannot reach the engine still shows the spec.
   */
  async validate(spec: IntakeSpec): Promise<EngineValidateResponse | null> {
    try {
      return await this.post<EngineValidateResponse>("/intake/validate", spec, 30_000);
    } catch (err) {
      this.logger.warn(`validate unavailable: ${(err as Error).message}`);
      return null;
    }
  }

  /**
   * Correct a field the wizard filed wrongly, and re-run Layer A's gate.
   *
   * Throws rather than returning null, and for the same reason `designChange`
   * does: the user pressed save on a correction, and "we could not reach the
   * engine" is the answer — a correction that silently did not happen would
   * leave them looking at a spec they believe they have fixed.
   *
   * A 400 from the engine is a refusal, not an outage: the value was the wrong
   * shape for the field, and the message names which.
   */
  correct(body: EngineCorrectRequest): Promise<EngineCorrectResponse> {
    return this.post<EngineCorrectResponse>("/intake/correct", body, 30_000);
  }

  /**
   * Apply a batch of markings to only the packages they touch.
   *
   * Throws rather than returning null: unlike the review screen's decorations,
   * a change the user pressed go on has no useful degraded state — "we could
   * not reach the engine" is the answer, not a silent no-op.
   */
  designChange(body: EngineDesignChangeRequest): Promise<EngineDesignChangeResponse> {
    return this.post<EngineDesignChangeResponse>("/design/change", body, 900_000);
  }

  /**
   * Put an earlier design version's code back.
   *
   * No model runs, so the budget is a file operation's rather than a build's.
   * "That version cannot be restored" comes back as `restored: false` with the
   * reason — a refusal is an answer, and the engine has already put the working
   * tree back where it was.
   */
  designRestore(body: EngineDesignRestoreRequest): Promise<EngineDesignRestoreResponse> {
    return this.post<EngineDesignRestoreResponse>("/design/restore", body, 120_000);
  }

  /** Layer B, for the review screen's confirmation. Null rather than throwing. */
  async architecture(spec: IntakeSpec): Promise<EngineArchitectureResponse | null> {
    try {
      return await this.post<EngineArchitectureResponse>(
        "/architecture",
        { spec, whole_passes: 2 },
        180_000,
      );
    } catch (err) {
      this.logger.warn(`architecture unavailable: ${(err as Error).message}`);
      return null;
    }
  }

  /**
   * The whole build, streamed.
   *
   * Events are handed to the caller one at a time rather than collected: a build
   * takes minutes, and the build view's progress is only honest if it arrives
   * while the parts are actually finishing.
   */
  async streamBuild(
    body: EngineBuildRequest,
    onEvent: (event: string, data: Record<string, unknown>) => Promise<void> | void,
  ): Promise<void> {
    return this.streamEvents("/build", body, onEvent);
  }

  /**
   * Deliver the app a design session produced, without rebuilding it (B070).
   *
   * The same events in the same order as `/build`, because to everything
   * downstream it IS a build: it produces the delivered version. What it does
   * not do is regenerate the code — the user shaped that code by hand in the
   * design window, and a fresh generation from the spec would contain none of
   * it.
   */
  async promoteBuild(
    body: EnginePromoteRequest,
    onEvent: (event: string, data: Record<string, unknown>) => Promise<void> | void,
  ): Promise<void> {
    return this.streamEvents("/build/promote", body, onEvent);
  }

  private async streamEvents(
    path: string,
    body: unknown,
    onEvent: (event: string, data: Record<string, unknown>) => Promise<void> | void,
  ): Promise<void> {
    let res: Response;
    try {
      res = await fetch(`${this.baseUrl}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json",
        ...engineAuth(), Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });
    } catch (err) {
      throw new EngineUnavailableError(`${path}: ${(err as Error).message}`);
    }
    if (!res.ok || !res.body) {
      throw new EngineUnavailableError(`${path} returned ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE frames are separated by a blank line; a partial frame stays buffered.
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const parsed = parseFrame(frame);
        if (parsed) await onEvent(parsed.event, parsed.data);
      }
    }
  }

  /**
   * Delete a project's code and stop its app (B100).
   *
   * Never throws: deleting a project must not fail because a directory would
   * not go. The report says what actually happened, and the caller records it
   * rather than assuming — the one thing neither of us may do is claim the code
   * is gone when it is still there.
   */
  async discardWorkspace(
    projectId: string,
    previewUrl: string,
  ): Promise<{ stopped_preview: boolean; removed: string[]; problems: string[] }> {
    try {
      return await this.post(
        "/workspace/discard",
        { project_id: projectId, preview_url: previewUrl },
        30_000,
      );
    } catch (err) {
      return {
        stopped_preview: false,
        removed: [],
        problems: [`the engine could not be reached: ${(err as Error).message}`],
      };
    }
  }

  /** Layer C, for the rough part count. Null rather than throwing. */
  async plan(architecture: Record<string, unknown>, whole: string): Promise<EnginePlanResponse | null> {
    try {
      return await this.post<EnginePlanResponse>(
        "/plan",
        { architecture, whole, use_judgment: false },
        180_000,
      );
    } catch (err) {
      this.logger.warn(`plan unavailable: ${(err as Error).message}`);
      return null;
    }
  }
}
