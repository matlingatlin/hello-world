import { Controller, Get } from "@nestjs/common";
import { ApiBearerAuth, ApiOperation, ApiTags } from "@nestjs/swagger";
import type { WorkspaceResponse } from "@scio/shared";
import { CurrentWorkspace } from "../../auth/auth-context";
import { WorkspaceService } from "./workspace.service";

@ApiTags("workspace")
@ApiBearerAuth()
@Controller("workspace")
export class WorkspaceController {
  constructor(private readonly workspaces: WorkspaceService) {}

  @Get()
  @ApiOperation({ summary: "Current workspace (stub)" })
  current(@CurrentWorkspace() workspaceId: string): Promise<WorkspaceResponse> {
    return this.workspaces.current(workspaceId);
  }
}
