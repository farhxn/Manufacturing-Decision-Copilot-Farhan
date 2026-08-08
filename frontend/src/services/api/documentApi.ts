import { apiClient } from '@/lib/api-client';
import { getActiveWorkspaceId } from '@/store/workspaceStore';
import type {
  APIResponse,
  PaginationMeta,
  DocumentUploadResponse,
  DocumentStatusResponse,
  DocumentSummary,
  DocumentChunk,
  DocumentChunkWithMeta,
  JobStatusResponse,
} from '@/types';

export const documentApi = {
  upload: async (
    file: File,
    projectId?: string,
    supplierId?: string,
  ): Promise<DocumentUploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    form.append('project_id', projectId ?? getActiveWorkspaceId());
    if (supplierId) form.append('supplier_id', supplierId);

    const res = await apiClient.post<APIResponse<DocumentUploadResponse>>(
      '/documents/upload',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    if (!res.data) throw new Error('Upload failed');
    return res.data;
  },

  list: async (
    projectId?: string,
    page = 1,
    limit = 20,
  ): Promise<{ data: DocumentSummary[]; meta: PaginationMeta }> => {
    const res = await apiClient.get<APIResponse<DocumentSummary[]>>('/documents', {
      params: { project_id: projectId ?? getActiveWorkspaceId(), page, limit },
    });
    return {
      data: res.data ?? [],
      meta: res.meta ?? { page, limit, total: 0, total_pages: 0 },
    };
  },

  getStatus: async (documentId: string): Promise<DocumentStatusResponse> => {
    const res = await apiClient.get<APIResponse<DocumentStatusResponse>>(
      `/documents/${documentId}`,
    );
    if (!res.data) throw new Error('Document not found');
    return res.data;
  },

  getChunks: async (documentId: string): Promise<DocumentChunk[]> => {
    const res = await apiClient.get<APIResponse<DocumentChunk[]>>(
      `/documents/${documentId}/chunks`,
    );
    return res.data ?? [];
  },

  getVerificationQueue: async (
    projectId?: string,
    limit = 50,
  ): Promise<DocumentChunkWithMeta[]> => {
    const res = await apiClient.get<APIResponse<DocumentChunkWithMeta[]>>(
      '/documents/claims/queue',
      {
        params: { project_id: projectId ?? getActiveWorkspaceId(), limit },
      },
    );
    return res.data ?? [];
  },

  pollJob: async (jobId: string, documentId: string): Promise<JobStatusResponse> => {
    const res = await apiClient.get<APIResponse<JobStatusResponse>>(`/jobs/${jobId}`, {
      params: { document_id: documentId },
    });
    if (!res.data) throw new Error('Job not found');
    return res.data;
  },

  delete: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/documents/${documentId}`);
  },
};
