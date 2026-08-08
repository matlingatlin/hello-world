import { Controller, Get } from "@nestjs/common";
import { ApiOkResponse, ApiOperation, ApiTags } from "@nestjs/swagger";
import type { HealthResponse } from "@scio/shared";
import { Public } from "../auth/public.decorator";
import { PrismaService } from "../prisma/prisma.service";

@ApiTags("health")
@Controller("health")
export class HealthController {
  constructor(private readonly prisma: PrismaService) {}

  @Public()
  @Get()
  @ApiOperation({ summary: "Liveness + database connectivity" })
  @ApiOkResponse({ description: "Service is up; db reports connectivity state." })
  async health(): Promise<HealthResponse> {
    let db: HealthResponse["db"] = "not_configured";
    if (this.prisma.isConfigured) {
      try {
        await this.prisma.$queryRaw`SELECT 1`;
        db = "connected";
      } catch {
        db = "error";
      }
    }
    return { status: "ok", db, timestamp: new Date().toISOString() };
  }
}
