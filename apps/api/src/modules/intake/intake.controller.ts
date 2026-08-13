import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { IntakeStepResponse } from "@scio/shared";
import { IsNotEmpty, IsString, MaxLength } from "class-validator";
import { CurrentWorkspace } from "../../auth/auth-context";
import { IntakeService } from "./intake.service";

export class IntakeMessageDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(4000)
  text!: string;
}

@ApiTags("intake")
@Controller("projects/:projectId/intake")
export class IntakeController {
  constructor(private readonly intake: IntakeService) {}

  @Get()
  @ApiOperation({ summary: "The wizard conversation and working spec so far" })
  history(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
  ): Promise<IntakeStepResponse> {
    return this.intake.history(workspaceId, projectId);
  }

  @Post("message")
  @ApiOperation({
    summary: "One wizard turn: extract what was said, answer with the next question",
  })
  message(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: IntakeMessageDto,
  ): Promise<IntakeStepResponse> {
    return this.intake.step(workspaceId, projectId, body.text);
  }
}
