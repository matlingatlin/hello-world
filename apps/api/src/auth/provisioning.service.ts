import { Injectable } from "@nestjs/common";
import type { VerifiedIdentity } from "./identity-verifier";
import { PrismaService } from "../prisma/prisma.service";

export interface ProvisionedIdentity {
  userId: string;
  workspaceId: string;
}

/**
 * Get-or-create provisioning (ADR-0009): resolves the local user from the
 * provider identity; on first authenticated request creates the user AND their
 * workspace (MVP: one per user) in a single transaction.
 */
@Injectable()
export class ProvisioningService {
  constructor(private readonly prisma: PrismaService) {}

  async getOrCreate(identity: VerifiedIdentity): Promise<ProvisionedIdentity> {
    const existing = await this.prisma.user.findUnique({
      where: { clerkUserId: identity.externalId },
    });
    if (existing) {
      return { userId: existing.id, workspaceId: existing.workspaceId };
    }
    return this.prisma.$transaction(async (tx) => {
      const workspace = await tx.workspace.create({
        data: { name: identity.email || "My workspace" },
      });
      const user = await tx.user.create({
        data: {
          clerkUserId: identity.externalId,
          email: identity.email,
          workspaceId: workspace.id,
          role: "owner",
        },
      });
      return { userId: user.id, workspaceId: workspace.id };
    });
  }
}
