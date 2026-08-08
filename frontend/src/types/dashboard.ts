import type { Recommendation } from './recommendation';

export interface DashboardKPI {
  supplier_count: number;
  document_count: number;
  average_confidence: number;
  top_supplier_score: number;
}

export interface Dashboard {
  project_id: string;
  project_name: string;
  kpis: DashboardKPI;
  recommendation: Recommendation;
}
