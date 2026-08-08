import { createParamDecorator, ExecutionContext } from "@nestjs/common";

/** Attached to every authenticated request by the auth guard. */
export interface AuthContext {
  userId: string;
  workspaceId: string;
  externalId: string;
  email: string;
}

export const AUTH_CONTEXT_KEY = "authContext";

function contextOf(ctx: ExecutionContext): AuthContext | undefined {
  return ctx.switchToHttp().getRequest()[AUTH_CONTEXT_KEY];
}

/** The authenticated local user id. */
export const CurrentUser = createParamDecorator(
  (_: unknown, ctx: ExecutionContext): string | undefined => contextOf(ctx)?.userId,
);

/** The caller's workspace id — the tenant boundary every query must scope by. */
export const CurrentWorkspace = createParamDecorator(
  (_: unknown, ctx: ExecutionContext): string | undefined => contextOf(ctx)?.workspaceId,
);
