import { Injectable, NotFoundException } from "@nestjs/common";
import type { Prisma, Project as ProjectRow } from "@prisma/client";
import type {
  CreateProjectDto,
  Project,
  ProjectListResponse,
  ProjectResponse,
  UpdateProjectDto,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";

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
  constructor(private readonly scope: WorkspaceScope) {}

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

  async softDelete(workspaceId: string, id: string): Promise<void> {
    await this.get(workspaceId, id); // scoped existence check → 404 across tenants
    await this.client(workspaceId).project.update({
      where: { id },
      data: { deletedAt: new Date() },
    });
  }
}
