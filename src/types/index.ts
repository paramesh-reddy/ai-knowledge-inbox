export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type FileType = 'pdf' | 'txt' | 'md' | 'note';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  extracted_text: string;
  page_number?: number | null;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  title: string;
  original_filename: string;
  file_type: FileType;
  file_size: number;
  processing_status: DocumentStatus;
  error_message?: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentItem {
  raw_content_preview?: string | null;
  chunks: DocumentChunk[];
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProcessingJobItem {
  id: string;
  document_id: string;
  document_title?: string | null;
  job_type: string;
  status: JobStatus;
  attempt_count: number;
  max_attempts: number;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  heartbeat_at?: string | null;
}

export interface JobListResponse {
  items: ProcessingJobItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CitationItem {
  document_id: string;
  document_title: string;
  chunk_id: string;
  excerpt: string;
  page_number?: number | null;
  similarity_score?: number | null;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: CitationItem[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
}

export interface AskQuestionResponse {
  session_id: string;
  user_message_id: string;
  assistant_message_id: string;
  answer: string;
  citations: CitationItem[];
  has_evidence: boolean;
}

export interface DashboardStats {
  total_documents: number;
  completed_documents: number;
  processing_documents: number;
  failed_documents: number;
  pending_documents: number;
  total_chunks: number;
  total_jobs: number;
  recent_documents: DocumentItem[];
  recent_jobs: ProcessingJobItem[];
}

export interface HealthInfo {
  status: string;
  app_name: string;
  app_env: string;
  timestamp: string;
  database_connected: boolean;
  database_type: string;
  gemini_configured: boolean;
  configured_model: string;
  configured_embedding_model: string;
  embedding_dimensions: number;
  worker_status: string;
}
