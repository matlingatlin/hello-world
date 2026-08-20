import { ConflictException, Injectable, Logger, NotFoundException } from "@nestjs/common";
import type {
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

  async list(workspaceId: string, projectId: string): Promise<BuildVersionListResponse> {
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
  async latest(workspaceId: string, projectId: string): Promise<LatestBuildResponse> {
    const project = await this.project(workspaceId, projectId);
    const builds = await this.client(workspaceId).buildVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const current =
      builds.find((b: { isCurrent: boolean }) => b.isCurrent) ?? builds[0] ?? null;

    const specs = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const spec = specs.find((s: { isCurrent: boolean }) => s.isCurrent) ?? specs[0];
    const frozen = (spec?.assumptions ?? {}) as { whole?: string; estimate?: unknown };
    const whole = frozen.whole ?? null;
    // The estimate the user approved AGAINST, frozen with the spec — not
    // whatever the draft says now. Comparing spend to a figure that has since
    // moved would be worse than showing no comparison at all.
    const estimate = (frozen.estimate ?? null) as LatestBuildResponse["estimate"];

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
      honestStatus: (current?.honestStatus ?? null) as LatestBuildResponse["honestStatus"],
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
  async run(
    workspaceId: string,
    projectId: string,
    emit: (event: string, data: Record<string, unknown>) => Promise<void> | void,
  ): Promise<void> {
    await this.project(workspaceId, projectId);

    const specVersions = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const current = specVersions.find((s: { isCurrent: boolean }) => s.isCurrent);
    if (!current) {
      throw new ConflictException("Approve a spec first — there is nothing frozen to build.");
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

    try {
      await this.engine.streamBuild(
        {
          spec: current.content as IntakeSpec,
          project_id: projectId,
          build_version: number,
        },
        async (event, data) => {
          if (event === "finished") finished = data as unknown as BuildFinished;
          if (event === "error") failure = String(data.message ?? "the build failed");
          await emit(event, data);
        },
      );
    } catch (err) {
      failure = (err as Error).message;
      await emit("error", { type: "engine_unavailable", message: failure });
    }

    if (finished) {
      await this.persist(workspaceId, projectId, current.id, number, finished);
      return;
    }

    // No finished event means no app: say so in the project's status rather than
    // leaving it "building" forever.
    this.logger.warn(`build for ${projectId} produced no result: ${failure ?? "unknown"}`);
    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { status: "error" },
    });
  }

  private async persist(
    workspaceId: string,
    projectId: string,
    specVersionId: string,
    number: number,
    finished: BuildFinished,
  ): Promise<void> {
    const client = this.client(workspaceId);
    const previous = await client.buildVersion.findMany({ where: { projectId } });
    for (const row of previous.filter((r: { isCurrent: boolean }) => r.isCurrent)) {
      await client.buildVersion.update({ where: { id: row.id }, data: { isCurrent: false } });
    }

    await client.buildVersion.create({
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
        isCurrent: true,
      },
    });

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
        this.logger.warn(`could not record usage for ${projectId}: ${(err as Error).message}`);
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
