import type { SupplierScore } from './supplier';

export interface RankedSupplier {
  supplier_id: string;
  supplier_name: string;
  country: string;
  rank: number;
  final_score: number;
  lead_time_days: number;
  scores: SupplierScore;
  citations: Record<string, { document_id?: string | null, source_document: string, page_number: number, chunk_text: string }>;
}

export interface Recommendation {
  id: string | null;
  project_id: string;
  recommended_supplier_id: string;
  recommended_supplier_name: string;
  summary: string;
  confidence_score: number;
  confidence_label: 'Low' | 'Medium' | 'High';
  confidence_explanation: string;
  ranking: RankedSupplier[];
  pros: string[];
  pros_citations: { document_id?: string | null, source_document: string, page_number: number, chunk_text: string }[];
  cons: string[];
  tradeoffs: string[];
  risks: string[];
  assumptions: string[];
  limitations: string[];
  next_actions: string[];
  evidence_ids: string[];
  ai_narrative: boolean;
}
