import { Injectable } from "@nestjs/common";
import type { AuthStatusResponse } from "@scio/shared";

/**
 * STUB — real Clerk integration is phase 3.3 (ADR-0008).
 * Will verify Clerk JWTs, resolve the user + workspace, and expose a guard
 * that enforces workspace scoping on every request.
 */
@Injectable()
export class AuthService {
  status(): AuthStatusResponse {
    // TODO(3.3): verify Clerk session JWT and return the real user id.
    return { authenticated: false, userId: null };
  }
}
