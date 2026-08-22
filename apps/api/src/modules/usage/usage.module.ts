import { Module } from "@nestjs/common";
import { UsageController } from "./usage.controller";
import { UsageService } from "./usage.service";

@Module({
  controllers: [UsageController],
  providers: [UsageService],
  // Exported so the build path can ask, before starting work, whether this
  // workspace has any allowance left (the per-period ceiling).
  exports: [UsageService],
})
export class UsageModule {}
