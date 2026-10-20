export interface DocumentItem {
  id: string;
  owner_id: string;
  filename: string;
  file_size_bytes: number;
  page_count: number;
  status: 'uploaded' | 'processing' | 'indexed' | 'failed' | string;
  chunk_count: number;
  error_message?: string | null;
  uploaded_at: string;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  total: number;
}

export interface DocumentStatusResponse {
  id: string;
  status: string;
  page_count: number;
  chunk_count: number;
  error_message?: string | null;
}
