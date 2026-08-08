-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- CreateEnum
CREATE TYPE "Plan" AS ENUM ('starter', 'builder', 'team');

-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('owner', 'member');

-- CreateEnum
CREATE TYPE "ProjectType" AS ENUM ('app', 'website', 'automation');

-- CreateEnum
CREATE TYPE "ProjectStatus" AS ENUM ('draft', 'building', 'ready', 'error');

-- CreateEnum
CREATE TYPE "MessageRole" AS ENUM ('user', 'scio');

-- CreateEnum
CREATE TYPE "DeploymentTarget" AS ENUM ('scio_url', 'own_infra');

-- CreateEnum
CREATE TYPE "DeploymentStatus" AS ENUM ('pending', 'live', 'failed');

-- CreateEnum
CREATE TYPE "ReferenceKind" AS ENUM ('color', 'font', 'layout', 'document', 'brand', 'other');

-- CreateEnum
CREATE TYPE "UsageKind" AS ENUM ('generation', 'critique', 'sandbox', 'storage', 'other');

-- CreateEnum
CREATE TYPE "NotificationKind" AS ENUM ('build_done', 'needs_look', 'limit', 'cost', 'update');

-- CreateTable
CREATE TABLE "workspace" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "plan" "Plan" NOT NULL DEFAULT 'starter',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "workspace_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user" (
    "id" UUID NOT NULL,
    "clerk_user_id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "workspace_id" UUID NOT NULL,
    "role" "UserRole" NOT NULL DEFAULT 'owner',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "project" (
    "id" UUID NOT NULL,
    "workspace_id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "type" "ProjectType" NOT NULL DEFAULT 'app',
    "status" "ProjectStatus" NOT NULL DEFAULT 'draft',
    "deleted_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "message" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "role" "MessageRole" NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "message_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "spec_version" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "number" INTEGER NOT NULL,
    "content" JSONB NOT NULL,
    "assumptions" JSONB NOT NULL,
    "is_current" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "spec_version_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "design_version" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "number" INTEGER NOT NULL,
    "ref" TEXT NOT NULL,
    "is_current" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "design_version_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "build_version" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "number" INTEGER NOT NULL,
    "description" TEXT NOT NULL,
    "git_sha" TEXT NOT NULL,
    "honest_status" JSONB NOT NULL,
    "spec_version_id" UUID NOT NULL,
    "design_version_id" UUID,
    "is_current" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "build_version_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "deployment" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "build_version_id" UUID NOT NULL,
    "target" "DeploymentTarget" NOT NULL,
    "url" TEXT,
    "status" "DeploymentStatus" NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "deployment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "reference_asset" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "kind" "ReferenceKind" NOT NULL,
    "filename" TEXT NOT NULL,
    "storage_url" TEXT NOT NULL,
    "extracted" JSONB NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "reference_asset_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "reference_embedding" (
    "id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "asset_id" UUID NOT NULL,
    "chunk" TEXT NOT NULL,
    "embedding" vector,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "reference_embedding_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "usage_event" (
    "id" UUID NOT NULL,
    "workspace_id" UUID NOT NULL,
    "project_id" UUID,
    "kind" "UsageKind" NOT NULL,
    "model" TEXT,
    "amount" DECIMAL(65,30) NOT NULL,
    "cost" DECIMAL(65,30) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "usage_event_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "notification" (
    "id" UUID NOT NULL,
    "workspace_id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "kind" "NotificationKind" NOT NULL,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "read" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_log" (
    "id" UUID NOT NULL,
    "workspace_id" UUID NOT NULL,
    "actor" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "target" TEXT NOT NULL,
    "metadata" JSONB NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_log_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "user_clerk_user_id_key" ON "user"("clerk_user_id");

-- CreateIndex
CREATE UNIQUE INDEX "spec_version_project_id_number_key" ON "spec_version"("project_id", "number");

-- CreateIndex
CREATE UNIQUE INDEX "design_version_project_id_number_key" ON "design_version"("project_id", "number");

-- CreateIndex
CREATE UNIQUE INDEX "build_version_project_id_number_key" ON "build_version"("project_id", "number");

-- AddForeignKey
ALTER TABLE "user" ADD CONSTRAINT "user_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "workspace"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project" ADD CONSTRAINT "project_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "workspace"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "message" ADD CONSTRAINT "message_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "spec_version" ADD CONSTRAINT "spec_version_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "design_version" ADD CONSTRAINT "design_version_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "build_version" ADD CONSTRAINT "build_version_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "build_version" ADD CONSTRAINT "build_version_spec_version_id_fkey" FOREIGN KEY ("spec_version_id") REFERENCES "spec_version"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "build_version" ADD CONSTRAINT "build_version_design_version_id_fkey" FOREIGN KEY ("design_version_id") REFERENCES "design_version"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "deployment" ADD CONSTRAINT "deployment_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "deployment" ADD CONSTRAINT "deployment_build_version_id_fkey" FOREIGN KEY ("build_version_id") REFERENCES "build_version"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reference_asset" ADD CONSTRAINT "reference_asset_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reference_embedding" ADD CONSTRAINT "reference_embedding_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reference_embedding" ADD CONSTRAINT "reference_embedding_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "reference_asset"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "usage_event" ADD CONSTRAINT "usage_event_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "workspace"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "usage_event" ADD CONSTRAINT "usage_event_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "project"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notification" ADD CONSTRAINT "notification_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "workspace"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notification" ADD CONSTRAINT "notification_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "user"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "audit_log" ADD CONSTRAINT "audit_log_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "workspace"("id") ON DELETE RESTRICT ON UPDATE CASCADE;


-- The vector index (hnsw/ivfflat) on reference_embedding.embedding is added once the
-- Python engine fixes the embedding dimensionality, e.g.:
--   CREATE INDEX reference_embedding_hnsw ON reference_embedding
--     USING hnsw ((embedding::vector(1536)) vector_cosine_ops);
