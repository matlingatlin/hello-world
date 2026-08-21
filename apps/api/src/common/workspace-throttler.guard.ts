import { Injectable } from "@nestjs/common";
import { ThrottlerGuard } from "@nestjs/throttler";
import { AUTH_CONTEXT_KEY } from "../auth/auth-context";

/**
 * Rate limit per workspace, not per address.
 *
 * The default tracker is the client IP, which is the wrong unit here twice over:
 * everyone behind one office NAT shares a single bucket, and a workspace that
 * moves between networks gets a fresh one. The bill and the abuse both belong to
 * a workspace, so that is what the bucket should follow.
 *
 * Falls back to the address for unauthenticated routes (health, the Clerk
 * webhook), which is the right unit for those.
 */
@Injectable()
export class WorkspaceThrottlerGuard extends ThrottlerGuard {
  protected async getTracker(req: Record<string, unknown>): Promise<string> {
    const context = (req as Record<string, unknown>)[AUTH_CONTEXT_KEY] as
      | { workspaceId?: string }
      | undefined;
    const workspaceId = context?.workspaceId;
    if (workspaceId) return `workspace:${workspaceId}`;
    const ip = (req as { ip?: string }).ip;
    return `ip:${ip ?? "unknown"}`;
  }
}
