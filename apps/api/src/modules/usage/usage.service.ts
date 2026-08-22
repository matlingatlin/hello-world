import { Injectable, Logger } from "@nestjs/common";
import type { UsageListResponse } from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";

/**
 * What a workspace has spent, and whether it may spend more.
 *
 * `list` used to throw `NotImplementedException`, which meant the product could
 * *predict* a cost, *record* a cost, and never *answer* the question a business
 * asks first: how much have we spent? The rows were there the whole time.
 *
 * The ceiling is the other half. A per-BUILD ceiling has always been enforced in
 * the relay, and it is the wrong unit on its own: it bounds one build and
 * nothing bounds the number of builds. One compromised or careless account could
 * run them back to back until a card or a model quota stopped it — the platform
 * had no opinion.
 */
@Injectable()
export class UsageService {
  private readonly logger = new Logger(UsageService.name);

  constructor(private readonly scope: WorkspaceScope) {}

  /**
   * What a workspace may spend in a period, in USD.
   *
   * An env var with a documented default rather than a per-plan column: plans
   * and pricing are an open product decision (B063), and inventing a per-plan
   * number here would be pretending that decision has been made. What must not
   * wait for it is *having a ceiling at all*.
   */
  static cap(): number {
    const raw = Number(process.env.SCIO_WORKSPACE_PERIOD_CAP_USD);
    return Number.isFinite(raw) && raw > 0 ? raw : 50;
  }

  /** The window a cap applies to: the calendar month, in UTC. */
  static periodStart(now = new Date()): Date {
    return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
  }

  async list(workspaceId: string): Promise<UsageListResponse> {
    const rows = await this.scope.forWorkspace(workspaceId).usageEvent.findMany({
      orderBy: { createdAt: "desc" },
    });
    return {
      usageEvents: rows.map((row: Record<string, unknown>) => ({
        id: row.id as string,
        workspaceId: row.workspaceId as string,
        projectId: (row.projectId as string) ?? null,
        kind: row.kind as UsageListResponse["usageEvents"][number]["kind"],
        model: (row.model as string) ?? null,
        amount: Number(row.amount),
        cost: Number(row.cost),
        createdAt: new Date(row.createdAt as string).toISOString(),
      })),
    };
  }

  /** What this workspace has spent since the period began. */
  async spentThisPeriod(workspaceId: string): Promise<number> {
    const rows = await this.scope.forWorkspace(workspaceId).usageEvent.findMany({
      where: { createdAt: { gte: UsageService.periodStart() } },
    });
    return rows.reduce(
      (total: number, row: { cost: unknown }) => total + Number(row.cost ?? 0),
      0,
    );
  }

  /**
   * Whether there is room to start more work, and what the figures are.
   *
   * Returns rather than throws: the caller decides what refusing looks like,
   * and the numbers belong in the refusal — "you have spent $50.12 of $50 this
   * month" is actionable, "over budget" is not.
   */
  async allowance(workspaceId: string): Promise<{
    spent: number;
    cap: number;
    room: boolean;
  }> {
    const cap = UsageService.cap();
    const spent = await this.spentThisPeriod(workspaceId);
    return { spent, cap, room: spent < cap };
  }
}
