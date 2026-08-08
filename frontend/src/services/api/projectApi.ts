import { apiClient } from '@/lib/api-client';
import type { APIResponse, ProjectSummary, ProjectCreateRequest, ProjectUpdateRequest } from '@/types';

export const projectApi = {
  list: async (): Promise<ProjectSummary[]> => {
    const res = await apiClient.get<APIResponse<ProjectSummary[]>>('/projects');
    return res.data ?? [];
  },

  getById: async (projectId: string): Promise<ProjectSummary> => {
    const res = await apiClient.get<APIResponse<ProjectSummary>>(`/projects/${projectId}`);
    if (!res.data) throw new Error('Project not found');
    return res.data;
  },

  create: async (data: ProjectCreateRequest): Promise<ProjectSummary> => {
    const res = await apiClient.post<APIResponse<ProjectSummary>>('/projects', data);
    if (!res.data) throw new Error('Failed to create project');
    return res.data;
  },

  update: async (projectId: string, data: ProjectUpdateRequest): Promise<ProjectSummary> => {
    const res = await apiClient.patch<APIResponse<ProjectSummary>>(`/projects/${projectId}`, data);
    if (!res.data) throw new Error('Failed to update project');
    return res.data;
  },

  delete: async (projectId: string): Promise<void> => {
    await apiClient.delete<APIResponse<void>>(`/projects/${projectId}`);
  },
};
