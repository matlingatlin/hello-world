import { Controller, Get } from "@nestjs/common";
import { ApiBearerAuth, ApiOperation, ApiTags } from "@nestjs/swagger";
import type { MeResponse } from "@scio/shared";
import { CurrentUser } from "../../auth/auth-context";
import { UserService } from "./user.service";

@ApiTags("user")
@ApiBearerAuth()
@Controller("me")
export class UserController {
  constructor(private readonly users: UserService) {}

  @Get()
  @ApiOperation({ summary: "Current user + workspace (stub)" })
  me(@CurrentUser() userId: string): Promise<MeResponse> {
    return this.users.me(userId);
  }
}
