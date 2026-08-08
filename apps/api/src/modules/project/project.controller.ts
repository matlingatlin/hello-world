import { Body, Controller, Delete, Get, Param, Patch, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type {
  CreateProjectRequest,
  ProjectListResponse,
  ProjectResponse,
  UpdateProjectRequest,
} from "@scio/shared";
import { ProjectService } from "./project.service";

@ApiTags("project")
@Controller("projects")
export class ProjectController {
  constructor(private readonly projects: ProjectService) {}

  @Get()
  @ApiOperation({ summary: "List projects in the workspace (stub)" })
  list(): Promise<ProjectListResponse> {
    return this.projects.list();
  }

  @Post()
  @ApiOperation({ summary: "Create a project (stub)" })
  create(@Body() body: CreateProjectRequest): Promise<ProjectResponse> {
    return this.projects.create(body);
  }

  @Get(":id")
  @ApiOperation({ summary: "Get a project (stub)" })
  get(@Param("id") id: string): Promise<ProjectResponse> {
    return this.projects.get(id);
  }

  @Patch(":id")
  @ApiOperation({ summary: "Update a project (stub)" })
  update(@Param("id") id: string, @Body() body: UpdateProjectRequest): Promise<ProjectResponse> {
    return this.projects.update(id, body);
  }

  @Delete(":id")
  @ApiOperation({ summary: "Soft-delete a project (stub)" })
  remove(@Param("id") id: string): Promise<void> {
    return this.projects.softDelete(id);
  }
}
