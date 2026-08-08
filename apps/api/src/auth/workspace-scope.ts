import { Injectable } from "@nestjs/common";
import { PrismaService } from "../prisma/prisma.service";

/**
 * Tenant isolation, enforced at the data layer (ADR-0009).
 *
 * Models carrying workspace_id directly are auto-scoped: reads get
 * `workspaceId` merged into `where`, creates get it stamped into `data`.
 * Project-child models (spec/build/message/…) are scoped via their project —
 * services must resolve the project through this scoped client first.
 */

const WORKSPACE_SCOPED_MODELS = new Set([
  "Project",
  "UsageEvent",
  "Notification",
  "AuditLog",
  "User",
]);

const READ_OPERATIONS = new Set([
  "findFirst",
  "findFirstOrThrow",
  "findMany",
  "findUnique",
  "findUniqueOrThrow",
  "count",
  "aggregate",
  "groupBy",
  "update",
  "updateMany",
  "delete",
  "deleteMany",
]);

const CREATE_OPERATIONS = new Set(["create", "createMany", "upsert"]);

/** Pure helper — exported for tests. Returns args with workspace scoping applied. */
export function applyWorkspaceScope(
  model: string,
  operation: string,
  args: Record<string, any>,
  workspaceId: string,
): Record<string, any> {
  if (!WORKSPACE_SCOPED_MODELS.has(model)) return args;
  const next = { ...args };
  if (READ_OPERATIONS.has(operation)) {
    next.where = { ...(next.where ?? {}), workspaceId };
  }
  if (CREATE_OPERATIONS.has(operation) && next.data && !Array.isArray(next.data)) {
    next.data = { ...next.data, workspaceId };
  }
  return next;
}

@Injectable()
export class WorkspaceScope {
  constructor(private readonly prisma: PrismaService) {}

  /**
   * A Prisma client where every query on a workspace-scoped model is filtered
   * by (or stamped with) the given workspace_id. Services must use this —
   * never the raw client — for tenant data.
   */
  forWorkspace(workspaceId: string) {
    return this.prisma.$extends({
      query: {
        $allModels: {
          $allOperations({ model, operation, args, query }) {
            return query(applyWorkspaceScope(model, operation, args as any, workspaceId));
          },
        },
      },
    });
  }
}
