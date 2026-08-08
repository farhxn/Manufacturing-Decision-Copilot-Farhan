import { apiClient } from '@/lib/api-client';
import type { APIResponse, ScenarioSummary, ScenarioSimulation, ScenarioCreateRequest } from '@/types';
import { getActiveWorkspaceId } from '@/store/workspaceStore';

export const scenarioApi = {
  list: async (projectId?: string): Promise<ScenarioSummary[]> => {
    const res = await apiClient.get<APIResponse<ScenarioSummary[]>>('/scenarios', {
      params: { project_id: projectId ?? getActiveWorkspaceId() },
    });
    return res.data ?? [];
  },

  create: async (payload: Omit<ScenarioCreateRequest, 'project_id'> & { project_id?: string }): Promise<ScenarioSummary> => {
    const data = { ...payload, project_id: payload.project_id ?? getActiveWorkspaceId() };
    const res = await apiClient.post<APIResponse<ScenarioSummary>>('/scenarios', data);
    if (!res.data) throw new Error('Scenario creation failed');
    return res.data;
  },

  getById: async (scenarioId: string): Promise<ScenarioSummary> => {
    const res = await apiClient.get<APIResponse<ScenarioSummary>>(`/scenarios/${scenarioId}`);
    if (!res.data) throw new Error('Scenario not found');
    return res.data;
  },

  simulate: async (scenarioId: string): Promise<ScenarioSimulation> => {
    const res = await apiClient.post<APIResponse<ScenarioSimulation>>(
      `/scenarios/${scenarioId}/simulate`,
    );
    if (!res.data) throw new Error('Simulation failed');
    return res.data;
  },

  delete: async (scenarioId: string): Promise<void> => {
    await apiClient.delete(`/scenarios/${scenarioId}`);
  },
};
