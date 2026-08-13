-- AlterEnum
ALTER TYPE "ProjectStatus" ADD VALUE 'spec_locked';

-- AlterTable
ALTER TABLE "project" ADD COLUMN     "draft_spec" JSONB;

