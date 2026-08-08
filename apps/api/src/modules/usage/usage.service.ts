import { Injectable, NotImplementedException } from "@nestjs/common";
import type { UsageListResponse } from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/** Metering (4.5). Billing tables themselves are deferred to Phase 12. */
@Injectable()
export class UsageService {
  constructor(private readonly prisma: PrismaService) {}

  async list(): Promise<UsageListResponse> {
    // TODO(4.5): workspace-scoped usage events for the caller's workspace only.
    throw new NotImplementedException("usage.list — phase 4.5");
  }
}
