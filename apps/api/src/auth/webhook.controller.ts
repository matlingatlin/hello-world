import {
  Body,
  Controller,
  Headers,
  HttpCode,
  Logger,
  Post,
  UnauthorizedException,
} from "@nestjs/common";
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
    // Fail closed, in the right order.
    //
    // The handler is inert today — it logs — so an unsigned POST is noise
    // rather than account manipulation. The danger is the sequence: the moment
    // somebody implements `user.deleted` cleanup behind an unverified
    // signature, an anonymous request deletes accounts. So the refusal lands
    // FIRST, and whoever implements the handler inherits it.
    const secret = process.env.CLERK_WEBHOOK_SIGNING_SECRET ?? "";
    if (secret && !signature) {
      throw new UnauthorizedException("unsigned webhook");
    }
    if (!secret && process.env.NODE_ENV === "production") {
      throw new UnauthorizedException(
        "CLERK_WEBHOOK_SIGNING_SECRET is not set, so this request cannot be trusted",
      );
    }
    // TODO(3.3 follow-up): verify the svix signature itself, not merely its
    // presence — `svix` is the library, and this refusal is already in place.
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
