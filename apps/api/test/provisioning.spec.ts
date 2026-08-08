import { describe, expect, it, vi } from "vitest";
import { ProvisioningService } from "../src/auth/provisioning.service";
import type { PrismaService } from "../src/prisma/prisma.service";

describe("ProvisioningService", () => {
  const identity = { externalId: "clerk_abc", email: "alex@example.com" };

  it("returns the existing user without creating anything", async () => {
    const prisma = {
      user: {
        findUnique: vi.fn().mockResolvedValue({ id: "u1", workspaceId: "w1" }),
      },
      $transaction: vi.fn(),
    } as unknown as PrismaService;

    const result = await new ProvisioningService(prisma).getOrCreate(identity);
    expect(result).toEqual({ userId: "u1", workspaceId: "w1" });
    expect(prisma.$transaction).not.toHaveBeenCalled();
  });

  it("creates user + workspace in one transaction on first sight", async () => {
    const tx = {
      workspace: { create: vi.fn().mockResolvedValue({ id: "w-new" }) },
      user: { create: vi.fn().mockResolvedValue({ id: "u-new" }) },
    };
    const prisma = {
      user: { findUnique: vi.fn().mockResolvedValue(null) },
      $transaction: vi.fn((fn: (tx: unknown) => unknown) => fn(tx)),
    } as unknown as PrismaService;

    const result = await new ProvisioningService(prisma).getOrCreate(identity);
    expect(result).toEqual({ userId: "u-new", workspaceId: "w-new" });
    expect(tx.workspace.create).toHaveBeenCalledWith({
      data: { name: "alex@example.com" },
    });
    expect(tx.user.create).toHaveBeenCalledWith({
      data: {
        clerkUserId: "clerk_abc",
        email: "alex@example.com",
        workspaceId: "w-new",
        role: "owner",
      },
    });
  });
});
