import { CurrentWorkspace } from "../../auth/auth-context";
import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type {
  CreateDeploymentRequest,
  DeploymentListResponse,
  DeploymentResponse,
} from "@scio/shared";
import { DeploymentService } from "./deployment.service";

@ApiTags("deployment")
@Controller("projects/:projectId/deployments")
export class DeploymentController {
  constructor(private readonly deployments: DeploymentService) {}

  @Get()
  @ApiOperation({ summary: "List deployments (stub)" })
  list(@CurrentWorkspace() workspaceId: string, @Param("projectId") projectId: string): Promise<DeploymentListResponse> {
    return this.deployments.list(workspaceId, projectId);
  }

  @Post()
  @ApiOperation({ summary: "Publish a build version (stub)" })
  create(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: CreateDeploymentRequest,
  ): Promise<DeploymentResponse> {
    return this.deployments.create(workspaceId, projectId, body);
  }
}
