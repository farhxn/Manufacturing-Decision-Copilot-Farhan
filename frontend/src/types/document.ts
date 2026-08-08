export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: string;
  job_id: string;
}

export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'extracting'
  | 'indexing'
  | 'completed'
  | 'error';

export interface DocumentStatusResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  progress: number;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentSummary {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  chunk_count: number;
  supplier_id: string | null;
  created_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  section_name: string | null;
  content: string;
  token_count: number;
  extraction_confidence: number;
}

export interface DocumentChunkWithMeta extends DocumentChunk {
  document_filename: string;
  created_at: string;
}

export interface JobStatusResponse {
  job_id: string;
  document_id: string;
  status: DocumentStatus | 'pending' | 'failed';
  progress: number;
  detail: string;
  error: string | null;
}
