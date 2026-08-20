import { Injectable, NotImplementedException } from "@nestjs/common";
import type { WorkspaceResponse } from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

@Injectable()
export class WorkspaceService {
  constructor(private readonly prisma: PrismaService) {}

  async current(workspaceId: string): Promise<WorkspaceResponse> {
    // TODO(3.4): return the caller's workspace via WorkspaceScope.forWorkspace(workspaceId).
    throw new NotImplementedException("workspace.current — phase 3.4");
  }
}
