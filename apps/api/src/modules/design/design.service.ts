import {
  ConflictException,
  Injectable,
  Logger,
  NotFoundException,
} from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import type {
  ApplyDesignChangeRequest,
  ApplyDesignChangeResponse,
  DesignPreviewResponse,
  DesignVersion,
  DesignVersionListResponse,
  DesignVersionResponse,
  FreezeDesignRequest,
  IntakeSpec,
  RestoreDesignVersionResponse,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";
import { allowancesOf } from "../spec/spec.service";
import { EngineClient } from "../../engine/engine.client";
import type { BuildFinished, DesignPreviewEventName } from "@scio/shared";

/**
 * Level 2 — "show me before you build it".
 *
 * The user gets a running preview of their app, marks things in it, says what
 * they want, and presses go. Only the parts they touched are rebuilt.
 *
 * Two things here are load-bearing and easy to get wrong:
 *
 * 1. **The preview is a different build from a delivery build.** It carries the
 *    marking bridge, which exists so the design window can hear about clicks it
 *    cannot see (the preview is cross-origin — spikes/design-marking). The
 *    engine only injects it when this service passes `shell_origin`, so a
 *    delivered app never contains it.
 * 2. **A change is a design version.** Every generate-again is recorded, because
 *    "go back to how it looked before I asked for that" is the whole reason
 *    someone is willing to keep asking.
 *
 * Conflicts are relayed, never resolved: if a marking argues with the approved
 * spec, the engine returns a question and builds nothing, and this service
 * passes that question straight through.
 */
@Injectable()
export class DesignService {
  private readonly logger = new Logger(DesignService.name);

  constructor(
    private readonly scope: WorkspaceScope,
    private readonly engine: EngineClient,
    private readonly config: ConfigService,
  ) {}

  private client(workspaceId: string) {
    return this.scope.forWorkspace(workspaceId);
  }

  private async project(workspaceId: string, projectId: string) {
    const row = await this.client(workspaceId).project.findFirst({
      where: { id: projectId, deletedAt: null },
    });
    // 404 rather than 403 across tenants — a 403 would confirm the id exists.
    if (!row) throw new NotFoundException("Project not found");
    return row;
  }

  /**
   * Where the design window is served from.
   *
   * The bridge posts only to this origin, and refusing to guess cuts both ways:
   * a wrong value makes marking go silent rather than broadcast, and a MISSING
   * value would produce a preview with no bridge in it at all — a design window
   * where clicking does nothing and nothing says why. So it is required, and
   * asked for by name.
   */
  private shellOrigin(): string {
    const configured =
      this.config.get<string>("APP_ORIGIN") ??
      (this.config.get<string>("CORS_ORIGINS") ?? "").split(",")[0];
    const origin = (configured ?? "").trim().replace(/\/$/, "");
    if (!origin) {
      throw new ConflictException(
        "APP_ORIGIN is not set, so a preview would be built without the marking bridge and " +
          "nothing in the design window would be clickable. Set APP_ORIGIN to the app's origin.",
      );
    }
    return origin;
  }

  private async currentSpec(workspaceId: string, projectId: string) {
    const specs = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const current =
      specs.find((s: { isCurrent: boolean }) => s.isCurrent) ?? specs[0];
    if (!current) {
      throw new ConflictException(
        "Approve a spec first — there is nothing to design against.",
      );
    }
    return current;
  }

  private async currentDesign(workspaceId: string, projectId: string) {
    const rows = await this.client(workspaceId).designVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    return (
      rows.find((r: { isCurrent: boolean }) => r.isCurrent) ?? rows[0] ?? null
    );
  }

  /**
   * A design version is a *pointer to a preview*, not a copy of one.
   *
   * `ref` carries what the design window needs to come back to this state: the
   * workspace it was built in, the running URL, the manifest markings resolve
   * against, and the file map isolation is proven against. Storing the manifest
   * rather than re-deriving it is deliberate — a manifest that has drifted from
   * the code is exactly how a marking targets the wrong package (B039).
   */

  /**
   * The design window spends real money too, and none of it was counted.
   *
   * `usage_event` was written by exactly one place — the delivery build — while
   * a preview build and every directed change make the same model calls. The
   * engine returned `total_cost_usd` for both and the api dropped it on the
   * floor, so a ledger that billing will rest on could not see the interaction
   * the product expects people to spend most of their time in.
   *
   * Never allowed to fail the work it is recording: a bookkeeping error must not
   * undo a preview the user is looking at.
   */
  /** What one batch of markings may spend. Deliberately generous and finite. */
  private static readonly CHANGE_CEILING_USD = 2.0;

  private async meter(
    workspaceId: string,
    projectId: string,
    kind: "preview" | "design_change",
    cost: number,
    tokens = 0,
    model: string | null = null,
  ): Promise<void> {
    if (!(cost > 0) && !(tokens > 0)) return;
    try {
      await this.client(workspaceId).usageEvent.create({
        data: { workspaceId, projectId, kind, model, amount: tokens, cost },
      });
    } catch (err) {
      this.logger.warn(`could not meter ${kind} for ${projectId}: ${(err as Error).message}`);
    }
  }

  private async record(
    workspaceId: string,
    projectId: string,
    ref: Record<string, unknown>,
  ): Promise<DesignVersion> {
    const client = this.client(workspaceId);
    const rows = await client.designVersion.findMany({ where: { projectId } });
    // One transaction, not two writes with a gap — see spec.service.approve.
    // Migration 0006 adds a partial unique index so the database refuses a
    // second current row too.
    const [, created] = await client.$transaction([
      client.designVersion.updateMany({
        where: { projectId, isCurrent: true },
        data: { isCurrent: false },
      }),
      client.designVersion.create({
        data: {
          projectId,
          number:
            Math.max(0, ...rows.map((r: { number: number }) => r.number)) + 1,
          ref: JSON.stringify(ref),
          isCurrent: true,
        },
      }),
    ]);
    return this.asDto(created);
  }

  private asDto(row: Record<string, unknown>): DesignVersion {
    return {
      id: row.id as string,
      projectId: row.projectId as string,
      number: row.number as number,
      ref: row.ref as string,
      isCurrent: row.isCurrent as boolean,
      createdAt: new Date(row.createdAt as string).toISOString(),
    };
  }

  private refOf(row: { ref: string } | null): Record<string, unknown> {
    if (!row) return {};
    try {
      return JSON.parse(row.ref) as Record<string, unknown>;
    } catch {
      return {};
    }
  }

  async list(
    workspaceId: string,
    projectId: string,
  ): Promise<DesignVersionListResponse> {
    await this.project(workspaceId, projectId);
    const rows = await this.client(workspaceId).designVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    return {
      designVersions: rows.map((row: Record<string, unknown>) =>
        this.asDto(row),
      ),
    };
  }

  /**
   * Generate the preview the design window embeds.
   *
   * Streamed for the same reason a build is: it takes minutes, and a progress
   * bar that is not driven by parts actually finishing is a lie. The caller
   * gets every event; the design version is written when the engine reports a
   * finished preview.
   */
  async generate(
    workspaceId: string,
    projectId: string,
    emit: (
      event: DesignPreviewEventName,
      data: Record<string, unknown>,
    ) => Promise<void> | void,
  ): Promise<void> {
    await this.project(workspaceId, projectId);
    const spec = await this.currentSpec(workspaceId, projectId);

    let finished: BuildFinished | null = null;
    let failure: string | null = null;

    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { status: "building" },
    });

    try {
      await this.engine.streamBuild(
        {
          spec: spec.content as IntakeSpec,
          project_id: projectId,
          build_version: 1,
          // The one thing that makes this a PREVIEW build rather than a
          // delivery build: with it the app carries the marking bridge.
          shell_origin: this.shellOrigin(),
        },
        async (event, data) => {
          // Off the wire as a string; the union is what everything downstream
          // is entitled to assume (B089).
          const name = event as DesignPreviewEventName;
          if (name === "finished") finished = data as unknown as BuildFinished;
          if (name === "error")
            failure = String(data.message ?? "the preview failed");
          await emit(name, data);
        },
      );
    } catch (err) {
      failure = (err as Error).message;
      await emit("error", { type: "engine_unavailable", message: failure });
    }

    if (!finished) {
      this.logger.warn(
        `preview for ${projectId} produced nothing: ${failure ?? "unknown"}`,
      );
      // Every stream owes its reader a last word. See build.service.run.
      if (!failure) {
        await emit("error", {
          type: "no_result",
          message: "The engine stopped without producing a preview.",
        });
      }
      await this.client(workspaceId).project.update({
        where: { id: projectId },
        data: { status: "error" },
      });
      return;
    }

    const result = finished as BuildFinished;
    await this.meter(
      workspaceId,
      projectId,
      "preview",
      result.total_cost_usd ?? 0,
      result.total_tokens ?? 0,
      result.model ?? null,
    );
    const version = await this.record(workspaceId, projectId, {
      workspace: result.workspace ?? "",
      previewUrl: result.app_url ?? "",
      manifest: result.manifest ?? null,
      packageFiles: result.package_files ?? {},
      summary: result.summary ?? "",
      whole: result.whole ?? "",
      change: "the first preview",
      gitSha: result.git_sha ?? "",
    });

    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { status: "ready", previewUrl: result.app_url || null },
    });
    await emit("design_version", { ...version });
  }

  /** What the design window loads when it opens: the current preview. */
  async current(
    workspaceId: string,
    projectId: string,
  ): Promise<DesignPreviewResponse> {
    await this.project(workspaceId, projectId);
    const row = await this.currentDesign(workspaceId, projectId);
    const ref = this.refOf(row);
    return {
      previewUrl: (ref.previewUrl as string) || null,
      manifest: (ref.manifest as Record<string, unknown>) ?? null,
      designVersion: row ? this.asDto(row) : null,
      whole: (ref.whole as string) || null,
      summary: (ref.summary as string) ?? "",
    };
  }

  /**
   * Apply a batch of markings.
   *
   * The api does not decide anything about a marking: it hands the batch to the
   * engine, which resolves each one strictly, refuses the ones it cannot
   * address, asks about the ones that argue with the spec, and regenerates only
   * the affected packages behind the isolation and instrumentation guardrails.
   * This method's job is the workspace scoping, the versioning, and translating
   * the answer.
   */
  async change(
    workspaceId: string,
    projectId: string,
    body: ApplyDesignChangeRequest,
  ): Promise<ApplyDesignChangeResponse> {
    await this.project(workspaceId, projectId);
    const spec = await this.currentSpec(workspaceId, projectId);
    const design = await this.currentDesign(workspaceId, projectId);
    const ref = this.refOf(design);

    if (!ref.workspace) {
      throw new ConflictException(
        "Generate a preview first — there is nothing to change yet.",
      );
    }

    const result = await this.engine.designChange({
      app_dir: ref.workspace as string,
      spec: spec.content as IntakeSpec,
      batch: {
        markings: (body.markings ?? []).map((m) => ({
          scio_id: m.scioId,
          scio_package: m.scioPackage ?? null,
          tag: m.tag ?? "",
          text: m.text ?? "",
          ancestor_id: m.ancestorId ?? null,
          ancestor_package: m.ancestorPackage ?? null,
          ancestor_distance: m.ancestorDistance ?? 0,
          note: m.note ?? "",
        })),
        prompt: body.prompt ?? "",
      },
      package_files: (ref.packageFiles as Record<string, string[]>) ?? {},
      // A directed change is the cheap, frequent interaction, and until now the
      // only one in the product with no ceiling of any kind. Flat rather than
      // derived from the estimate: the estimate prices a BUILD, and a change is
      // a different unit of work that nobody has quoted.
      budget_usd: DesignService.CHANGE_CEILING_USD,
      // Questions the user has already answered. They live on the frozen spec,
      // so the engine keeps deciding what a conflict is — this only tells it
      // which ones were settled in writing.
      allowances: allowancesOf(spec.assumptions),
    });

    const previewUrl = (ref.previewUrl as string) || null;
    const manifest =
      result.manifest ?? (ref.manifest as Record<string, unknown>) ?? null;

    // Only an applied change is a new version. A conflict changed nothing, so
    // recording one would put a version in the history that nobody can see the
    // difference of.
    await this.meter(workspaceId, projectId, "design_change", result.total_cost_usd ?? 0);

    let version: DesignVersion | null = design ? this.asDto(design) : null;
    if (result.applied) {
      version = await this.record(workspaceId, projectId, {
        ...ref,
        manifest,
        change: result.description,
        // Empty when the change landed but could not be committed: the version
        // is then readable and not returnable, and the window says which.
        gitSha: result.git_sha ?? "",
      });
    }

    return {
      applied: result.applied,
      conflicts: result.conflicts.map((c) => ({
        kind: c.kind,
        scioId: c.scio_id,
        note: c.note,
        specSays: c.spec_says,
        question: c.question,
      })),
      packages: result.packages.map((p) => ({
        package: p.package,
        editedFiles: p.edited_files,
        unchangedFiles: p.unchanged_files,
        isolated: p.isolated,
        accepted: p.accepted,
        rejection: p.rejection,
      })),
      skipped: result.unaddressable.map((u) => ({
        scioId: u.marking.scio_id,
        note: u.marking.note,
        error: u.error,
      })),
      previewUrl,
      manifest,
      designVersion: version,
      summary: this.summarise(result),
    };
  }

  private summarise(result: {
    applied: boolean;
    conflicts: Array<{ question: string }>;
    packages: Array<{
      package: string;
      edited_files: string[];
      unchanged_files: number;
      accepted: boolean;
      rejection: string;
    }>;
    unaddressable: unknown[];
  }): string {
    if (result.conflicts.length > 0) {
      return `Not applied — ${result.conflicts.length} thing(s) need your call.`;
    }
    if (result.packages.length === 0)
      return "Nothing to change — no marking could be addressed.";
    const lines = result.packages.map((p) =>
      p.accepted
        ? `${p.package}: changed ${p.edited_files.join(", ")} (${p.unchanged_files} other files unchanged)`
        : `${p.package}: not applied — ${p.rejection}`,
    );
    if (result.unaddressable.length > 0) {
      lines.push(
        `${result.unaddressable.length} marking(s) could not be addressed`,
      );
    }
    return lines.join("\n");
  }

  /**
   * Return to an earlier design version.
   *
   * The list is only worth having if you can go back to what is on it — that is
   * what makes "keep asking, you can undo it" true rather than a slogan. The
   * restore is a write like any other, so the engine re-verifies the restored
   * tree's instrumentation and refuses a version whose code and manifest have
   * drifted; that refusal is relayed as an answer, not an error.
   *
   * Going back is recorded as a NEW version rather than deleting the ones after
   * it. Changing your mind twice is normal, and a history that erases itself
   * cannot support the second change of mind.
   */
  async restore(
    workspaceId: string,
    projectId: string,
    versionId: string,
  ): Promise<RestoreDesignVersionResponse> {
    await this.project(workspaceId, projectId);
    const target = await this.client(workspaceId).designVersion.findFirst({
      where: { id: versionId, projectId },
    });
    if (!target) throw new NotFoundException("Design version not found");

    const targetRef = this.refOf(target);
    const current = await this.currentDesign(workspaceId, projectId);
    const currentRef = this.refOf(current);
    const gitSha = (targetRef.gitSha as string) || "";
    const workspace =
      (currentRef.workspace as string) || (targetRef.workspace as string) || "";

    if (!gitSha) {
      return {
        restored: false,
        previewUrl: (currentRef.previewUrl as string) || null,
        manifest: (currentRef.manifest as Record<string, unknown>) ?? null,
        designVersion: current ? this.asDto(current) : null,
        error:
          `Version ${target.number} was never committed, so there is nothing to return to. ` +
          "The change it describes is still in the versions after it.",
      };
    }
    if (!workspace) {
      throw new ConflictException(
        "Generate a preview first — there is nothing to restore into.",
      );
    }

    const result = await this.engine.designRestore({
      app_dir: workspace,
      git_sha: gitSha,
      package_files:
        (currentRef.packageFiles as Record<string, string[]>) ?? {},
    });

    if (!result.restored) {
      return {
        restored: false,
        previewUrl: (currentRef.previewUrl as string) || null,
        manifest: (currentRef.manifest as Record<string, unknown>) ?? null,
        designVersion: current ? this.asDto(current) : null,
        error: result.error || "That version could not be restored.",
      };
    }

    const version = await this.record(workspaceId, projectId, {
      ...currentRef,
      manifest:
        result.manifest ?? targetRef.manifest ?? currentRef.manifest ?? null,
      change: `returned to version ${target.number}`,
      gitSha: result.head || gitSha,
    });

    return {
      restored: true,
      previewUrl: (currentRef.previewUrl as string) || null,
      manifest: (result.manifest as Record<string, unknown>) ?? null,
      designVersion: version,
      error: "",
    };
  }

  async freeze(
    workspaceId: string,
    projectId: string,
    body: FreezeDesignRequest,
  ): Promise<DesignVersionResponse> {
    await this.project(workspaceId, projectId);
    const version = await this.record(workspaceId, projectId, {
      approved: true,
      ref: body.ref,
    });
    return { designVersion: version };
  }
}
