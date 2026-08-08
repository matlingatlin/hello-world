import { Injectable, NotImplementedException } from "@nestjs/common";
import type {
  CreateProjectRequest,
  ProjectListResponse,
  ProjectResponse,
  UpdateProjectRequest,
} from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/**
 * Project CRUD — business logic lands in phase 3.4.
 * Every query MUST filter on workspace_id (tenant isolation, ADR-0009);
 * list/get additionally exclude soft-deleted rows (deleted_at IS NULL).
 */
@Injectable()
export class ProjectService {
  constructor(private readonly prisma: PrismaService) {}

  async list(): Promise<ProjectListResponse> {
    // TODO(3.4): prisma.project.findMany({ where: { workspaceId, deletedAt: null } })
    throw new NotImplementedException("project.list — phase 3.4");
  }

  async get(id: string): Promise<ProjectResponse> {
    // TODO(3.4): scope by workspaceId; 404 when not in this workspace or soft-deleted.
    throw new NotImplementedException("project.get — phase 3.4");
  }

  async create(body: CreateProjectRequest): Promise<ProjectResponse> {
    // TODO(3.4): create under the caller's workspaceId only.
    throw new NotImplementedException("project.create — phase 3.4");
  }

  async update(id: string, body: UpdateProjectRequest): Promise<ProjectResponse> {
    // TODO(3.4): scope by workspaceId.
    throw new NotImplementedException("project.update — phase 3.4");
  }

  async softDelete(id: string): Promise<void> {
    // TODO(3.4): set deleted_at (never hard-delete); scope by workspaceId.
    throw new NotImplementedException("project.softDelete — phase 3.4");
  }
}
