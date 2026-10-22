import {
  DocumentListResponse,
  DocumentDetail,
  DocumentItem,
  JobListResponse,
  ProcessingJobItem,
  DashboardStats,
  HealthInfo,
  AskQuestionResponse,
  ChatSession,
  ChatMessage,
  FileType,
  DocumentStatus,
  JobStatus,
} from '../types';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Use fallback errorDetail
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Health & Stats
  async getHealth(): Promise<HealthInfo> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse<HealthInfo>(res);
  },

  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${BASE_URL}/dashboard/stats`);
    return handleResponse<DashboardStats>(res);
  },

  // Documents
  async getDocuments(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    fileType?: FileType | '';
    status?: DocumentStatus | '';
  }): Promise<DocumentListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', String(params.page));
    if (params?.pageSize) query.append('page_size', String(params.pageSize));
    if (params?.search) query.append('search', params.search);
    if (params?.fileType) query.append('file_type', params.fileType);
    if (params?.status) query.append('status', params.status);

    const res = await fetch(`${BASE_URL}/documents?${query.toString()}`);
    return handleResponse<DocumentListResponse>(res);
  },

  async getDocument(id: string): Promise<DocumentDetail> {
    const res = await fetch(`${BASE_URL}/documents/${id}`);
    return handleResponse<DocumentDetail>(res);
  },

  async getDocumentContent(id: string): Promise<string> {
    const res = await fetch(`${BASE_URL}/documents/${id}/content`);
    if (!res.ok) throw new Error('Failed to fetch document content');
    return res.text();
  },

  async uploadFile(file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DocumentItem>(res);
  },

  async createNote(title: string, content: string): Promise<DocumentItem> {
    const res = await fetch(`${BASE_URL}/documents/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    return handleResponse<DocumentItem>(res);
  },

  async retryDocument(id: string): Promise<DocumentItem> {
    const res = await fetch(`${BASE_URL}/documents/${id}/retry`, {
      method: 'POST',
    });
    return handleResponse<DocumentItem>(res);
  },

  async deleteDocument(id: string): Promise<{ message: string; document_id: string }> {
    const res = await fetch(`${BASE_URL}/documents/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<{ message: string; document_id: string }>(res);
  },

  // Jobs
  async getJobs(params?: {
    page?: number;
    pageSize?: number;
    status?: JobStatus | '';
  }): Promise<JobListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', String(params.page));
    if (params?.pageSize) query.append('page_size', String(params.pageSize));
    if (params?.status) query.append('status', params.status);

    const res = await fetch(`${BASE_URL}/jobs?${query.toString()}`);
    return handleResponse<JobListResponse>(res);
  },

  async getJob(id: string): Promise<ProcessingJobItem> {
    const res = await fetch(`${BASE_URL}/jobs/${id}`);
    return handleResponse<ProcessingJobItem>(res);
  },

  // Chat & RAG
  async askQuestion(
    question: string,
    sessionId?: string | null,
    topK?: number
  ): Promise<AskQuestionResponse> {
    const res = await fetch(`${BASE_URL}/chat/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        session_id: sessionId || null,
        top_k: topK || null,
      }),
    });
    return handleResponse<AskQuestionResponse>(res);
  },

  async getChatSessions(): Promise<ChatSession[]> {
    const res = await fetch(`${BASE_URL}/chat/sessions`);
    return handleResponse<ChatSession[]>(res);
  },

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    const res = await fetch(`${BASE_URL}/chat/sessions/${sessionId}/messages`);
    return handleResponse<ChatMessage[]>(res);
  },
};
