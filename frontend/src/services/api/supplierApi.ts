import { apiClient } from '@/lib/api-client';
import type { APIResponse, PaginationMeta, SupplierSummary, SupplierDetail, SupplierCompareRequest, SupplierCreateRequest, SupplierUpdateRequest } from '@/types';
import { getActiveWorkspaceId } from '@/store/workspaceStore';

export interface SupplierListParams {
  project_id?: string;
  page?: number;
  limit?: number;
  search?: string;
  country?: string;
}

export const supplierApi = {
  list: async (params: SupplierListParams = {}): Promise<{ data: SupplierSummary[]; meta: PaginationMeta }> => {
    const res = await apiClient.get<APIResponse<SupplierSummary[]>>('/suppliers', {
      params: { project_id: params.project_id || getActiveWorkspaceId(), page: 1, limit: 20, ...params },
    });
    return {
      data: res.data ?? [],
      meta: res.meta ?? { page: 1, limit: 20, total: 0, total_pages: 0 },
    };
  },

  getById: async (supplierId: string): Promise<SupplierDetail> => {
    const res = await apiClient.get<APIResponse<SupplierDetail>>(`/suppliers/${supplierId}`);
    if (!res.data) throw new Error('Supplier not found');
    return res.data;
  },

  compare: async (supplierIds: string[], projectId?: string): Promise<SupplierDetail[]> => {
    const body: SupplierCompareRequest = {
      supplier_ids: supplierIds,
      project_id: projectId ?? getActiveWorkspaceId(),
    };
    const res = await apiClient.post<APIResponse<SupplierDetail[]>>('/suppliers/compare', body);
    return res.data ?? [];
  },

  create: async (data: SupplierCreateRequest): Promise<SupplierSummary> => {
    const payload = { ...data, project_id: data.project_id || getActiveWorkspaceId() };
    const res = await apiClient.post<APIResponse<SupplierSummary>>('/suppliers', payload);
    if (!res.data) throw new Error('Failed to create supplier');
    return res.data;
  },

  update: async (supplierId: string, data: SupplierUpdateRequest): Promise<SupplierSummary> => {
    const res = await apiClient.patch<APIResponse<SupplierSummary>>(`/suppliers/${supplierId}`, data);
    if (!res.data) throw new Error('Failed to update supplier');
    return res.data;
  },

  delete: async (supplierId: string): Promise<void> => {
    await apiClient.delete<APIResponse<void>>(`/suppliers/${supplierId}`);
  },
};
