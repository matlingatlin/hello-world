/**
 * Entity types mirroring docs/DATA-MODEL.md (ADR-0009).
 * All app data is scoped by workspaceId — the tenant boundary.
 */

export type Plan = "starter" | "builder" | "team";
export type UserRole = "owner" | "member";
export type ProjectType = "app" | "website" | "automation";
export type ProjectStatus = "draft" | "spec_locked" | "building" | "ready" | "error";
export type MessageRole = "user" | "scio";
export type DeploymentTarget = "scio_url" | "own_infra";
export type DeploymentStatus = "pending" | "live" | "failed";
export type ReferenceKind = "color" | "font" | "layout" | "document" | "brand" | "other";
export type UsageKind = "generation" | "critique" | "sandbox" | "storage" | "other";
export type NotificationKind = "build_done" | "needs_look" | "limit" | "cost" | "update";

export interface Workspace {
  id: string;
  name: string;
  plan: Plan;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  clerkUserId: string;
  email: string;
  workspaceId: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export interface Project {
  id: string;
  workspaceId: string;
  name: string;
  type: ProjectType;
  status: ProjectStatus;
  deletedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  projectId: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

/** Frozen spec/whole contract. */
export interface SpecVersion {
  id: string;
  projectId: string;
  number: number;
  content: Record<string, unknown>;
  assumptions: Record<string, unknown>;
  isCurrent: boolean;
  createdAt: string;
}

/** Approved design contract (Level 2). */
export interface DesignVersion {
  id: string;
  projectId: string;
  number: number;
  ref: string;
  isCurrent: boolean;
  createdAt: string;
}

/** Honest status shown at reveal: what works, what needs a look. */
export interface HonestStatus {
  passed: number;
  needsLook: string[];
}

/** The version timeline. Content lives in git (gitSha); restore inserts a new row. */
export interface BuildVersion {
  id: string;
  projectId: string;
  number: number;
  description: string;
  gitSha: string;
  honestStatus: HonestStatus;
  specVersionId: string;
  designVersionId: string | null;
  isCurrent: boolean;
  createdAt: string;
}

export interface Deployment {
  id: string;
  projectId: string;
  buildVersionId: string;
  target: DeploymentTarget;
  url: string | null;
  status: DeploymentStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ReferenceAsset {
  id: string;
  projectId: string;
  kind: ReferenceKind;
  filename: string;
  storageUrl: string;
  extracted: Record<string, unknown>;
  createdAt: string;
}

export interface UsageEvent {
  id: string;
  workspaceId: string;
  projectId: string | null;
  kind: UsageKind;
  model: string | null;
  amount: number;
  cost: number;
  createdAt: string;
}

export interface Notification {
  id: string;
  workspaceId: string;
  userId: string;
  kind: NotificationKind;
  title: string;
  body: string;
  read: boolean;
  createdAt: string;
}

export interface AuditLog {
  id: string;
  workspaceId: string;
  actor: string;
  action: string;
  target: string;
  metadata: Record<string, unknown>;
  createdAt: string;
}
