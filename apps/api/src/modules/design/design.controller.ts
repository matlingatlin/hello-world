import { CurrentWorkspace } from "../../auth/auth-context";
import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type {
  DesignVersionListResponse,
  DesignVersionResponse,
  FreezeDesignRequest,
} from "@scio/shared";
import { DesignService } from "./design.service";

@ApiTags("design")
@Controller("projects/:projectId/design-versions")
export class DesignController {
  constructor(private readonly designs: DesignService) {}

  @Get()
  @ApiOperation({ summary: "List approved design versions (stub)" })
  list(@CurrentWorkspace() workspaceId: string, @Param("projectId") projectId: string): Promise<DesignVersionListResponse> {
    return this.designs.list(workspaceId, projectId);
  }

  @Post()
  @ApiOperation({ summary: "Freeze the approved design as a new version (stub)" })
  freeze(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: FreezeDesignRequest,
  ): Promise<DesignVersionResponse> {
    return this.designs.freeze(workspaceId, projectId, body);
  }
}
