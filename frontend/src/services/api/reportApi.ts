import { apiClient } from '@/lib/api-client';
import { getActiveWorkspaceId } from '@/store/workspaceStore';
import type { APIResponse } from '@/types';

export interface ReportSummary {
  id: string;
  title: string;
  report_type: string;
  project_id: string;
  created_at: string;
}

export interface ReportDetail extends ReportSummary {
  summary_text: string;
}

export interface ReportGenerateRequest {
  project_id?: string;
  report_type?: 'executive' | 'risk' | 'technical';
  title?: string | null;
}

export const reportApi = {
  /**
   * Generate and persist a report. Returns full report detail including
   * the plain-text summary_text for in-browser preview.
   */
  generate: async (params: ReportGenerateRequest = {}): Promise<ReportDetail> => {
    const body: ReportGenerateRequest = {
      project_id: getActiveWorkspaceId(),
      report_type: 'executive',
      title: null,
      ...params,
    };
    const res = await apiClient.post<APIResponse<ReportDetail>>('/reports/generate', body);
    if (!res.data) throw new Error('Report generation failed');
    return res.data;
  },

  /**
   * List all saved reports for a project, newest first.
   */
  list: async (projectId?: string, limit = 20): Promise<ReportSummary[]> => {
    const res = await apiClient.get<APIResponse<ReportSummary[]>>('/reports', {
      params: { project_id: projectId ?? getActiveWorkspaceId(), limit },
    });
    return res.data ?? [];
  },

  /**
   * Fetch full report detail for client-side PDF rendering.
   * The backend returns JSON; the browser renders the PDF via @react-pdf/renderer.
   */
  download: async (reportId: string): Promise<ReportDetail> => {
    const res = await apiClient.get<APIResponse<ReportDetail>>(`/reports/${reportId}/download`);
    if (!res.data) throw new Error(`Report ${reportId} not found`);
    return res.data;
  },

  /**
   * Delete a saved report record.
   */
  delete: async (reportId: string): Promise<void> => {
    await apiClient.delete<void>(`/reports/${reportId}`);
  },
};
