import { apiClient } from '@/lib/api-client';
import type { APIResponse, EvidenceList } from '@/types';

export const evidenceApi = {
  getByRecommendation: async (recommendationId: string): Promise<EvidenceList> => {
    const res = await apiClient.get<APIResponse<EvidenceList>>(
      `/evidence/${recommendationId}`,
    );
    return res.data ?? { recommendation_id: recommendationId, items: [] };
  },
};
