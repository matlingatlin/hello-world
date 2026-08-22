import {
  ConflictException,
  Injectable,
  Logger,
  NotFoundException,
} from "@nestjs/common";
import type {
  BuildEventName,
  BuildFinished,
  BuildVersionListResponse,
  IntakeSpec,
  LatestBuildResponse,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";
import { EngineClient } from "../../engine/engine.client";

/**
 * The build: a frozen spec in, a running app out.
 *
 * The stream is relayed rather than collected. A build takes minutes, and the
 * build view's promise — real per-part progress, not a fake bar — only holds if
 * events reach the browser as parts actually finish.
 *
 * Persistence happens at the end, when the engine reports a git_sha: a
 * build_version is the pointer to a commit, so writing one before the commit
 * exists would create a version nobody can restore. Status moves building ->
 * ready (or error) so the projects list is honest even if the user closed the tab.
 */
@Injectable()
export class BuildService {
  private readonly logger = new Logger(BuildService.name);

  constructor(
    private readonly scope: WorkspaceScope,
    private readonly engine: EngineClient,
  ) {}

  private client(workspaceId: string) {
    return this.scope.forWorkspace(workspaceId);
  }

  private async project(workspaceId: string, projectId: string) {
    const row = await this.client(workspaceId).project.findFirst({
      where: { id: projectId, deletedAt: null },
    });
    if (!row) throw new NotFoundException("Project not found");
    return row;
  }

  async list(
    workspaceId: string,
    projectId: string,
  ): Promise<BuildVersionListResponse> {
    await this.project(workspaceId, projectId);
    const rows = await this.client(workspaceId).buildVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    return {
      buildVersions: rows.map((row: Record<string, unknown>) => ({
        id: row.id as string,
        projectId: row.projectId as string,
        number: row.number as number,
        description: row.description as string,
        gitSha: row.gitSha as string,
        honestStatus: row.honestStatus as never,
        specVersionId: row.specVersionId as string,
        designVersionId: (row.designVersionId ?? null) as string | null,
        isCurrent: row.isCurrent as boolean,
        createdAt: new Date(row.createdAt as string).toISOString(),
      })),
    };
  }

  /**
   * What the reveal shows, read back from storage.
   *
   * Re-read rather than carried through the browser: a project opened months
   * later must show the same honest status it showed the day it was built.
   */
  async latest(
    workspaceId: string,
    projectId: string,
  ): Promise<LatestBuildResponse> {
    const project = await this.project(workspaceId, projectId);
    const builds = await this.client(workspaceId).buildVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const current =
      builds.find((b: { isCurrent: boolean }) => b.isCurrent) ??
      builds[0] ??
      null;

    const specs = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const spec =
      specs.find((s: { isCurrent: boolean }) => s.isCurrent) ?? specs[0];
    const frozen = (spec?.assumptions ?? {}) as {
      whole?: string;
      estimate?: unknown;
    };
    const whole = frozen.whole ?? null;
    // The estimate the user approved AGAINST, frozen with the spec — not
    // whatever the draft says now. Comparing spend to a figure that has since
    // moved would be worse than showing no comparison at all.
    const estimate = (frozen.estimate ??
      null) as LatestBuildResponse["estimate"];

    // What the build actually cost, read back from the metering record rather
    // than recomputed. The estimate on the review screen says what a build
    // SHOULD cost; until now nothing anywhere said what it did.
    const metered = await this.client(workspaceId).usageEvent.findMany({
      where: { projectId, kind: "generation" },
      orderBy: { createdAt: "desc" },
    });
    const spend = metered[0] ?? null;

    return {
      buildVersion: current
        ? {
            id: current.id,
            number: current.number,
            description: current.description,
            gitSha: current.gitSha,
            isCurrent: current.isCurrent,
            createdAt: new Date(current.createdAt).toISOString(),
            costUsd: current.costUsd === null ? null : Number(current.costUsd),
            tokens: current.tokens ?? null,
          }
        : null,
      previewUrl: (project.previewUrl ?? null) as string | null,
      projectStatus: project.status as string,
      honestStatus: (current?.honestStatus ??
        null) as LatestBuildResponse["honestStatus"],
      whole,
      estimate,
      spend: spend
        ? {
            costUsd: Number(spend.cost),
            tokens: Number(spend.amount),
            model: (spend.model as string) ?? "",
            at: new Date(spend.createdAt).toISOString(),
          }
        : null,
    };
  }

  /**
   * Run a build, handing each event to `emit` as it arrives.
   *
   * `emit` is how the controller writes SSE to the browser; the service stays
   * ignorant of HTTP so the same path can later be driven by a queue worker for
   * builds the user walked away from.
   */
  /**
   * How long a build may hold the project before the lock is assumed stale.
   *
   * Longer than any build we have measured (the slowest real one took 46
   * minutes). A crashed engine must not lock a project forever, and a lock that
   * needs a human to clear is a lock nobody will clear.
   */
  private static readonly BUILD_LOCK_MS = 90 * 60 * 1000;

  /**
   * One build at a time, per project.
   *
   * `status` has said "building" since the first version and nothing read it.
   * Two builds are not merely wasteful: the engine keys its workspace by
   * project id and prepares it `fresh`, so the second build DELETES the first
   * one's files mid-flight, and both spend money. The trigger is not exotic —
   * it is pressing Build again when the stream looks dead, which is exactly
   * what a dropped connection invites.
   */
  /**
   * Called by the controller BEFORE the stream is opened.
   *
   * Once headers are sent a refusal can only be an event inside the stream,
   * which is the right shape for a build that fails half-way and the wrong one
   * for a build that never should have started: a caller that is not a browser
   * deserves a 409.
   */
  async ensureCanStart(workspaceId: string, projectId: string): Promise<void> {
    this.refuseIfAlreadyBuilding(await this.project(workspaceId, projectId));
  }

  private refuseIfAlreadyBuilding(project: { status: string; updatedAt: Date }): void {
    if (project.status !== "building") return;
    const held = Date.now() - new Date(project.updatedAt).getTime();
    if (held > BuildService.BUILD_LOCK_MS) {
      this.logger.warn(
        `project lock held for ${Math.round(held / 60000)} minutes — assuming a crashed build and taking it`,
      );
      return;
    }
    throw new ConflictException(
      "A build for this project is already running. Open it rather than starting a second one — " +
        "two builds share one workspace, and the second would delete the first one's files.",
    );
  }

  /**
   * What this build is allowed to spend.
   *
   * The high end of the estimate the user approved against — frozen into the
   * spec version at approval, so it is the figure that was on screen — with a
   * margin, because an estimate that stops a build the moment it is 1c over is
   * worse than no ceiling at all. A spec with no estimate gets none: a ceiling
   * invented here would be a number nobody agreed to.
   */
  private static readonly CEILING_MARGIN = 1.5;

  private ceilingFor(spec: { assumptions: unknown }): number | undefined {
    const frozen = (spec.assumptions ?? {}) as { estimate?: { cost_usd?: { high?: unknown } } };
    const high = Number(frozen.estimate?.cost_usd?.high);
    if (!Number.isFinite(high) || high <= 0) return undefined;
    return Number((high * BuildService.CEILING_MARGIN).toFixed(2));
  }

  async run(
    workspaceId: string,
    projectId: string,
    emit: (
      event: BuildEventName,
      data: Record<string, unknown>,
    ) => Promise<void> | void,
  ): Promise<void> {
    const project = await this.project(workspaceId, projectId);
    this.refuseIfAlreadyBuilding(project);

    const specVersions = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const current = specVersions.find(
      (s: { isCurrent: boolean }) => s.isCurrent,
    );
    if (!current) {
      throw new ConflictException(
        "Approve a spec first — there is nothing frozen to build.",
      );
    }

    const builds = await this.client(workspaceId).buildVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const number = (builds[0]?.number ?? 0) + 1;

    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { status: "building" },
    });

    let finished: BuildFinished | null = null;
    let failure: string | null = null;

    const relay = async (event: string, data: Record<string, unknown>) => {
      // The engine's frame names arrive as strings off the wire; the union is
      // what everything after this point is entitled to assume (B089).
      const name = event as BuildEventName;
      if (name === "finished") finished = data as unknown as BuildFinished;
      if (name === "error") failure = String(data.message ?? "the build failed");
      await emit(name, data);
    };

    // Did a design session already produce this app? Then that app IS the
    // build. Rebuilding it from the spec would regenerate every file the user
    // spent the session shaping — and, on the way, delete the workspace the
    // design history points at (B070).
    const design = await this.designToPromote(workspaceId, projectId);

    try {
      if (design) {
        await this.engine.promoteBuild(
          {
            app_dir: design.workspace,
            project_id: projectId,
            build_version: number,
            budget_usd: this.ceilingFor(current),
          },
          relay,
        );
      } else {
        await this.engine.streamBuild(
          {
            spec: current.content as IntakeSpec,
            project_id: projectId,
            build_version: number,
            budget_usd: this.ceilingFor(current),
          },
          relay,
        );
      }
    } catch (err) {
      failure = (err as Error).message;
      await emit("error", { type: "engine_unavailable", message: failure });
    }

    if (finished) {
      await this.persist(workspaceId, projectId, current.id, number, finished, {
        designVersionId: design?.id ?? null,
      });
      return;
    }

    // No finished event means no app: say so in the project's status rather than
    // leaving it "building" forever.
    this.logger.warn(
      `build for ${projectId} produced no result: ${failure ?? "unknown"}`,
    );
    // And say so in the stream. Without this the engine hanging up quietly
    // closed a 200 that had reported nothing but progress, which reads to a
    // browser exactly like a build that is still going — forever.
    if (!failure) {
      await emit("error", {
        type: "no_result",
        message: "The engine stopped without producing an app.",
      });
    }
    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { status: "error" },
    });
  }

  /**
   * The design version this project would be delivered from, if any.
   *
   * `null` when the user never opened the design window — they went straight
   * from the spec to "build it", so there is nothing to promote and the build
   * generates the app for the first time.
   */
  private async designToPromote(
    workspaceId: string,
    projectId: string,
  ): Promise<{ id: string; workspace: string } | null> {
    const row = await this.client(workspaceId).designVersion.findFirst({
      where: { projectId, isCurrent: true },
    });
    if (!row) return null;
    let workspace = "";
    try {
      workspace = String(
        (JSON.parse(row.ref as string) as { workspace?: unknown }).workspace ?? "",
      );
    } catch {
      // A ref we cannot read is not a workspace we can deliver. Fall through to
      // a full build rather than guessing at a path.
      return null;
    }
    return workspace ? { id: row.id as string, workspace } : null;
  }

  private async persist(
    workspaceId: string,
    projectId: string,
    specVersionId: string,
    number: number,
    finished: BuildFinished,
    links: { designVersionId: string | null },
  ): Promise<void> {
    const client = this.client(workspaceId);
    // One transaction, not two writes with a gap — see spec.service.approve.
    // Migration 0006 adds a partial unique index so the database refuses a
    // second current row too.
    await client.$transaction([
      client.buildVersion.updateMany({
        where: { projectId, isCurrent: true },
        data: { isCurrent: false },
      }),
      client.buildVersion.create({
        data: {
          projectId,
          number,
          description: finished.summary.split("\n")[0] ?? `Build ${number}`,
          gitSha: finished.git_sha,
          // The honest status is stored whole: what worked, what needs a look and
          // what was never built are all part of the record, not just the good news.
          honestStatus: {
            works: finished.works,
            summary: finished.summary,
            working: finished.parts_working,
            needs_look: finished.parts_needing_a_look,
            blocked: finished.parts_blocked,
            failed: finished.parts_failed,
            remainders: finished.remainders,
            standin: finished.standin,
          },
          // The build's own provenance. usage_event below is the metering ledger
          // for a workspace; this is what one build cost, readable from the build.
          costUsd: finished.total_cost_usd || null,
          tokens: finished.total_tokens || null,
          specVersionId,
          // Which design the delivered app came from, when it came from one:
          // without it the build's provenance stops at the spec, and the app on
          // disk is not the app the spec describes.
          designVersionId: links.designVersionId,
          isCurrent: true,
        },
      }),
    ]);

    // The metering record. `usage_event` has existed since ADR-0009 and nothing
    // had ever written to it: the engine computed `total_cost_usd`, the api
    // passed it through to the browser, and it was dropped there — so the
    // product could predict a cost and never say what it spent.
    //
    // Written after the build_version and never allowed to fail the build: a
    // delivered app must not be undone by a bookkeeping error.
    if (finished.total_cost_usd > 0 || (finished.total_tokens ?? 0) > 0) {
      try {
        await client.usageEvent.create({
          data: {
            // Also stamped by the scoped client (auth/workspace-scope); named
            // here because Prisma's generated types require it.
            workspaceId,
            projectId,
            kind: "generation",
            model: finished.model ?? null,
            // Tokens, not "one build": a cost with no quantity behind it cannot
            // be audited or re-priced when the rate card changes.
            amount: finished.total_tokens ?? 0,
            cost: finished.total_cost_usd,
          },
        });
      } catch (err) {
        this.logger.warn(
          `could not record usage for ${projectId}: ${(err as Error).message}`,
        );
      }
    }

    await client.project.update({
      where: { id: projectId },
      data: {
        // "ready" means there is something to look at, not that everything
        // passed — the honest status carries that, and the reveal shows it.
        status: "ready",
        previewUrl: finished.app_url || null,
      },
    });
  }
}
