import { ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import type {
  ApproveSpecResponse,
  IntakeSpec,
  SpecField,
  SpecVersionListResponse,
  SpecVersionResponse,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";

/**
 * Frozen spec contracts. All queries scoped via project -> workspace_id.
 *
 * Freezing is what gate 1 is *for*: after it, the build has something it can be
 * held to. So a spec_version is written once and never edited — a later change
 * is a new version, and the old one stays readable because a build points at it.
 */
@Injectable()
export class SpecService {
  constructor(private readonly scope: WorkspaceScope) {}

  private client(workspaceId: string) {
    return this.scope.forWorkspace(workspaceId);
  }

  private async project(workspaceId: string, projectId: string) {
    const row = await this.client(workspaceId).project.findFirst({
      where: { id: projectId, deletedAt: null },
    });
    if (!row) throw new NotFoundException("Project not found");
    return row;
  }

  async list(workspaceId: string, projectId: string): Promise<SpecVersionListResponse> {
    await this.project(workspaceId, projectId);
    const rows = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    return { specVersions: rows.map(toSpecVersion) };
  }

  /**
   * Freeze the wizard's working spec as the current version.
   *
   * The assumptions are extracted here rather than trusted from the client: they
   * are the "assumed" tags the user was shown at the review screen, and a frozen
   * contract must record what was actually assumed on their behalf.
   */
  async approve(workspaceId: string, projectId: string): Promise<ApproveSpecResponse> {
    const project = await this.project(workspaceId, projectId);
    const spec = (project.draftSpec ?? null) as IntakeSpec | null;
    if (!spec || Object.keys(spec).length === 0) {
      throw new ConflictException("There is no spec to approve yet — finish the wizard first.");
    }

    const previous = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const number = (previous[0]?.number ?? 0) + 1;

    for (const row of previous.filter((r: { isCurrent: boolean }) => r.isCurrent)) {
      await this.client(workspaceId).specVersion.update({
        where: { id: row.id },
        data: { isCurrent: false },
      });
    }

    const created = await this.client(workspaceId).specVersion.create({
      data: {
        projectId,
        number,
        content: spec as object,
        assumptions: { assumed: assumedFields(spec) },
        isCurrent: true,
      },
    });

    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { status: "spec_locked" },
    });

    return {
      specVersion: {
        id: created.id,
        number: created.number,
        isCurrent: true,
        createdAt: new Date(created.createdAt).toISOString(),
      },
      projectStatus: "spec_locked",
    };
  }
}

function isField(value: unknown): value is SpecField {
  return typeof value === "object" && value !== null && "source" in value && "value" in value;
}

/** The fields carried by a flagged default — what the review screen showed as "assumed". */
export function assumedFields(spec: IntakeSpec): string[] {
  return Object.entries(spec)
    .filter(([, value]) => isField(value) && value.source === "default")
    .map(([name]) => name)
    .sort();
}

function toSpecVersion(row: {
  id: string;
  projectId: string;
  number: number;
  content: unknown;
  assumptions: unknown;
  isCurrent: boolean;
  createdAt: Date | string;
}): SpecVersionResponse["specVersion"] {
  return {
    id: row.id,
    projectId: row.projectId,
    number: row.number,
    content: (row.content ?? {}) as Record<string, unknown>,
    assumptions: (row.assumptions ?? {}) as Record<string, unknown>,
    isCurrent: row.isCurrent,
    createdAt: new Date(row.createdAt).toISOString(),
  };
}
