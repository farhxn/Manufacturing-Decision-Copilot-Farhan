import { apiClient } from '@/lib/api-client';
import type { APIResponse, Dashboard } from '@/types';
import { getActiveWorkspaceId } from '@/store/workspaceStore';

export const dashboardApi = {
  get: async (projectId?: string): Promise<Dashboard> => {
    const res = await apiClient.get<APIResponse<Dashboard>>('/dashboard', {
      params: { project_id: projectId ?? getActiveWorkspaceId() },
    });
    if (!res.data) throw new Error('Dashboard data unavailable');
    return res.data;
  },
};
