/**
 * Gate 1's contract: the wizard conversation, the typed spec, and the freeze.
 *
 * The spec shapes mirror the engine's Layer A (docs/INTAKE-SCHEMA.md) field for
 * field, in the engine's snake_case, because the API passes them through rather
 * than translating. A translation layer here would be a second place for the
 * schema to drift — and the "assumed" tags the review screen depends on live in
 * this metadata.
 */

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
  /** True when the code came from the stand-in builder (no API keys): the
   *  pipeline is real, the code is not. Shown to the user, never hidden. */
  standin: boolean;
}

export interface BuildErrorEvent {
  type: string;
  message: string;
}

export type BuildEventName = "started" | "progress" | "package" | "finished" | "error";

export interface BuildEvent {
  event: BuildEventName;
  data: BuildStarted | BuildProgress | BuildFinished | BuildErrorEvent | Record<string, unknown>;
}

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
}
