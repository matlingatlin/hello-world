import { Module } from "@nestjs/common";
import { UsageModule } from "../usage/usage.module";
import { BuildController } from "./build.controller";
import { BuildService } from "./build.service";

@Module({
  // A build is the expensive thing, so it is the thing that has to ask whether
  // there is any allowance left.
  imports: [UsageModule],
  controllers: [BuildController],
  providers: [BuildService],
})
export class BuildModule {}
