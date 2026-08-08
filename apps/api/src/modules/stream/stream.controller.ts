import { Controller, Param, Sse } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { interval, map, Observable, take } from "rxjs";

interface SseMessage {
  data: string;
  type?: string;
}

/**
 * SSE plumbing for later engine output (multi-pass narration, build progress).
 * Skeleton stage: emits a few heartbeat events and completes. The real stream
 * (phase 4/7) relays engine events for projects in the caller's workspace only.
 */
@ApiTags("stream")
@Controller("projects/:projectId/stream")
export class StreamController {
  @Sse()
  @ApiOperation({ summary: "Engine output stream (SSE stub — heartbeats only)" })
  stream(@Param("projectId") projectId: string): Observable<SseMessage> {
    return interval(1000).pipe(
      take(3),
      map((i) => ({
        type: "build.progress",
        data: JSON.stringify({ projectId, heartbeat: i, note: "stub stream" }),
      })),
    );
  }
}
