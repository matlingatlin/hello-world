import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { AuthStatusResponse } from "@scio/shared";
import { AuthService } from "./auth.service";

@ApiTags("auth")
@Controller("auth")
export class AuthController {
  constructor(private readonly auth: AuthService) {}

  @Get("status")
  @ApiOperation({ summary: "Auth status (stub — Clerk lands in phase 3.3)" })
  status(): AuthStatusResponse {
    return this.auth.status();
  }
}
