import { Body, Controller, Delete, Get, HttpCode, Param, Patch, Post } from "@nestjs/common";
import {
  ApiBearerAuth,
  ApiBody,
  ApiNoContentResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
} from "@nestjs/swagger";
import {
  CreateProjectDto,
  PROJECT_STATUSES,
  PROJECT_TYPES,
  UpdateProjectDto,
} from "@scio/shared";
import type { ProjectListResponse, ProjectResponse } from "@scio/shared";
import type { SchemaObject } from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";
import { CurrentWorkspace } from "../../auth/auth-context";
import { ProjectService } from "./project.service";

const projectSchema: SchemaObject = {
  type: "object",
  properties: {
    id: { type: "string", format: "uuid" },
    workspaceId: { type: "string", format: "uuid" },
    name: { type: "string" },
    type: { enum: [...PROJECT_TYPES] },
    status: { enum: [...PROJECT_STATUSES] },
    deletedAt: { type: "string", nullable: true },
    createdAt: { type: "string" },
    updatedAt: { type: "string" },
  },
};

@ApiTags("project")
@ApiBearerAuth()
@Controller("projects")
export class ProjectController {
  constructor(private readonly projects: ProjectService) {}

  @Get()
  @ApiOperation({ summary: "List the workspace's projects (newest first, excl. deleted)" })
  @ApiOkResponse({
    schema: { properties: { projects: { type: "array", items: projectSchema } } },
  })
  list(@CurrentWorkspace() workspaceId: string): Promise<ProjectListResponse> {
    return this.projects.list(workspaceId);
  }

  @Post()
  @ApiOperation({ summary: "Create a project (status starts as draft)" })
  @ApiBody({
    schema: {
      type: "object",
      required: ["name"],
      properties: {
        name: { type: "string", maxLength: 200 },
        type: { enum: [...PROJECT_TYPES], default: "app" },
      },
    },
  })
  @ApiOkResponse({ schema: { properties: { project: projectSchema } } })
  create(
    @CurrentWorkspace() workspaceId: string,
    @Body() body: CreateProjectDto,
  ): Promise<ProjectResponse> {
    return this.projects.create(workspaceId, body);
  }

  @Get(":id")
  @ApiOperation({ summary: "Get a project" })
  @ApiOkResponse({ schema: { properties: { project: projectSchema } } })
  @ApiNotFoundResponse({ description: "Missing, deleted, or another workspace's project" })
  get(@CurrentWorkspace() workspaceId: string, @Param("id") id: string): Promise<ProjectResponse> {
    return this.projects.get(workspaceId, id);
  }

  @Patch(":id")
  @ApiOperation({ summary: "Update name/status" })
  @ApiBody({
    schema: {
      type: "object",
      properties: {
        name: { type: "string", maxLength: 200 },
        status: { enum: [...PROJECT_STATUSES] },
      },
    },
  })
  @ApiOkResponse({ schema: { properties: { project: projectSchema } } })
  @ApiNotFoundResponse({ description: "Missing, deleted, or another workspace's project" })
  update(
    @CurrentWorkspace() workspaceId: string,
    @Param("id") id: string,
    @Body() body: UpdateProjectDto,
  ): Promise<ProjectResponse> {
    return this.projects.update(workspaceId, id, body);
  }

  @Delete(":id")
  @HttpCode(204)
  @ApiOperation({ summary: "Soft-delete a project (sets deleted_at; history preserved)" })
  @ApiNoContentResponse({ description: "Deleted" })
  @ApiNotFoundResponse({ description: "Missing, deleted, or another workspace's project" })
  remove(@CurrentWorkspace() workspaceId: string, @Param("id") id: string): Promise<void> {
    return this.projects.softDelete(workspaceId, id);
  }
}
