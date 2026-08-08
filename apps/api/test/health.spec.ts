import { describe, expect, it } from "vitest";
import { HealthController } from "../src/health/health.controller";
import { PrismaService } from "../src/prisma/prisma.service";

describe("HealthController", () => {
  it("reports ok with db not_configured when DATABASE_URL is unset", async () => {
    delete process.env.DATABASE_URL;
    const controller = new HealthController(new PrismaService());
    const res = await controller.health();
    expect(res.status).toBe("ok");
    expect(res.db).toBe("not_configured");
    expect(res.timestamp).toBeTruthy();
  });
});
