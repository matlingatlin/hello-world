import { Global, Module } from "@nestjs/common";
import { APP_GUARD } from "@nestjs/core";
import { AuthGuard } from "../../auth/auth.guard";
import { ClerkIdentityVerifier } from "../../auth/clerk-identity-verifier";
import { IDENTITY_VERIFIER } from "../../auth/identity-verifier";
import { ProvisioningService } from "../../auth/provisioning.service";
import { ClerkWebhookController } from "../../auth/webhook.controller";
import { WorkspaceScope } from "../../auth/workspace-scope";
import { AuthController } from "./auth.controller";

@Global()
@Module({
  controllers: [AuthController, ClerkWebhookController],
  providers: [
    ProvisioningService,
    WorkspaceScope,
    { provide: IDENTITY_VERIFIER, useClass: ClerkIdentityVerifier },
    { provide: APP_GUARD, useClass: AuthGuard },
  ],
  exports: [ProvisioningService, WorkspaceScope, IDENTITY_VERIFIER],
})
export class AuthModule {}
