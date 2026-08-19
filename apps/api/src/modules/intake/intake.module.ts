import { Module } from "@nestjs/common";
import { DraftSpecController, IntakeController } from "./intake.controller";
import { IntakeService } from "./intake.service";

@Module({
  controllers: [IntakeController, DraftSpecController],
  providers: [IntakeService],
})
export class IntakeModule {}
