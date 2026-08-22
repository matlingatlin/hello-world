/**
 * Gate 1's contract: the wizard conversation, the typed spec, and the freeze.
 *
 * The spec shapes mirror the engine's Layer A (docs/INTAKE-SCHEMA.md) field for
 * field, in the engine's snake_case, because the API passes them through rather
 * than translating. A translation layer here would be a second place for the
 * schema to drift — and the "assumed" tags the review screen depends on live in
 * this metadata.
 */

import type { DesignVersion } from "./entities";

export type SpecSource = "stated" | "derived" | "default";
export type SpecConfidence = "low" | "medium" | "high";

/** One filled intake slot: the value plus where it came from. */
export interface SpecField<T = unknown> {
  value: T;
  source: SpecSource;
  confidence: SpecConfidence;
  /** Ids of the wizard messages this came from. */
  provenance: string[];
}

export interface SpecContradiction {
  fields: string[];
  description: string;
  resolved: boolean;
}

export interface DataSensitivity {
  owner: string;
  sensitive: boolean;
  kinds: string[];
}

/** The Layer A spec. Unset slots are null; assumed ones carry source "default". */
export interface IntakeSpec {
  purpose?: SpecField<string> | null;
  users_and_roles?: SpecField<string[]> | null;
  entities?: SpecField<string[]> | null;
  key_actions?: SpecField<string[]> | null;
  sign_in?: SpecField<string> | null;
  data_ownership_sensitivity?: SpecField<DataSensitivity> | null;
  non_goals?: SpecField<string[]> | null;
  role_permissions?: SpecField<string> | null;
  payment?: SpecField<string> | null;
  notifications?: SpecField<string> | null;
  integrations?: SpecField<string> | null;
  media?: SpecField<string> | null;
  compliance?: SpecField<string> | null;
  visibility_seo?: SpecField<string> | null;
  localization?: SpecField<string> | null;
  scheduling?: SpecField<string> | null;
  platform?: SpecField<string>;
  data_owner?: SpecField<string>;
  look?: SpecField<string>;
  publishing?: SpecField<string>;
  security_and_a11y?: SpecField<string>;
  scale?: SpecField<string>;
  signals?: Record<string, boolean>;
  contradictions?: SpecContradiction[];
  /** Forward-compatible: the engine may add slots before this package knows them. */
  [key: string]: unknown;
}

export interface NextQuestion {
  /** The intake field it targets; empty when it is about a contradiction. */
  field: string;
  text: string;
  example: string;
  about: "field" | "contradiction";
  written_by: "model" | "guide";
}

export interface GateVerdict {
  buildable: boolean;
  missing_core: string[];
  unresolved_conditionals: string[];
  contradictions: SpecContradiction[];
}

/** One wizard turn, as the app sees it. */
export interface IntakeMessageRequest {
  text: string;
}

export interface WizardTurn {
  id: string;
  role: MessageRoleName;
  text: string;
  /** Present on Scio's turns that carried an example with the question. */
  example?: string;
}

export type MessageRoleName = "user" | "scio";

/** A low-high band. Never collapsed to one number: see BuildEstimate. */
export interface EstimateRange {
  low: number;
  high: number;
}

/** Where the app comes from — how much was reused rather than built. */
export interface EstimateComposition {
  parts_total: number;
  assembled: number;
  generated: number;
}

/**
 * What the build will cost and take, shown at the review screen.
 *
 * `cost_usd`/`minutes`/`composition` are present when the engine could price the
 * plan; when it could not, only `parts` and `packages` are, and the UI falls
 * back to the part count rather than inventing a figure.
 *
 * Always a RANGE and always for the base build: a package that needs a repair
 * round costs about twice one that passes first time, and which will is not
 * knowable in advance. `basis` carries that caveat from the engine so the UI
 * cannot quietly drop it.
 */
export interface BuildEstimate {
  parts: number;
  packages: string[];
  cost_usd?: EstimateRange | null;
  minutes?: EstimateRange | null;
  composition?: EstimateComposition | null;
  model?: string;
  passes?: number;
  basis?: string;
}

export interface IntakeStepResponse {
  updated_spec: IntakeSpec;
  buildable: boolean;
  next_question: NextQuestion | null;
  contradictions: SpecContradiction[];
  gate: GateVerdict;
  messages: WizardTurn[];
  /** The confirmation narrative, once the spec is buildable and Layer B could run. */
  whole?: string | null;
  estimate?: BuildEstimate | null;
  /** What the engine could and couldn't do for this turn — never hidden. */
  engine: EngineStatus;
  /** What this exchange cost. A wizard is one model call per message. */
  cost_usd?: number;
}

/**
 * Correcting a field the wizard filed wrongly, from the review screen.
 *
 * `clear` is how "this answer belongs under a different field" is expressed:
 * set it on the right field and empty the wrong one, in one action, so the spec
 * never passes through a state where the same answer is filed twice.
 *
 * A correction touches the WORKING spec only. A spec_version is a frozen
 * contract written at approve, and rewriting one in place would break the
 * promise that a build can be traced to exactly what was approved.
 */
export interface CorrectSpecFieldRequest {
  field: string;
  /** A sentence, a list, or the sensitivity object — whatever the field holds. */
  value: string | string[] | Record<string, unknown>;
  clear?: string[];
}

/**
 * The corrected spec, re-validated.
 *
 * Same shape as a wizard turn, so the review screen re-renders from one place,
 * plus what the correction OPENED: two roles trigger role_permissions, sensitive
 * data triggers compliance. Those are asked inline — the point of the whole
 * feature is not having to restart the wizard.
 */
export interface CorrectSpecFieldResponse extends IntakeStepResponse {
  newly_required: string[];
  still_needed: string[];
  changed: string[];
  cleared: string[];
}

export interface EngineStatus {
  reachable: boolean;
  /** Set when a non-essential engine call failed; the turn still succeeded. */
  degraded?: string[];
}

/**
 * The whole is what the user actually approved at the spec gate, so it is stored
 * with the frozen spec — the reveal's "what you built" then quotes the contract
 * rather than re-deriving prose that might come out differently.
 */
export interface ApproveSpecRequest {
  whole?: string;
}

export interface ApproveSpecResponse {
  specVersion: {
    id: string;
    number: number;
    isCurrent: boolean;
    createdAt: string;
  };
  projectStatus: string;
}

/**
 * Gate 1 leads straight to the build on the Level 1 path (no design window), so
 * the build's contract lives beside it.
 */

/** Sent once, before any part is built: the real schedule the build view draws. */
export interface BuildStarted {
  project_id: string;
  whole: string;
  packages: string[];
  total: number;
  workspace: string;
  /** What the relay will actually run — e.g. "claude-sonnet-5 only, 2 passes".
   *  Shown rather than assumed: a build's quality follows from this. */
  models?: string;
}

/** One part finishing. `done`/`total` is a real count, never a timer. */
export interface BuildProgress {
  package_id: string;
  index: number;
  total: number;
  done: number;
  status: string;
  message: string;
}

/** The reveal's payload: the running app, and what is honestly true about it. */
export interface BuildFinished {
  project_id: string;
  app_url: string;
  build_version: number | null;
  git_sha: string;
  whole: string;
  summary: string;
  works: boolean;
  parts_working: string[];
  parts_needing_a_look: string[];
  parts_blocked: string[];
  parts_failed: string[];
  remainders: string[];
  element_count: number;
  files: string[];
  total_cost_usd: number;
  /** Input + output tokens the build spent. Recorded beside the cost because a
   *  figure with no quantity behind it cannot be audited or re-priced. */
  total_tokens?: number;
  /** Which model wrote it — a cost is only re-checkable against a rate card. */
  model?: string;
  /** True when the code came from the stand-in builder (no API keys): the
   *  pipeline is real, the code is not. Shown to the user, never hidden. */
  standin: boolean;
  /** Where the app was built. A design change operates on this directory. */
  workspace?: string;
  /** True when this build carries the design window's marking bridge (Level 2).
   *  A delivery build does not. */
  preview?: boolean;
  /** id -> package + source location. The design window resolves markings
   *  against it, so it travels with the build rather than being re-derived. */
  manifest?: Record<string, unknown> | null;
  /** package -> files, for the isolation proof on a directed change. */
  package_files?: Record<string, string[]>;
  /** Every page this app has, from the plan that built it. The design window
   *  showed whichever one the app opens on and offered no way to reach the
   *  others, so half an app could not be marked up at all (B069). */
  routes?: string[];
}

export interface BuildErrorEvent {
  type: string;
  message: string;
}

/** One part's own record, as the build reports it when it finishes. */
export interface BuildPackageResult {
  package_id: string;
  status: "passed" | "needs_look" | "failed" | "blocked";
  files: string[];
  remainders: { what: string; where?: string; source?: string }[];
  checks_passed: number;
  checks_total: number;
  total_cost_usd?: number;
  total_tokens?: number;
  /** Set when the part came from the library rather than being written. */
  entry_id?: string;
}

/** What a build gave back to the component library, when it gave anything. */
export interface BuildLibraryNote {
  summary: string;
  added: string[];
}

/**
 * Every event a build stream can carry, as a discriminated union.
 *
 * The build stream was the one path in the product that opted out of these
 * types (B089): the events were declared here and then consumed as
 * `Record<string, unknown>` with a cast at each use site, so the compiler could
 * not tell anyone that `payload.total` does not exist on an error. Switching on
 * `event` now narrows `data`, and the single unchecked cast lives at the wire —
 * where the claim is actually being made.
 */
export type BuildEvent =
  | { event: "started"; data: BuildStarted }
  | { event: "progress"; data: BuildProgress }
  | { event: "package"; data: BuildPackageResult }
  | { event: "library"; data: BuildLibraryNote }
  | { event: "finished"; data: BuildFinished }
  | { event: "error"; data: BuildErrorEvent };

export type BuildEventName = BuildEvent["event"];

/**
 * The design window's preview stream: a build, plus the version it produced.
 *
 * Same events as a build — it *is* a build — with one more at the end, because
 * the design window needs to know which version it is now looking at.
 */
export type DesignPreviewEvent =
  | BuildEvent
  | { event: "design_version"; data: DesignVersion };

export type DesignPreviewEventName = DesignPreviewEvent["event"];

/**
 * What the reveal shows. Read back from the database rather than carried in the
 * router, so returning to a finished project months later shows the same thing.
 */
export interface LatestBuildResponse {
  buildVersion: {
    id: string;
    number: number;
    description: string;
    gitSha: string;
    isCurrent: boolean;
    createdAt: string;
    /** What this build cost, on the build's own record. Null for builds
     *  recorded before this existed — 0 would be a claim, not an absence. */
    costUsd?: number | null;
    tokens?: number | null;
  } | null;
  previewUrl: string | null;
  projectStatus: string;
  honestStatus: {
    works: boolean;
    summary: string;
    working: string[];
    needs_look: string[];
    blocked: string[];
    failed: string[];
    remainders: string[];
    standin: boolean;
  } | null;
  whole: string | null;
  /** The estimate the user approved against, frozen with the spec. Comparing
   *  spend to a figure that has since moved would be worse than no comparison. */
  estimate?: BuildEstimate | null;
  /** What this build actually cost, read back from the metering record.
   *  The estimate says what a build should cost; this says what it did. Null
   *  when nothing was metered — which is the truthful answer for a build that
   *  assembled every part from the library and called no model at all. */
  spend?: BuildSpend | null;
}

export interface BuildSpend {
  costUsd: number;
  tokens: number;
  model: string;
  at: string;
}
