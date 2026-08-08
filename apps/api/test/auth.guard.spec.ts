import { UnauthorizedException } from "@nestjs/common";
import type { ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { describe, expect, it, vi } from "vitest";
import { AuthGuard } from "../src/auth/auth.guard";
import { AUTH_CONTEXT_KEY } from "../src/auth/auth-context";
import type { IdentityVerifier } from "../src/auth/identity-verifier";
import type { ProvisioningService } from "../src/auth/provisioning.service";

const fakeVerifier: IdentityVerifier = {
  async verify(token: string) {
    if (token !== "valid-token") throw new UnauthorizedException("bad token");
    return { externalId: "clerk_abc", email: "alex@example.com" };
  },
};

const fakeProvisioning = {
  getOrCreate: vi.fn().mockResolvedValue({ userId: "u1", workspaceId: "w1" }),
} as unknown as ProvisioningService;

function contextFor(request: Record<string, unknown>, isPublic = false): ExecutionContext {
  return {
    getHandler: () => ({}),
    getClass: () => ({}),
    switchToHttp: () => ({ getRequest: () => request }),
    __isPublic: isPublic,
  } as unknown as ExecutionContext;
}

function guardWith(isPublic: boolean): AuthGuard {
  const reflector = {
    getAllAndOverride: () => isPublic,
  } as unknown as Reflector;
  return new AuthGuard(reflector, fakeVerifier, fakeProvisioning);
}

describe("AuthGuard", () => {
  it("rejects a request without a bearer token (401)", async () => {
    await expect(guardWith(false).canActivate(contextFor({ headers: {} }))).rejects.toThrow(
      UnauthorizedException,
    );
  });

  it("rejects an invalid token (401)", async () => {
    const req = { headers: { authorization: "Bearer wrong" } };
    await expect(guardWith(false).canActivate(contextFor(req))).rejects.toThrow(
      UnauthorizedException,
    );
  });

  it("accepts a valid identity, provisions, and attaches the auth context", async () => {
    const req: Record<string, any> = { headers: { authorization: "Bearer valid-token" } };
    await expect(guardWith(false).canActivate(contextFor(req))).resolves.toBe(true);
    expect(fakeProvisioning.getOrCreate).toHaveBeenCalledWith({
      externalId: "clerk_abc",
      email: "alex@example.com",
    });
    expect(req[AUTH_CONTEXT_KEY]).toEqual({
      userId: "u1",
      workspaceId: "w1",
      externalId: "clerk_abc",
      email: "alex@example.com",
    });
  });

  it("lets @Public() routes through without a token", async () => {
    await expect(guardWith(true).canActivate(contextFor({ headers: {} }))).resolves.toBe(true);
  });
});
