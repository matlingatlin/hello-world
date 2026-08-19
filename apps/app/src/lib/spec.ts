import type { IntakeSpec, SpecField } from "@scio/shared";

/**
 * Reading Layer A's spec for display.
 *
 * The metadata is the point: `source: "default"` is an assumption Scio made on
 * the user's behalf, and the product's promise is that those are shown, not
 * buried. Every place that renders a spec goes through here so the "assumed" tag
 * cannot be forgotten on one screen and present on another.
 */

export const CORE_FIELDS = [
  "purpose",
  "users_and_roles",
  "entities",
  "key_actions",
  "sign_in",
  "data_ownership_sensitivity",
] as const;

const LABELS: Record<string, string> = {
  purpose: "What it does",
  users_and_roles: "Who it's for",
  entities: "What it manages",
  key_actions: "What users can do",
  sign_in: "Sign-in",
  data_ownership_sensitivity: "Data & sensitivity",
  non_goals: "Deliberately skipped",
  role_permissions: "Who may do what",
  payment: "Payments",
  notifications: "Notifications",
  integrations: "Integrations",
  media: "Files & media",
  compliance: "Compliance",
  visibility_seo: "Public & search",
  localization: "Languages",
  scheduling: "Times & scheduling",
  platform: "Platform",
  data_owner: "Data owner",
  look: "Look",
  publishing: "Publishing",
  security_and_a11y: "Security & accessibility",
  scale: "Scale",
};

export function labelFor(field: string): string {
  return LABELS[field] ?? field.replace(/_/g, " ");
}

export function isSpecField(value: unknown): value is SpecField {
  return typeof value === "object" && value !== null && "value" in value && "source" in value;
}

/** A field's value as one readable line — lists joined, sensitivity summarised. */
export function readValue(field: SpecField): string {
  const value = field.value;
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") {
    const sensitivity = value as { owner?: string; sensitive?: boolean; kinds?: string[] };
    const kinds = sensitivity.kinds?.length ? ` (${sensitivity.kinds.join(", ")})` : "";
    const sensitive = sensitivity.sensitive ? "sensitive" : "nothing sensitive";
    return `${sensitivity.owner ?? "you"} owns it — ${sensitive}${kinds}`;
  }
  return String(value ?? "");
}

export interface SpecRow {
  field: string;
  label: string;
  value: string;
  assumed: boolean;
  derived: boolean;
}

function rowFor(spec: IntakeSpec, field: string): SpecRow | null {
  const raw = spec[field];
  if (!isSpecField(raw)) return null;
  return {
    field,
    label: labelFor(field),
    value: readValue(raw),
    assumed: raw.source === "default",
    derived: raw.source === "derived",
  };
}

/** Everything answered so far, core fields first, in the schema's order. */
export function specRows(spec: IntakeSpec): SpecRow[] {
  const core = CORE_FIELDS.map((field) => rowFor(spec, field)).filter(Boolean) as SpecRow[];
  const rest = Object.keys(spec)
    .filter((field) => !CORE_FIELDS.includes(field as (typeof CORE_FIELDS)[number]))
    .map((field) => rowFor(spec, field))
    .filter(Boolean) as SpecRow[];
  return [...core, ...rest];
}

/** The rows the review screen shows under "assumptions I made". */
export function assumptionRows(spec: IntakeSpec): SpecRow[] {
  return specRows(spec).filter((row) => row.assumed);
}

/**
 * What shape a field holds, so the review screen can offer the right editor.
 *
 * Read from the value when there is one — that cannot drift from the spec. The
 * two sets below are only for a field that is EMPTY and being asked for: a
 * correction can open `role_permissions`, and there is no value to look at.
 * They mirror `intake/fields.py`'s guide, where the shapes are actually defined.
 */
export type FieldKind = "text" | "list" | "sensitivity";

const LIST_FIELDS = new Set(["users_and_roles", "entities", "key_actions", "non_goals"]);
const SENSITIVITY_FIELDS = new Set(["data_ownership_sensitivity"]);

export function kindOf(field: string, value?: unknown): FieldKind {
  if (Array.isArray(value)) return "list";
  if (value !== null && value !== undefined && typeof value === "object") return "sensitivity";
  if (LIST_FIELDS.has(field)) return "list";
  if (SENSITIVITY_FIELDS.has(field)) return "sensitivity";
  return "text";
}

/** Every field a correction may target — what "this belongs somewhere else" offers. */
export const CORRECTABLE_FIELDS: string[] = [
  ...CORE_FIELDS,
  "non_goals",
  "role_permissions",
  "payment",
  "notifications",
  "integrations",
  "media",
  "compliance",
  "visibility_seo",
  "localization",
  "scheduling",
  "platform",
  "data_owner",
  "look",
  "publishing",
  "security_and_a11y",
  "scale",
];

/** A field's value as something a person can type into and read back. */
export function editText(value: unknown, kind: FieldKind): string {
  if (kind === "list") return Array.isArray(value) ? value.join(", ") : String(value ?? "");
  return typeof value === "string" ? value : "";
}

/** …and back, in the shape the api wants. Splitting is the editor's job, not the server's. */
export function toValue(text: string, kind: FieldKind): string | string[] {
  if (kind !== "list") return text.trim();
  return text
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

/** The sensitivity object, read defensively — it is the one structured field. */
export function readSensitivity(value: unknown): {
  owner: string;
  sensitive: boolean;
  kinds: string[];
} {
  const raw = (value ?? {}) as { owner?: unknown; sensitive?: unknown; kinds?: unknown };
  return {
    owner: typeof raw.owner === "string" ? raw.owner : "you",
    sensitive: raw.sensitive === true,
    kinds: Array.isArray(raw.kinds) ? raw.kinds.map(String) : [],
  };
}

/** How far the six core answers have got — the wizard's honest progress. */
export function coreProgress(spec: IntakeSpec): { answered: number; total: number } {
  const answered = CORE_FIELDS.filter((field) => isSpecField(spec[field])).length;
  return { answered, total: CORE_FIELDS.length };
}
