import {
  CanActivate,
  ExecutionContext,
  Inject,
  Injectable,
  UnauthorizedException,
} from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { AUTH_CONTEXT_KEY } from "./auth-context";
import { IDENTITY_VERIFIER, type IdentityVerifier } from "./identity-verifier";
import { IS_PUBLIC_KEY } from "./public.decorator";
import { ProvisioningService } from "./provisioning.service";

/**
 * Global guard: verifies the bearer token via the swappable IdentityVerifier,
 * provisions user + workspace on first sight, and attaches the AuthContext
 * ({ userId, workspaceId }) that all workspace scoping flows from.
 */
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    @Inject(IDENTITY_VERIFIER) private readonly verifier: IdentityVerifier,
    private readonly provisioning: ProvisioningService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;

    const request = context.switchToHttp().getRequest();
    const header: string | undefined = request.headers?.authorization;
    if (!header || !header.startsWith("Bearer ")) {
      throw new UnauthorizedException("Missing bearer token");
    }
    const identity = await this.verifier.verify(header.slice("Bearer ".length));
    const provisioned = await this.provisioning.getOrCreate(identity);
    request[AUTH_CONTEXT_KEY] = {
      userId: provisioned.userId,
      workspaceId: provisioned.workspaceId,
      externalId: identity.externalId,
      email: identity.email,
    };
    return true;
  }
}
