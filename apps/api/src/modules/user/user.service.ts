import { Injectable, NotImplementedException } from "@nestjs/common";
import type { MeResponse } from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

@Injectable()
export class UserService {
  constructor(private readonly prisma: PrismaService) {}

  async me(userId: string): Promise<MeResponse> {
    // TODO(3.4): return the provisioned user + workspace for this userId.
    throw new NotImplementedException("user.me — phase 3.4");
  }
}
