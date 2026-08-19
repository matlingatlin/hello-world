import { Body, Controller, Get, Param, Post, Res } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import type { Response } from "express";
import type {
  ApplyDesignChangeRequest,
  ApplyDesignChangeResponse,
  DesignPreviewResponse,
  DesignVersionListResponse,
  DesignVersionResponse,
  FreezeDesignRequest,
  RestoreDesignVersionResponse,
} from "@scio/shared";
import { CurrentWorkspace } from "../../auth/auth-context";
import { DesignService } from "./design.service";

/**
 * Level 2 — the design window's backend.
 *
 * Generating a preview streams, for the same reason a build does: it takes
 * minutes and the window shows real per-part progress. Applying a change does
 * not — it either lands, or comes back with a question.
 */
@ApiTags("design")
@Controller("projects/:projectId/design")
export class DesignController {
  constructor(private readonly designs: DesignService) {}

  @Get()
  @ApiOperation({ summary: "The current preview: URL, manifest and design version" })
  current(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
  ): Promise<DesignPreviewResponse> {
    return this.designs.current(workspaceId, projectId);
  }

  @Post("preview")
  @ApiOperation({ summary: "Generate the preview the design window embeds (SSE)" })
  async generate(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Res() res: Response,
  ): Promise<void> {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache, no-transform");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders?.();

    await this.designs.generate(workspaceId, projectId, (event, data) => {
      res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    });
    res.end();
  }

  @Post("change")
  @ApiOperation({ summary: "Apply a batch of markings to only the packages they touch" })
  change(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: ApplyDesignChangeRequest,
  ): Promise<ApplyDesignChangeResponse> {
    return this.designs.change(workspaceId, projectId, body);
  }
}

/**
 * The version history, on its own path.
 *
 * Kept separate from the routes above because it is the *record* rather than
 * the working surface — gate 2b's undo reads from here.
 */
@ApiTags("design")
@Controller("projects/:projectId/design-versions")
export class DesignVersionController {
  constructor(private readonly designs: DesignService) {}

  @Get()
  @ApiOperation({ summary: "Every design version, newest first" })
  list(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
  ): Promise<DesignVersionListResponse> {
    return this.designs.list(workspaceId, projectId);
  }

  @Post(":versionId/restore")
  @ApiOperation({ summary: "Put an earlier design version's code back" })
  restore(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Param("versionId") versionId: string,
  ): Promise<RestoreDesignVersionResponse> {
    return this.designs.restore(workspaceId, projectId, versionId);
  }

  @Post()
  @ApiOperation({ summary: "Freeze the approved design as a new version" })
  freeze(
    @CurrentWorkspace() workspaceId: string,
    @Param("projectId") projectId: string,
    @Body() body: FreezeDesignRequest,
  ): Promise<DesignVersionResponse> {
    return this.designs.freeze(workspaceId, projectId, body);
  }
}
