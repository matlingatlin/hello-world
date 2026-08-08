import { Injectable, NotImplementedException } from "@nestjs/common";
import type {
  CreateProjectRequest,
  ProjectListResponse,
  ProjectResponse,
  UpdateProjectRequest,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";

/**
 * Project CRUD — business logic lands in phase 3.4.
 * All queries go through WorkspaceScope.forWorkspace(workspaceId) so tenant
 * isolation is enforced structurally; list/get additionally exclude
 * soft-deleted rows (deleted_at IS NULL).
 */
@Injectable()
export class ProjectService {
  constructor(private readonly scope: WorkspaceScope) {}

  async list(workspaceId: string): Promise<ProjectListResponse> {
    // TODO(3.4): this.scope.forWorkspace(workspaceId).project.findMany({ where: { deletedAt: null } })
    throw new NotImplementedException("project.list — phase 3.4");
  }

  async get(workspaceId: string, id: string): Promise<ProjectResponse> {
    // TODO(3.4): scoped findFirst; 404 when not in this workspace or soft-deleted.
    throw new NotImplementedException("project.get — phase 3.4");
  }

  async create(workspaceId: string, body: CreateProjectRequest): Promise<ProjectResponse> {
    // TODO(3.4): scoped create (workspaceId stamped by the scope helper).
    throw new NotImplementedException("project.create — phase 3.4");
  }

  async update(
    workspaceId: string,
    id: string,
    body: UpdateProjectRequest,
  ): Promise<ProjectResponse> {
    // TODO(3.4): scoped update.
    throw new NotImplementedException("project.update — phase 3.4");
  }

  async softDelete(workspaceId: string, id: string): Promise<void> {
    // TODO(3.4): scoped update setting deleted_at (never hard-delete).
    throw new NotImplementedException("project.softDelete — phase 3.4");
  }
}
