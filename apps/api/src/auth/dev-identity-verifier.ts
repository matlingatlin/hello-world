import { Injectable, Logger, UnauthorizedException } from "@nestjs/common";
import type { ConfigService } from "@nestjs/config";
import type { IdentityVerifier, VerifiedIdentity } from "./identity-verifier";

/**
 * Dev-only identity (ADR-0008's other implementation).
 *
 * Clerk needs an account, a dashboard and two keys before anyone can see a
 * single screen — which meant the product had never been clicked through by a
 * human, only tested. This verifier removes that wall for local work: the
 * bearer token IS the identity.
 *
 *     Authorization: Bearer dev                 -> dev@scio.local
 *     Authorization: Bearer dev:ada@example.com -> ada@example.com
 *
 * The second form matters more than it looks: two tokens are two users with two
 * workspaces, so workspace scoping can be exercised by hand rather than only in
 * a test with a fake.
 *
 * It is bound only when SCIO_DEV_AUTH is set AND the process is not production —
 * see auth.module. Everything downstream (provisioning, scoping, the guard) is
 * the real thing; only the question "who is this" is answered differently.
 */

export const DEV_TOKEN_PREFIX = "dev";
export const DEFAULT_DEV_EMAIL = "dev@scio.local";

/** Whether this process should run on dev auth rather than Clerk. */
export function devAuthEnabled(env: Record<string, string | undefined>): boolean {
  const flag = (env.SCIO_DEV_AUTH ?? "").toLowerCase();
  if (!["1", "true", "yes"].includes(flag)) return false;
  if (env.NODE_ENV === "production") {
    // Refused rather than honoured: an accidental flag in a deployed
    // environment would accept any bearer token at all.
    throw new Error(
      "SCIO_DEV_AUTH is set but NODE_ENV=production. Dev auth accepts any token and must " +
        "never run in production — unset one of them.",
    );
  }
  return true;
}

@Injectable()
export class DevIdentityVerifier implements IdentityVerifier {
  private readonly logger = new Logger(DevIdentityVerifier.name);

  constructor(_config?: ConfigService) {
    this.logger.warn(
      "DEV AUTH IS ON — any 'dev' bearer token is accepted. Never in production.",
    );
  }

  async verify(token: string): Promise<VerifiedIdentity> {
    const [prefix, ...rest] = token.trim().split(":");
    if (prefix !== DEV_TOKEN_PREFIX) {
      // Still a real check: a stale Clerk token must fail loudly here rather
      // than silently signing someone in as the default dev user.
      throw new UnauthorizedException(
        `Dev auth expects a token of the form 'dev' or 'dev:<email>' (got '${prefix}')`,
      );
    }
    const email = rest.join(":").trim() || DEFAULT_DEV_EMAIL;
    return { externalId: `dev_${email}`, email };
  }
}
