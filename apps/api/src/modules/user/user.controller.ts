import { Controller, Get } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { MeResponse } from "@scio/shared";
import { UserService } from "./user.service";

@ApiTags("user")
@Controller("me")
export class UserController {
  constructor(private readonly users: UserService) {}

  @Get()
  @ApiOperation({ summary: "Current user + workspace (stub)" })
  me(): Promise<MeResponse> {
    return this.users.me();
  }
}
