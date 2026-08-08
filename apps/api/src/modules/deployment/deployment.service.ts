import { Injectable, NotImplementedException } from "@nestjs/common";
import type {
  CreateDeploymentRequest,
  DeploymentListResponse,
  DeploymentResponse,
} from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/** Publish targets (scio_url | own_infra). Scoped via project -> workspace_id. */
@Injectable()
export class DeploymentService {
  constructor(private readonly prisma: PrismaService) {}

  async list(workspaceId: string, projectId: string): Promise<DeploymentListResponse> {
    // TODO(8): workspace-scoped listing.
    throw new NotImplementedException("deployment.list — phase 8");
  }

  async create(workspaceId: string, projectId: string, body: CreateDeploymentRequest): Promise<DeploymentResponse> {
    // TODO(8): publish a build version; honest status travels with the deployment.
    throw new NotImplementedException("deployment.create — phase 8");
  }
}
