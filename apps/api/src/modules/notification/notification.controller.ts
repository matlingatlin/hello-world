import { CurrentUser, CurrentWorkspace } from "../../auth/auth-context";
import { Body, Controller, Get, Param, Patch } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { MarkNotificationReadRequest, NotificationListResponse } from "@scio/shared";
import { NotificationService } from "./notification.service";

@ApiTags("notification")
@Controller("notifications")
export class NotificationController {
  constructor(private readonly notifications: NotificationService) {}

  @Get()
  @ApiOperation({ summary: "List notifications (stub)" })
  list(@CurrentWorkspace() workspaceId: string, @CurrentUser() userId: string): Promise<NotificationListResponse> {
    return this.notifications.list(workspaceId, userId);
  }

  @Patch(":id/read")
  @ApiOperation({ summary: "Mark a notification read/unread (stub)" })
  markRead(
    @CurrentWorkspace() workspaceId: string,
    @CurrentUser() userId: string,
    @Param("id") id: string, @Body() body: MarkNotificationReadRequest): Promise<void> {
    return this.notifications.markRead(workspaceId, userId, id, body.read);
  }
}
