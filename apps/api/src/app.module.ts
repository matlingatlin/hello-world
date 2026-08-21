import { Module } from "@nestjs/common";
import { APP_GUARD } from "@nestjs/core";
import { ThrottlerModule } from "@nestjs/throttler";
import { WorkspaceThrottlerGuard } from "./common/workspace-throttler.guard";
import { ConfigModule } from "@nestjs/config";
import { EngineModule } from "./engine/engine.module";
import { PrismaModule } from "./prisma/prisma.module";
import { HealthModule } from "./health/health.module";
import { IntakeModule } from "./modules/intake/intake.module";
import { AuthModule } from "./modules/auth/auth.module";
import { BuildModule } from "./modules/build/build.module";
import { DeploymentModule } from "./modules/deployment/deployment.module";
import { DesignModule } from "./modules/design/design.module";
import { NotificationModule } from "./modules/notification/notification.module";
import { ProjectModule } from "./modules/project/project.module";
import { ReferenceModule } from "./modules/reference/reference.module";
import { SpecModule } from "./modules/spec/spec.module";
import { StreamModule } from "./modules/stream/stream.module";
import { UsageModule } from "./modules/usage/usage.module";
import { UserModule } from "./modules/user/user.module";
import { WorkspaceModule } from "./modules/workspace/workspace.module";

@Module({
  imports: [
    // A ceiling on requests, because every expensive path — intake, a preview
    // build, a directed change — is one authenticated loop away from an
    // unbounded bill. Generous per minute: this is a bill guard and a crude DoS
    // guard, not a UX constraint.
    ThrottlerModule.forRoot([{ ttl: 60_000, limit: 120 }]),
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    EngineModule,
    HealthModule,
    AuthModule,
    WorkspaceModule,
    UserModule,
    ProjectModule,
    IntakeModule,
    SpecModule,
    DesignModule,
    BuildModule,
    DeploymentModule,
    ReferenceModule,
    UsageModule,
    NotificationModule,
    StreamModule,
  ],
  providers: [{ provide: APP_GUARD, useClass: WorkspaceThrottlerGuard }],
})
export class AppModule {}
