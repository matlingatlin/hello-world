import { Injectable, UnauthorizedException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { createClerkClient, verifyToken } from "@clerk/backend";
import type { IdentityVerifier, VerifiedIdentity } from "./identity-verifier";

/**
 * Clerk implementation of IdentityVerifier (ADR-0008). The only place in the
 * backend that talks to Clerk directly.
 */
@Injectable()
export class ClerkIdentityVerifier implements IdentityVerifier {
  private readonly secretKey: string;
  private readonly client;

  constructor(config: ConfigService) {
    this.secretKey = config.get<string>("CLERK_SECRET_KEY") ?? "";
    this.client = createClerkClient({ secretKey: this.secretKey });
  }

  async verify(token: string): Promise<VerifiedIdentity> {
    if (!this.secretKey) {
      throw new UnauthorizedException("Auth is not configured (CLERK_SECRET_KEY missing)");
    }
    let sub: string;
    let claimEmail: string | undefined;
    try {
      const payload = await verifyToken(token, { secretKey: this.secretKey });
      sub = payload.sub;
      claimEmail = typeof payload.email === "string" ? payload.email : undefined;
    } catch {
      throw new UnauthorizedException("Invalid or expired session token");
    }
    // Session tokens don't always carry the email claim — fall back to the API.
    let email = claimEmail;
    if (!email) {
      const user = await this.client.users.getUser(sub);
      email =
        user.primaryEmailAddress?.emailAddress ?? user.emailAddresses[0]?.emailAddress ?? "";
    }
    return { externalId: sub, email };
  }
}
