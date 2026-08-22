/**
 * Request/response DTOs for the Scio API contract.
 * Skeleton stage: shapes only — validation and business logic land in phases 3.3+.
 */

import type {
  BuildVersion,
  Deployment,
  DeploymentTarget,
  DesignVersion,
  HonestStatus,
  Notification,
  Project,
  ProjectStatus,
  ProjectType,
  ReferenceAsset,
  ReferenceKind,
  SpecVersion,
  UsageEvent,
  User,
  Workspace,
} from "./entities";

// health
export interface HealthResponse {
  status: "ok";
  db: "connected" | "not_configured" | "error";
  timestamp: string;
}

// workspace
export interface WorkspaceResponse {
  workspace: Workspace;
}

// user
export interface MeResponse {
  user: User;
  workspace: Workspace;
}

// auth (stub — real Clerk integration is phase 3.3)
export interface AuthStatusResponse {
  authenticated: boolean;
  userId: string | null;
}

// project
export interface CreateProjectRequest {
  name: string;
  type?: ProjectType;
}
export interface UpdateProjectRequest {
  name?: string;
  status?: ProjectStatus;
}
export interface ProjectResponse {
  project: Project;
}
export interface ProjectListResponse {
  projects: Project[];
}

// spec
export interface FreezeSpecRequest {
  content: Record<string, unknown>;
  assumptions: Record<string, unknown>;
}
export interface SpecVersionResponse {
  specVersion: SpecVersion;
}
export interface SpecVersionListResponse {
  specVersions: SpecVersion[];
}

/**
 * A deliberate, recorded change to the approved spec, made from the design
 * window because a marking argued with it.
 *
 * Two shapes, because dropping a non-goal and dropping a protection are not the
 * same act: `non_goal` removes the thing the spec excluded, while `auth` and
 * `access` leave the security posture alone and record an ALLOWANCE — the exact
 * sentence the user was asked about and said yes to. The posture still says the
 * data is sensitive; the record says what was permitted anyway, and by whom.
 */
export interface AmendSpecRequest {
  kind: "non_goal" | "auth" | "access";
  /** The exact sentence the conflict quoted. Only that sentence is affected. */
  specSays: string;
  /** What the user had marked when they were asked. Kept for the record. */
  note?: string;
}

export interface AmendSpecResponse {
  specVersion: {
    id: string;
    number: number;
    isCurrent: boolean;
    createdAt: string;
  };
  /** Every allowance now on the spec — what the engine is told to stop asking about. */
  allowances: string[];
  /** The non-goal that was dropped, if this was that kind of amendment. */
  removedNonGoal: string | null;
}

// design (Level 2 — the design window)

/** One element the user marked, exactly as the in-preview bridge reports it.
 *  `ancestorId` is evidence for a refusal, never a fallback target. */
export interface DesignMarking {
  scioId: string | null;
  scioPackage?: string | null;
  tag?: string;
  text?: string;
  ancestorId?: string | null;
  ancestorPackage?: string | null;
  ancestorDistance?: number;
  note?: string;
}

/** Everything marked before pressing go, plus whatever was typed for the change
 *  as a whole. One change, several targets. */
export interface ApplyDesignChangeRequest {
  markings: DesignMarking[];
  prompt?: string;
}

/** A marking that argues with the approved spec. Returned as a question — the
 *  change is NOT applied until the user decides. */
export interface DesignConflict {
  kind: string;
  scioId: string;
  note: string;
  specSays: string;
  question: string;
}

/** What happened to one package. `unchangedFiles` is the isolation proof. */
export interface DesignPackageChange {
  package: string;
  editedFiles: string[];
  unchangedFiles: number;
  isolated: boolean;
  accepted: boolean;
  rejection: string;
}

/** A marking that could not be addressed, and why. */
export interface DesignSkippedMarking {
  scioId: string | null;
  note: string;
  error: string;
}

export interface DesignPreviewResponse {
  previewUrl: string | null;
  /** id -> package + source location. The design window resolves markings against it. */
  manifest: Record<string, unknown> | null;
  designVersion: DesignVersion | null;
  whole: string | null;
  summary: string;
  /** Every page the app has. Without it the window shows whichever one the app
   *  opens on and offers no way to reach the others (B069). */
  routes?: string[];
}

export interface ApplyDesignChangeResponse {
  applied: boolean;
  conflicts: DesignConflict[];
  packages: DesignPackageChange[];
  skipped: DesignSkippedMarking[];
  previewUrl: string | null;
  manifest: Record<string, unknown> | null;
  designVersion: DesignVersion | null;
  summary: string;
}

/**
 * What a design version's `ref` holds, as JSON.
 *
 * It is a *pointer to a preview*, not a copy of one: where the app is on disk,
 * where it is running, the manifest markings resolve against, and the commit to
 * check out to come back here. `gitSha` empty means the change landed on disk
 * but could not be committed — so this version can be read, and not returned to.
 */
export interface DesignVersionRef {
  workspace?: string;
  previewUrl?: string;
  manifest?: Record<string, unknown> | null;
  packageFiles?: Record<string, string[]>;
  summary?: string;
  whole?: string;
  /** What the user asked for, in their own words. */
  change?: string;
  gitSha?: string;
}

/** Returning to an earlier design version. Never a 500 for "that one cannot be
 *  restored" — the reason is the answer. */
export interface RestoreDesignVersionResponse {
  restored: boolean;
  previewUrl: string | null;
  manifest: Record<string, unknown> | null;
  designVersion: DesignVersion | null;
  error: string;
}

export interface FreezeDesignRequest {
  ref: string;
}
export interface DesignVersionResponse {
  designVersion: DesignVersion;
}
export interface DesignVersionListResponse {
  designVersions: DesignVersion[];
}

// build
export interface CreateBuildRequest {
  specVersionId: string;
  designVersionId?: string;
}
export interface BuildVersionResponse {
  buildVersion: BuildVersion;
}
export interface BuildVersionListResponse {
  buildVersions: BuildVersion[];
}
export interface RestoreBuildRequest {
  /** Restore is non-destructive: creates a new version pointing at this one's git_sha. */
  buildVersionId: string;
}
export type BuildHonestStatus = HonestStatus;

// deployment
export interface CreateDeploymentRequest {
  buildVersionId: string;
  target: DeploymentTarget;
}
export interface DeploymentResponse {
  deployment: Deployment;
}
export interface DeploymentListResponse {
  deployments: Deployment[];
}

// reference (tagged RAG uploads)
export interface CreateReferenceAssetRequest {
  kind: ReferenceKind;
  filename: string;
}
export interface ReferenceAssetResponse {
  referenceAsset: ReferenceAsset;
}
export interface ReferenceAssetListResponse {
  referenceAssets: ReferenceAsset[];
}

// usage
export interface UsageListResponse {
  usageEvents: UsageEvent[];
}

// notification
export interface NotificationListResponse {
  notifications: Notification[];
}
export interface MarkNotificationReadRequest {
  read: boolean;
}

// streaming (SSE) — event names for later engine output
export type StreamEventName =
  | "engine.pass"
  | "build.progress"
  | "build.done"
  | "build.needs_look";
export interface StreamEvent<T = unknown> {
  event: StreamEventName;
  data: T;
}
