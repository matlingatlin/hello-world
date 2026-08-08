import { Body, Controller, Delete, Get, Param, Patch, Post } from "@nestjs/common";
import { ApiBearerAuth, ApiOperation, ApiTags } from "@nestjs/swagger";
import type {
  CreateProjectRequest,
  ProjectListResponse,
  ProjectResponse,
  UpdateProjectRequest,
} from "@scio/shared";
import { CurrentWorkspace } from "../../auth/auth-context";
import { ProjectService } from "./project.service";

@ApiTags("project")
@ApiBearerAuth()
@Controller("projects")
export class ProjectController {
  constructor(private readonly projects: ProjectService) {}

  @Get()
  @ApiOperation({ summary: "List projects in the workspace (stub)" })
  list(@CurrentWorkspace() workspaceId: string): Promise<ProjectListResponse> {
    return this.projects.list(workspaceId);
  }

  @Post()
  @ApiOperation({ summary: "Create a project (stub)" })
  create(
    @CurrentWorkspace() workspaceId: string,
    @Body() body: CreateProjectRequest,
  ): Promise<ProjectResponse> {
    return this.projects.create(workspaceId, body);
  }

  @Get(":id")
  @ApiOperation({ summary: "Get a project (stub)" })
  get(@CurrentWorkspace() workspaceId: string, @Param("id") id: string): Promise<ProjectResponse> {
    return this.projects.get(workspaceId, id);
  }

  @Patch(":id")
  @ApiOperation({ summary: "Update a project (stub)" })
  update(
    @CurrentWorkspace() workspaceId: string,
    @Param("id") id: string,
    @Body() body: UpdateProjectRequest,
  ): Promise<ProjectResponse> {
    return this.projects.update(workspaceId, id, body);
  }

  @Delete(":id")
  @ApiOperation({ summary: "Soft-delete a project (stub)" })
  remove(@CurrentWorkspace() workspaceId: string, @Param("id") id: string): Promise<void> {
    return this.projects.softDelete(workspaceId, id);
  }
}
