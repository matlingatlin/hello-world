import { Controller, Get, HttpCode, Param, Post, Res } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { BuildVersionListResponse, LatestBuildResponse } from "@scio/shared";
import type { Response } from "express";
import { openStream } from "../../common/sse";
import { CurrentWorkspace } from "../../auth/auth-context";
import { BuildService } from "./build.service";

@ApiTags("build")
@Controller("projects/:projectId/build")
export class BuildController {
  constructor(private readonly builds: BuildService) {}

  @Get("versions")
  @ApiOperation({ summary: "The version timeline, newest first" })
  list(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
  ): Promise<BuildVersionListResponse> {
    return this.builds.list(workspaceId, projectId);
  }

  @Get("latest")
  @ApiOperation({ summary: "The current build: preview URL + honest status" })
  latest(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
  ): Promise<LatestBuildResponse> {
    return this.builds.latest(workspaceId, projectId);
  }

  /**
   * Run a build, streaming progress as SSE.
   *
   * Written by hand rather than through Nest's @Sse decorator: that expects an
   * Observable of a fixed shape, and this relays named events (`started`,
   * `progress`, `package`, `finished`, `error`) from the engine unchanged, so
   * the browser sees exactly what the engine said.
   */
  @Post()
  // 200, not Nest's default 201: this response is a stream being read, not a
  // resource that was created — the build_version appears at the end of it.
  @HttpCode(200)
  @ApiOperation({ summary: "Build the current spec into a running app (SSE)" })
  async run(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Res() res: Response,
  ): Promise<void> {
    const { emit, close } = openStream(res);

    try {
      await this.builds.run(workspaceId, projectId, emit);
    } catch (err) {
      // The stream is already open, so an error is an event in it — a severed
      // connection would leave the build view frozen mid-progress with no reason.
      const error = err as { status?: number; message?: string };
      emit("error", {
        type: error.status === 404 ? "not_found" : "build_failed",
        message: error.message ?? "The build could not start.",
      });
    } finally {
      close();
    }
  }
}
