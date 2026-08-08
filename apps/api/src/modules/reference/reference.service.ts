import { Injectable, NotImplementedException } from "@nestjs/common";
import type {
  CreateReferenceAssetRequest,
  ReferenceAssetListResponse,
  ReferenceAssetResponse,
} from "@scio/shared";
import { PrismaService } from "../../prisma/prisma.service";

/**
 * Tagged RAG uploads (4.6). Files land in object storage; embeddings are
 * owned by the Python engine — this service only manages asset metadata.
 * Scoped via project -> workspace_id (tenant-isolated retrieval).
 */
@Injectable()
export class ReferenceService {
  constructor(private readonly prisma: PrismaService) {}

  async list(workspaceId: string, projectId: string): Promise<ReferenceAssetListResponse> {
    // TODO(4.6): workspace-scoped listing.
    throw new NotImplementedException("reference.list — phase 4.6");
  }

  async create(
    workspaceId: string,
    projectId: string,
    body: CreateReferenceAssetRequest,
  ): Promise<ReferenceAssetResponse> {
    // TODO(4.6): issue an upload URL, store pointer + tag, kick extraction.
    throw new NotImplementedException("reference.create — phase 4.6");
  }
}
