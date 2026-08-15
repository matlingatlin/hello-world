import { Global, Module } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { APP_GUARD } from "@nestjs/core";
import { AuthGuard } from "../../auth/auth.guard";
import { ClerkIdentityVerifier } from "../../auth/clerk-identity-verifier";
import { DevIdentityVerifier, devAuthEnabled } from "../../auth/dev-identity-verifier";
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
    {
      // Which implementation of ADR-0008's IdentityVerifier this process runs.
      // Clerk unless SCIO_DEV_AUTH says otherwise, and never dev auth in
      // production — devAuthEnabled throws rather than allowing that.
      provide: IDENTITY_VERIFIER,
      useFactory: (config: ConfigService) =>
        devAuthEnabled(process.env)
          ? new DevIdentityVerifier(config)
          : new ClerkIdentityVerifier(config),
      inject: [ConfigService],
    },
    { provide: APP_GUARD, useClass: AuthGuard },
  ],
  exports: [ProvisioningService, WorkspaceScope, IDENTITY_VERIFIER],
})
export class AuthModule {}
