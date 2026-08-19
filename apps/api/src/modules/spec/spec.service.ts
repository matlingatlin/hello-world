import { ConflictException, Injectable, NotFoundException } from "@nestjs/common";
import type {
  AmendSpecRequest,
  AmendSpecResponse,
  ApproveSpecRequest,
  ApproveSpecResponse,
  IntakeSpec,
  SpecField,
  SpecVersionListResponse,
  SpecVersionResponse,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";
import { EngineClient } from "../../engine/engine.client";

/**
 * Frozen spec contracts. All queries scoped via project -> workspace_id.
 *
 * Freezing is what gate 1 is *for*: after it, the build has something it can be
 * held to. So a spec_version is written once and never edited — a later change
 * is a new version, and the old one stays readable because a build points at it.
 */
@Injectable()
export class SpecService {
  constructor(
    private readonly scope: WorkspaceScope,
    private readonly engine: EngineClient,
  ) {}

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
  async approve(
    workspaceId: string,
    projectId: string,
    body: ApproveSpecRequest = {},
  ): Promise<ApproveSpecResponse> {
    const project = await this.project(workspaceId, projectId);
    const spec = (project.draftSpec ?? null) as IntakeSpec | null;
    if (!spec || Object.keys(spec).length === 0) {
      throw new ConflictException("There is no spec to approve yet — finish the wizard first.");
    }

    // The gate, checked where it is enforceable.
    //
    // The review screen holds its own approve button shut, but a button is not a
    // rule — and this became reachable the moment fields became editable there:
    // correcting "one role" to "two roles" opens role_permissions, and freezing
    // that spec would produce a contract Layer B refuses to build, discovered
    // minutes later in the build view instead of instantly here.
    //
    // An unreachable engine is NOT a refusal: we cannot prove the spec is
    // unbuildable, so approve behaves as it always did rather than blocking on
    // an outage.
    const verdict = await this.engine.validate(spec);
    if (verdict && !verdict.result.buildable) {
      const missing = [
        ...verdict.result.missing_core,
        ...verdict.result.unresolved_conditionals,
      ];
      throw new ConflictException(
        missing.length > 0
          ? `This spec still needs: ${missing.join(", ")}.`
          : "This spec has an unresolved contradiction — settle it before approving.",
      );
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
        assumptions: {
          assumed: assumedFields(spec),
          // What was on screen when they pressed the button.
          ...(body.whole ? { whole: body.whole } : {}),
        },
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

  /**
   * Change the approved spec because a marking argued with it.
   *
   * The design window asks before it builds — "you said no payments; do you
   * want them after all?" — and this is what "yes" means. It is a spec change,
   * frozen as a new version, not a flag on a change request: the spec is what
   * the build is held to, and something built against a decision the user
   * reversed has to be able to show when they reversed it.
   *
   * The two kinds are deliberately not the same act:
   *
   * - `non_goal` removes the thing the spec excluded. Exact, and the conflict
   *   disappears because the architecture no longer excludes it.
   * - `auth` / `access` leave the security posture ALONE and record an
   *   allowance. The spec still says the data is sensitive — because it is —
   *   and the record says what the user permitted anyway. Rewriting the posture
   *   from a side panel is how secure defaults quietly stop being defaults
   *   (ADR-0001), and this is the product's wedge.
   *
   * The known cost of an allowance: code and posture can drift, because the
   * architecture keeps deriving protections the code was allowed to skip. A
   * deeper change belongs in the wizard, and the design window says so.
   */
  async amend(
    workspaceId: string,
    projectId: string,
    body: AmendSpecRequest,
  ): Promise<AmendSpecResponse> {
    await this.project(workspaceId, projectId);
    const says = (body.specSays ?? "").trim();
    if (!says) {
      throw new ConflictException("An amendment has to name what it changes.");
    }

    const previous = await this.client(workspaceId).specVersion.findMany({
      where: { projectId },
      orderBy: { number: "desc" },
    });
    const current = previous.find((r: { isCurrent: boolean }) => r.isCurrent) ?? previous[0];
    if (!current) {
      throw new ConflictException("There is no approved spec to amend.");
    }

    const spec = structuredClone(current.content ?? {}) as IntakeSpec;
    const assumptions = { ...((current.assumptions ?? {}) as Record<string, unknown>) };
    const allowances = [...toStrings(assumptions.allowances)];
    let removedNonGoal: string | null = null;

    if (body.kind === "non_goal") {
      const field = spec.non_goals;
      const kept = (field?.value ?? []).filter((item) => !same(item, says));
      if (field && kept.length !== field.value.length) {
        removedNonGoal = says;
        spec.non_goals = {
          ...field,
          value: kept,
          provenance: [...(field.provenance ?? []), `dropped in the design window: ${says}`],
        };
      }
      // Not found is not an error: the same conflict answered twice must not
      // fail the second time, or the design window gets stuck on it.
    } else if (!allowances.some((a) => same(a, says))) {
      allowances.push(says);
    }

    assumptions.allowances = allowances;
    assumptions.amendments = [
      ...toRecords(assumptions.amendments),
      {
        kind: body.kind,
        specSays: says,
        note: body.note ?? "",
        at: new Date().toISOString(),
      },
    ];

    for (const row of previous.filter((r: { isCurrent: boolean }) => r.isCurrent)) {
      await this.client(workspaceId).specVersion.update({
        where: { id: row.id },
        data: { isCurrent: false },
      });
    }

    const created = await this.client(workspaceId).specVersion.create({
      data: {
        projectId,
        number: (previous[0]?.number ?? 0) + 1,
        content: spec as object,
        assumptions: assumptions as object,
        isCurrent: true,
      },
    });

    // The draft follows the frozen spec, or re-approving would quietly put the
    // dropped non-goal back and the same question would be asked again.
    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { draftSpec: spec as object },
    });

    return {
      specVersion: {
        id: created.id,
        number: created.number,
        isCurrent: true,
        createdAt: new Date(created.createdAt).toISOString(),
      },
      allowances,
      removedNonGoal,
    };
  }
}

/** Two sentences that mean the same allowance. Compared the way they were shown. */
function same(a: string, b: string): boolean {
  return a.trim().toLowerCase() === b.trim().toLowerCase();
}

function toStrings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function toRecords(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? (value as Array<Record<string, unknown>>) : [];
}

/** The allowances recorded on a frozen spec version. */
export function allowancesOf(assumptions: unknown): string[] {
  const record = (assumptions ?? {}) as Record<string, unknown>;
  return toStrings(record.allowances);
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
