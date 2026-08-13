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

/**
 * The rough signal shown at the review screen. Deliberately a part count, not a
 * price: the real cost formula is a later step (docs/STRATEGY.md, section B), and
 * showing a number we cannot stand behind would be worse than showing none.
 */
export interface RoughEstimate {
  parts: number;
  /** Always true here — kept explicit so the UI can never quietly drop the caveat. */
  rough: true;
  packages: string[];
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
  estimate?: RoughEstimate | null;
  /** What the engine could and couldn't do for this turn — never hidden. */
  engine: EngineStatus;
}

export interface EngineStatus {
  reachable: boolean;
  /** Set when a non-essential engine call failed; the turn still succeeded. */
  degraded?: string[];
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
