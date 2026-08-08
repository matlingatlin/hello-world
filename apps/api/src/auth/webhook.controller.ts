import { Body, Controller, Headers, HttpCode, Logger, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { Public } from "./public.decorator";

/**
 * Clerk webhook receiver (user.created / user.deleted) for keeping local
 * records in sync. Handler stub: provisioning is lazy (get-or-create on first
 * request), so nothing here is load-bearing yet.
 */
@ApiTags("auth")
@Controller("auth/webhooks/clerk")
export class ClerkWebhookController {
  private readonly logger = new Logger(ClerkWebhookController.name);

  @Public()
  @Post()
  @HttpCode(202)
  @ApiOperation({ summary: "Clerk webhook (stub — signature verification TODO)" })
  handle(
    @Body() event: { type?: string; data?: { id?: string } },
    @Headers("svix-signature") signature?: string,
  ): { received: boolean } {
    // TODO(3.3 follow-up): verify the svix signature (CLERK_WEBHOOK_SIGNING_SECRET)
    // before trusting the payload; reject unsigned requests in production.
    switch (event?.type) {
      case "user.created":
        // Lazy provisioning covers this; log for observability.
        this.logger.log(`clerk user.created ${event.data?.id ?? "?"}`);
        break;
      case "user.deleted":
        // TODO: mark the local user/workspace for cleanup.
        this.logger.log(`clerk user.deleted ${event.data?.id ?? "?"}`);
        break;
      default:
        this.logger.debug(`clerk webhook ignored: ${event?.type ?? "unknown"}`);
    }
    return { received: true };
  }
}
