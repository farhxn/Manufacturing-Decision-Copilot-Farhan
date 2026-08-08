export interface ProjectSummary {
  id: string;
  name: string;
  description: string | null;
  status: string;
  organization_id: string;
}

export interface ProjectCreateRequest {
  name: string;
  description?: string;
  status?: string;
}

export interface ProjectUpdateRequest {
  name?: string;
  description?: string;
  status?: string;
}
