import { Injectable, NotFoundException } from "@nestjs/common";
import type {
  EngineStatus,
  IntakeSpec,
  IntakeStepResponse,
  BuildEstimate,
  WizardTurn,
} from "@scio/shared";
import { WorkspaceScope } from "../../auth/workspace-scope";
import { EngineClient } from "../../engine/engine.client";

/**
 * Gate 1's server side: one wizard turn, persisted.
 *
 *   load the conversation -> append what they said -> ask the engine ->
 *   persist the updated spec and Scio's reply -> (once buildable) fetch the
 *   confirmation and a rough part count
 *
 * The conversation is stored rather than held in the browser because provenance
 * points at message ids: a spec that says "you told me this in m3" is worthless
 * if m3 disappears when the tab closes.
 *
 * The working spec lives on the project, not in a spec_version. A spec_version is
 * a frozen contract; rewriting one in place would break the promise that a build
 * can always be traced to exactly what was approved.
 */
@Injectable()
export class IntakeService {
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
    // 404 rather than 403 across tenants — a 403 would confirm the id exists.
    if (!row) throw new NotFoundException("Project not found");
    return row;
  }

  /**
   * The wizard as it stands, without taking a turn.
   *
   * This used to answer `buildable: false` with an empty gate, always — which
   * meant a reload of the wizard showed "0 of 6" however far along you were,
   * and the review screen, which loads through here, could never show the
   * whole or the cost estimate. Both only ever existed in the reply to a
   * message, so they vanished the moment the page was fetched again.
   *
   * The gate is deterministic and free, so it is recomputed here rather than
   * remembered. The confirmation costs a Layer B call, so it is fetched only
   * once the spec is actually buildable — which is exactly when the review
   * screen asks for it.
   */
  async history(workspaceId: string, projectId: string): Promise<IntakeStepResponse> {
    const project = await this.project(workspaceId, projectId);
    const messages = await this.messages(workspaceId, projectId);
    const spec = (project.draftSpec ?? null) as IntakeSpec | null;
    const engine: EngineStatus = { reachable: true };

    const verdict = spec ? await this.engine.validate(spec) : null;
    if (spec && !verdict) {
      engine.degraded = [...(engine.degraded ?? []), "validate"];
    }
    const gate = verdict?.result ?? {
      buildable: false,
      missing_core: [],
      unresolved_conditionals: [],
      contradictions: [],
    };

    let whole: string | null = null;
    let estimate: BuildEstimate | null = null;
    if (gate.buildable && spec) {
      ({ whole, estimate } = await this.confirmation(spec, engine));
    }

    return {
      updated_spec: spec ?? {},
      buildable: gate.buildable,
      next_question: null,
      contradictions: (spec?.contradictions ?? []).filter((c) => !c.resolved),
      gate,
      messages,
      whole,
      estimate,
      engine,
    };
  }

  private async messages(workspaceId: string, projectId: string): Promise<WizardTurn[]> {
    const rows = await this.client(workspaceId).message.findMany({
      where: { projectId },
      orderBy: { createdAt: "asc" },
    });
    return rows.map((row: { id: string; role: string; content: string }) => ({
      id: row.id,
      role: row.role as WizardTurn["role"],
      text: row.content,
    }));
  }

  async step(workspaceId: string, projectId: string, text: string): Promise<IntakeStepResponse> {
    const project = await this.project(workspaceId, projectId);

    await this.client(workspaceId).message.create({
      data: { projectId, role: "user", content: text },
    });

    const history = await this.messages(workspaceId, projectId);
    const step = await this.engine.intakeStep({
      // The engine's message ids ARE the provenance it writes into the spec, so
      // they must be the database ids — not positions in this request.
      messages: history.map((m) => ({
        id: m.id,
        role: m.role === "scio" ? "assistant" : "user",
        text: m.text,
      })),
      spec: (project.draftSpec ?? null) as IntakeSpec | null,
    });

    const question = step.next_question;
    if (question) {
      await this.client(workspaceId).message.create({
        data: {
          projectId,
          role: "scio",
          content: question.example ? `${question.text} For example: ${question.example}` : question.text,
        },
      });
    }

    await this.client(workspaceId).project.update({
      where: { id: projectId },
      data: { draftSpec: step.updated_spec as object },
    });

    const engine: EngineStatus = { reachable: true };
    let whole: string | null = null;
    let estimate: BuildEstimate | null = null;

    if (step.buildable) {
      ({ whole, estimate } = await this.confirmation(step.updated_spec, engine));
    }

    const messages = await this.messages(workspaceId, projectId);
    const last = messages[messages.length - 1];
    if (question && last && last.role === "scio") {
      // The example is stored inside the message text (so a reload still shows
      // it) and carried separately so the UI can style it as the prototype does.
      last.example = question.example;
    }

    return {
      updated_spec: step.updated_spec,
      buildable: step.buildable,
      next_question: question,
      contradictions: step.contradictions,
      gate: step.gate,
      messages,
      whole,
      estimate,
      engine,
    };
  }

  /**
   * The review screen's confirmation and rough size.
   *
   * Both are decoration on top of a spec the user can already read, so neither
   * may take the turn down with it: a failure is recorded in `degraded` and the
   * screen falls back to the structured spec. Without keys the engine's fake
   * provider returns a minimal whole — that is documented behaviour, not an
   * error.
   */
  private async confirmation(
    spec: IntakeSpec,
    engine: EngineStatus,
  ): Promise<{ whole: string | null; estimate: BuildEstimate | null }> {
    const architecture = await this.engine.architecture(spec);
    if (!architecture) {
      engine.degraded = [...(engine.degraded ?? []), "architecture"];
      return { whole: null, estimate: null };
    }

    // The narrative is nested inside Layer B's whole object — reading `whole`
    // directly would silently always be null.
    const narrative = architecture.whole?.narrative ?? null;
    const graph = architecture.architecture;
    if (!graph || typeof graph !== "object") {
      engine.degraded = [...(engine.degraded ?? []), "plan"];
      return { whole: narrative, estimate: null };
    }

    const planned = await this.engine.plan(graph as Record<string, unknown>, narrative ?? "");
    if (!planned) {
      engine.degraded = [...(engine.degraded ?? []), "plan"];
      return { whole: narrative, estimate: null };
    }
    const packages = planned.plan?.packages?.map((p) => p.id) ?? [];
    // The engine prices the plan deterministically as part of planning it. When
    // it could not, the review screen falls back to the part count rather than
    // inventing a figure — an estimate we cannot stand behind is worse than none.
    const priced = planned.estimate;
    return {
      whole: narrative,
      estimate: {
        parts: packages.length,
        packages,
        cost_usd: priced?.cost_usd ?? null,
        minutes: priced?.minutes ?? null,
        composition: priced?.composition ?? null,
        model: priced?.model,
        passes: priced?.passes,
        basis: priced?.basis,
      },
    };
  }
}
