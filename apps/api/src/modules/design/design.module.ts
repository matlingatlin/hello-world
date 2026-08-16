import { Module } from "@nestjs/common";
import { DesignController, DesignVersionController } from "./design.controller";
import { DesignService } from "./design.service";

@Module({
  controllers: [DesignController, DesignVersionController],
  providers: [DesignService],
})
export class DesignModule {}
