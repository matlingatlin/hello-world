import { IsIn, IsNotEmpty, IsOptional, IsString, MaxLength } from "class-validator";
import type { ProjectStatus, ProjectType } from "./entities";
import type { CreateProjectRequest, UpdateProjectRequest } from "./dtos";

export const PROJECT_TYPES: ProjectType[] = ["app", "website", "automation"];
export const PROJECT_STATUSES: ProjectStatus[] = ["draft", "building", "ready", "error"];

/** Body for POST /projects. MVP: type defaults to "app". */
export class CreateProjectDto implements CreateProjectRequest {
  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  name!: string;

  @IsOptional()
  @IsIn(PROJECT_TYPES)
  type: ProjectType = "app";
}

/** Body for PATCH /projects/:id. */
export class UpdateProjectDto implements UpdateProjectRequest {
  @IsOptional()
  @IsString()
  @IsNotEmpty()
  @MaxLength(200)
  name?: string;

  @IsOptional()
  @IsIn(PROJECT_STATUSES)
  status?: ProjectStatus;
}
