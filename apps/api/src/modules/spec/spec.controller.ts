import { CurrentWorkspace } from "../../auth/auth-context";
import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { FreezeSpecRequest, SpecVersionListResponse, SpecVersionResponse } from "@scio/shared";
import { SpecService } from "./spec.service";

@ApiTags("spec")
@Controller("projects/:projectId/spec-versions")
export class SpecController {
  constructor(private readonly specs: SpecService) {}

  @Get()
  @ApiOperation({ summary: "List frozen spec versions (stub)" })
  list(@CurrentWorkspace() workspaceId: string, @Param("projectId") projectId: string): Promise<SpecVersionListResponse> {
    return this.specs.list(workspaceId, projectId);
  }

  @Post()
  @ApiOperation({ summary: "Freeze the approved spec/whole as a new version (stub)" })
  freeze(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: FreezeSpecRequest,
  ): Promise<SpecVersionResponse> {
    return this.specs.freeze(workspaceId, projectId, body);
  }
}
