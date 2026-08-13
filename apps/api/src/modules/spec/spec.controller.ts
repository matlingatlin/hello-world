import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { ApproveSpecResponse, SpecVersionListResponse } from "@scio/shared";
import { IsOptional, IsString, MaxLength } from "class-validator";
import { CurrentWorkspace } from "../../auth/auth-context";
import { SpecService } from "./spec.service";

export class ApproveSpecDto {
  @IsOptional()
  @IsString()
  @MaxLength(20000)
  whole?: string;
}

@ApiTags("spec")
@Controller("projects/:projectId/spec")
export class SpecController {
  constructor(private readonly specs: SpecService) {}

  @Get("versions")
  @ApiOperation({ summary: "List frozen spec versions, newest first" })
  list(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
  ): Promise<SpecVersionListResponse> {
    return this.specs.list(workspaceId, projectId);
  }

  @Post("approve")
  @ApiOperation({ summary: "Freeze the working spec as the current spec version" })
  approve(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: ApproveSpecDto,
  ): Promise<ApproveSpecResponse> {
    return this.specs.approve(workspaceId, projectId, body);
  }
}
