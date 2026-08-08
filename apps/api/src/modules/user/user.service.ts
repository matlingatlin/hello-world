import { Injectable, NotImplementedException } from "@nestjs/common";
import type { MeResponse } from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

@Injectable()
export class UserService {
  constructor(private readonly prisma: PrismaService) {}

  async me(): Promise<MeResponse> {
    // TODO(3.3): look up the user by Clerk id from the verified JWT; include workspace.
    throw new NotImplementedException("user.me — lands with auth (3.3)");
  }
}
