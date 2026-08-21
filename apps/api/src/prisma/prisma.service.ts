import { Injectable, Logger, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import { PrismaClient } from "@prisma/client";

/**
 * Prisma wrapper. Connects lazily so the app can boot without a database
 * (health then reports db: "not_configured" instead of crashing).
 */
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(PrismaService.name);
  private connected = false;

  get isConfigured(): boolean {
    return Boolean(process.env.DATABASE_URL);
  }

  get isConnected(): boolean {
    return this.connected;
  }

  async onModuleInit() {
    if (!this.isConfigured) {
      this.logger.warn("DATABASE_URL not set — running without a database.");
      return;
    }
    try {
      await this.$connect();
      this.connected = true;
    } catch (err) {
      this.logger.error(`Could not connect to the database: ${String(err)}`);
    }
  }

  /**
   * On SIGTERM the pool used to drop mid-query. A deploy is a normal event and
   * should not look like a database failure to whoever was mid-request.
   */
  async onModuleDestroy(): Promise<void> {
    await this.$disconnect();
  }

}
