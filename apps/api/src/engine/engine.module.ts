import { Global, Module } from "@nestjs/common";
import { EngineClient } from "./engine.client";

/** Global: several modules will call the engine (intake now, build next). */
@Global()
@Module({
  providers: [EngineClient],
  exports: [EngineClient],
})
export class EngineModule {}
