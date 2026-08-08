import { apiClient } from '@/lib/api-client';
import type { APIResponse, Recommendation } from '@/types';
import { getActiveWorkspaceId } from '@/store/workspaceStore';

export const recommendationApi = {
  get: async (projectId?: string): Promise<Recommendation> => {
    const res = await apiClient.get<APIResponse<Recommendation>>('/recommendations', {
      params: { project_id: projectId ?? getActiveWorkspaceId() },
    });
    if (!res.data) throw new Error('No recommendation found');
    return res.data;
  },

  regenerate: async (projectId?: string): Promise<Recommendation> => {
    const res = await apiClient.post<APIResponse<Recommendation>>(
      '/recommendations/regenerate',
      null,
      { params: { project_id: projectId ?? getActiveWorkspaceId() } },
    );
    if (!res.data) throw new Error('Regeneration failed');
    return res.data;
  },
};
