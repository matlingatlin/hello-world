import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type {
  CreateReferenceAssetRequest,
  ReferenceAssetListResponse,
  ReferenceAssetResponse,
} from "@scio/shared";
import { ReferenceService } from "./reference.service";

@ApiTags("reference")
@Controller("projects/:projectId/references")
export class ReferenceController {
  constructor(private readonly references: ReferenceService) {}

  @Get()
  @ApiOperation({ summary: "List tagged reference assets (stub)" })
  list(@Param("projectId") projectId: string): Promise<ReferenceAssetListResponse> {
    return this.references.list(projectId);
  }

  @Post()
  @ApiOperation({ summary: "Register a tagged reference upload (stub)" })
  create(
    @Param("projectId") projectId: string,
    @Body() body: CreateReferenceAssetRequest,
  ): Promise<ReferenceAssetResponse> {
    return this.references.create(projectId, body);
  }
}
