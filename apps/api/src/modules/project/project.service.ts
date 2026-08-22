import { Injectable, Logger, NotFoundException } from "@nestjs/common";
import type { Prisma, Project as ProjectRow } from "@prisma/client";
import type {
  CreateProjectDto,
  Project,
  ProjectListResponse,
  ProjectResponse,
  UpdateProjectDto,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";
import { EngineClient } from "../../engine/engine.client";

function toProject(row: ProjectRow): Project {
  return {
    id: row.id,
    workspaceId: row.workspaceId,
    name: row.name,
    type: row.type,
    status: row.status,
    deletedAt: row.deletedAt ? row.deletedAt.toISOString() : null,
    createdAt: row.createdAt.toISOString(),
    updatedAt: row.updatedAt.toISOString(),
  };
}

/**
 * All access goes through WorkspaceScope.forWorkspace(workspaceId) — reads are
 * filtered by workspace_id and creates stamped with it, so a caller can never
 * see or touch another tenant's projects (missing → 404, not 403, to avoid
 * existence leaks).
 */
@Injectable()
export class ProjectService {
  private readonly logger = new Logger(ProjectService.name);

  constructor(
    private readonly scope: WorkspaceScope,
    private readonly engine: EngineClient,
  ) {}

  private client(workspaceId: string) {
    return this.scope.forWorkspace(workspaceId);
  }

  async list(workspaceId: string): Promise<ProjectListResponse> {
    const rows = await this.client(workspaceId).project.findMany({
      where: { deletedAt: null },
      orderBy: { createdAt: "desc" },
    });
    return { projects: rows.map(toProject) };
  }

  async get(workspaceId: string, id: string): Promise<ProjectResponse> {
    const row = await this.client(workspaceId).project.findFirst({
      where: { id, deletedAt: null },
    });
    if (!row) throw new NotFoundException("Project not found");
    return { project: toProject(row) };
  }

  async create(workspaceId: string, dto: CreateProjectDto): Promise<ProjectResponse> {
    const row = await this.client(workspaceId).project.create({
      // workspace_id is stamped by WorkspaceScope; status defaults to draft in the schema.
      data: { name: dto.name, type: dto.type ?? "app" } as Prisma.ProjectUncheckedCreateInput,
    });
    return { project: toProject(row) };
  }

  async update(workspaceId: string, id: string, dto: UpdateProjectDto): Promise<ProjectResponse> {
    await this.get(workspaceId, id); // scoped existence check → 404 across tenants
    const row = await this.client(workspaceId).project.update({
      where: { id },
      data: {
        ...(dto.name !== undefined && { name: dto.name }),
        ...(dto.status !== undefined && { status: dto.status }),
      },
    });
    return { project: toProject(row) };
  }

  /**
   * Delete a project: the row, the code, and the app that was serving it.
   *
   * It used to set a timestamp and stop. The workspace, its git history and its
   * screenshots stayed on disk indefinitely and the preview kept answering on
   * its port — so a "deleted" project was a hidden one, which is not what the
   * word means to the person who clicked it (B100).
   *
   * What is deliberately kept is the metering ledger. `usage_event` is a
   * billing record: it says what was spent from a workspace's allowance, and a
   * charge that disappears when its project does is not a ledger. Erasing those
   * belongs to account deletion, under a retention policy nobody has written
   * yet (ADR-0019).
   *
   * The row is marked deleted whatever happens to the files. A directory that
   * will not go must not keep the project alive — but it is logged rather than
   * swallowed, because the failure mode to avoid is telling someone their code
   * is gone while it sits on our disk.
   */
  async softDelete(workspaceId: string, id: string): Promise<void> {
    await this.get(workspaceId, id); // scoped existence check → 404 across tenants
    const row = await this.client(workspaceId).project.findFirst({ where: { id } });
    const previewUrl = (row?.previewUrl as string | null) ?? "";

    const outcome = await this.engine.discardWorkspace(id, previewUrl);
    if (outcome.problems.length > 0) {
      this.logger.warn(
        `project ${id} was deleted but its code is still on disk: ${outcome.problems.join("; ")}`,
      );
    }

    await this.client(workspaceId).project.update({
      where: { id },
      data: { deletedAt: new Date(), previewUrl: null },
    });
  }
}
