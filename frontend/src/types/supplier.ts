export interface SupplierScore {
  cost_score: number;
  quality_score: number;
  delivery_score: number;
  risk_score: number;
  capability_score: number;
  compliance_score: number;
  final_score: number;
  rank: number | null;
  landed_cost: number;
}

export interface SupplierCapability {
  name: string;
  category: string;
  verified: boolean;
}

export interface SupplierCertification {
  name: string;
  issuer: string | null;
  is_valid: boolean;
}

export interface SupplierSummary {
  id: string;
  name: string;
  country: string;
  city: string | null;
  status: string;
  unit_price: number;
  landed_cost: number;
  currency: string;
  lead_time_days: number;
  moq: number;
  risk_level: 'Low' | 'Medium' | 'High';
  scores: SupplierScore;
}

export interface SupplierDetail extends SupplierSummary {
  capabilities: SupplierCapability[];
  certifications: SupplierCertification[];
}

export interface SupplierCompareRequest {
  supplier_ids: string[];
  project_id?: string;
}

export interface SupplierCreateRequest {
  name: string;
  country: string;
  city?: string | null;
  status?: string;
  unit_price: number;
  landed_cost: number;
  currency?: string;
  lead_time_days: number;
  moq: number;
  risk_level?: 'Low' | 'Medium' | 'High';
  project_id?: string;
}

export interface SupplierUpdateRequest extends Partial<SupplierCreateRequest> {}
