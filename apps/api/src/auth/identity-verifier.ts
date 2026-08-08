/**
 * Swappable auth abstraction (ADR-0008). Everything in the app depends on this
 * interface — the concrete provider (Clerk today) is an implementation detail
 * and can be replaced (e.g. Entra External ID) without touching consumers.
 */

export interface VerifiedIdentity {
  /** The provider's stable user id (maps to user.clerk_user_id). */
  externalId: string;
  email: string;
}

export interface IdentityVerifier {
  /** Verifies a bearer token; throws on invalid/expired tokens. */
  verify(token: string): Promise<VerifiedIdentity>;
}

/** DI token — bind ClerkIdentityVerifier in prod, a fake in tests. */
export const IDENTITY_VERIFIER = Symbol("IDENTITY_VERIFIER");
