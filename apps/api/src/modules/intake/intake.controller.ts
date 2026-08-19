import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { CorrectSpecFieldResponse, IntakeStepResponse } from "@scio/shared";
import {
  ArrayMaxSize,
  IsArray,
  IsDefined,
  IsNotEmpty,
  IsOptional,
  IsString,
  MaxLength,
} from "class-validator";
import { CurrentWorkspace } from "../../auth/auth-context";
import { IntakeService } from "./intake.service";

export class IntakeMessageDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(4000)
  text!: string;
}

/**
 * One correction to the working spec.
 *
 * `value` is deliberately untyped here: a field holds a sentence, a list, or the
 * sensitivity object, and the engine is the one place that knows which — so it
 * validates the shape and names the field when it refuses. Validating it twice,
 * in two languages, is how the two definitions drift apart.
 */
export class CorrectSpecFieldDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(80)
  field!: string;

  @IsDefined()
  value!: string | string[] | Record<string, unknown>;

  @IsOptional()
  @IsArray()
  @ArrayMaxSize(20)
  @IsString({ each: true })
  clear?: string[];
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

/**
 * The working spec, edited directly.
 *
 * On its own path rather than under `intake` because it is not a wizard turn:
 * nothing is said, nothing is asked back, and no message is written. It is the
 * review screen correcting what the wizard got wrong.
 */
@ApiTags("intake")
@Controller("projects/:projectId/draft-spec")
export class DraftSpecController {
  constructor(private readonly intake: IntakeService) {}

  @Post("field")
  @ApiOperation({ summary: "Correct one field, and re-run the gate over the result" })
  correct(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: CorrectSpecFieldDto,
  ): Promise<CorrectSpecFieldResponse> {
    return this.intake.correct(workspaceId, projectId, body);
  }
}
