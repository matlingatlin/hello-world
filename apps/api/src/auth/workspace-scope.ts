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
  // A build job carries its workspace directly, like the metering rows: it is
  // read to answer "is anything of mine building?", which must never be
  // answered with somebody else's build (B094).
  "BuildJob",
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

const CREATE_OPERATIONS = new Set(["create"]);

/**
 * Operations that need no scoping — they do not read or write rows.
 *
 * Everything NOT in this set and not scopeable above is refused rather than
 * passed through. `upsert` used to sit in CREATE_OPERATIONS and quietly do
 * nothing: an upsert has no top-level `data` (it has `create`/`update`), so
 * nothing was stamped, and it is not a read either, so nothing was filtered.
 * `createMany` was skipped outright because its `data` is an array. Neither has
 * a caller today — which is exactly when to close a hole, rather than after one
 * appears and writes a row into the wrong tenant.
 */
const UNSCOPED_OPERATIONS = new Set(["findRaw", "aggregateRaw", "$queryRaw", "$executeRaw"]);

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
    return next;
  }
  if (CREATE_OPERATIONS.has(operation) && next.data && !Array.isArray(next.data)) {
    next.data = { ...next.data, workspaceId };
    return next;
  }
  if (UNSCOPED_OPERATIONS.has(operation)) return next;
  // Fail closed. This file exists to make tenancy impossible to get wrong, and
  // an operation it does not understand must stop the request, not slip past
  // unscoped. A loud failure in development beats a silent cross-tenant write.
  throw new Error(
    `workspace scoping does not know how to scope ${model}.${operation}. ` +
      "Add it to READ_OPERATIONS or CREATE_OPERATIONS with a test, or use an unscoped model.",
  );
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
