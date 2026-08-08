import { Injectable, NotImplementedException } from "@nestjs/common";
import type {
  DesignVersionListResponse,
  DesignVersionResponse,
  FreezeDesignRequest,
} from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/** Approved design contracts (Level 2). Scoped via project -> workspace_id. */
@Injectable()
export class DesignService {
  constructor(private readonly prisma: PrismaService) {}

  async list(projectId: string): Promise<DesignVersionListResponse> {
    // TODO(6.3): workspace-scoped listing.
    throw new NotImplementedException("design.list — phase 6.3");
  }

  async freeze(projectId: string, body: FreezeDesignRequest): Promise<DesignVersionResponse> {
    // TODO(6.3): freeze the approved design as a versioned contract.
    throw new NotImplementedException("design.freeze — phase 6.3");
  }
}
