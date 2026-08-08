import { Controller, Get } from "@nestjs/common";
import { ApiBearerAuth, ApiOperation, ApiTags } from "@nestjs/swagger";
import type { AuthStatusResponse } from "@scio/shared";
import { CurrentUser } from "../../auth/auth-context";

@ApiTags("auth")
@Controller("auth")
export class AuthController {
  @Get("status")
  @ApiBearerAuth()
  @ApiOperation({ summary: "Auth status for the authenticated caller" })
  status(@CurrentUser() userId: string): AuthStatusResponse {
    return { authenticated: true, userId };
  }
}
