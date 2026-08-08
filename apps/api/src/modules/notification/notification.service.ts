import { Injectable, NotImplementedException } from "@nestjs/common";
import type { NotificationListResponse } from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/** build_done | needs_look | limit | cost | update. Scoped by workspace_id + user_id. */
@Injectable()
export class NotificationService {
  constructor(private readonly prisma: PrismaService) {}

  async list(workspaceId: string, userId: string): Promise<NotificationListResponse> {
    // TODO(7): notifications for the authenticated user in their workspace.
    throw new NotImplementedException("notification.list — phase 7");
  }

  async markRead(workspaceId: string, userId: string, id: string, read: boolean): Promise<void> {
    // TODO(7): scope by workspace_id + user_id.
    throw new NotImplementedException("notification.markRead — phase 7");
  }
}
