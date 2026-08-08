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
  list(): Promise<NotificationListResponse> {
    return this.notifications.list();
  }

  @Patch(":id/read")
  @ApiOperation({ summary: "Mark a notification read/unread (stub)" })
  markRead(@Param("id") id: string, @Body() body: MarkNotificationReadRequest): Promise<void> {
    return this.notifications.markRead(id, body.read);
  }
}
