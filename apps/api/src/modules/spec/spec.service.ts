import { Injectable, NotImplementedException } from "@nestjs/common";
import type { FreezeSpecRequest, SpecVersionListResponse, SpecVersionResponse } from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/** Frozen spec/whole contracts. All queries scoped via project -> workspace_id. */
@Injectable()
export class SpecService {
  constructor(private readonly prisma: PrismaService) {}

  async list(workspaceId: string, projectId: string): Promise<SpecVersionListResponse> {
    // TODO(5): list versions for a project the caller's workspace owns.
    throw new NotImplementedException("spec.list — phase 5");
  }

  async freeze(workspaceId: string, projectId: string, body: FreezeSpecRequest): Promise<SpecVersionResponse> {
    // TODO(5): next number per project (unique project_id+number); mark is_current.
    throw new NotImplementedException("spec.freeze — phase 5");
  }
}
