export interface EvidenceItem {
  id: string;
  chunk_id: string;
  document_id: string | null;
  document_filename: string | null;
  snippet: string;
  relevance_score: number;
  page_number: number | null;
}

export interface EvidenceList {
  recommendation_id: string;
  items: EvidenceItem[];
}
