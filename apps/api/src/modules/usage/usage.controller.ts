import { CurrentWorkspace } from "../../auth/auth-context";
import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { UsageListResponse } from "@scio/shared";
import { UsageService } from "./usage.service";

@ApiTags("usage")
@Controller("usage")
export class UsageController {
  constructor(private readonly usage: UsageService) {}

  @Get()
  @ApiOperation({ summary: "Workspace usage events, newest first" })
  list(@CurrentWorkspace() workspaceId: string): Promise<UsageListResponse> {
    return this.usage.list(workspaceId);
  }

  @Get("allowance")
  @ApiOperation({ summary: "What this workspace has spent this period, and its ceiling" })
  allowance(
    @CurrentWorkspace() workspaceId: string,
  ): Promise<{ spent: number; cap: number; room: boolean }> {
    return this.usage.allowance(workspaceId);
  }
}
