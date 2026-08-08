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
  @ApiOperation({ summary: "Workspace usage events (stub)" })
  list(@CurrentWorkspace() workspaceId: string): Promise<UsageListResponse> {
    return this.usage.list(workspaceId);
  }
}
