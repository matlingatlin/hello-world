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
  type: ProjectType;
}
export interface UpdateProjectRequest {
  name?: string;
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

// design
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
