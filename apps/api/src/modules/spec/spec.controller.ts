import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type {
  AmendSpecResponse,
  ApproveSpecResponse,
  SpecVersionListResponse,
} from "@scio/shared";
import { IsIn, IsOptional, IsString, MaxLength } from "class-validator";
import { CurrentWorkspace } from "../../auth/auth-context";
import { SpecService } from "./spec.service";

export class ApproveSpecDto {
  @IsOptional()
  @IsString()
  @MaxLength(20000)
  whole?: string;
}

/**
 * An amendment names the exact sentence it changes.
 *
 * Not an id, and not "the current conflict": the design window quotes the spec
 * back at the user when it asks, and what they answered has to be the thing
 * that gets recorded — otherwise a second conflict arriving in between would
 * silently be the one they allowed.
 */
export class AmendSpecDto {
  @IsIn(["non_goal", "auth", "access"])
  kind!: "non_goal" | "auth" | "access";

  @IsString()
  @MaxLength(2000)
  specSays!: string;

  @IsOptional()
  @IsString()
  @MaxLength(2000)
  note?: string;
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

  @Post("amend")
  @ApiOperation({ summary: "Change the approved spec because a marking argued with it" })
  amend(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: AmendSpecDto,
  ): Promise<AmendSpecResponse> {
    return this.specs.amend(workspaceId, projectId, body);
  }
}
