import { apiFetch } from './client';
import { DocumentItem, DocumentListResponse, DocumentStatusResponse } from '../types/document';

export const documentsApi = {
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiFetch<DocumentItem>('documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  listDocuments: () => apiFetch<DocumentListResponse>('documents', { method: 'GET' }),

  getDocument: (id: string) => apiFetch<DocumentItem>(`documents/${id}`, { method: 'GET' }),

  getDocumentStatus: (id: string) =>
    apiFetch<DocumentStatusResponse>(`documents/${id}/status`, { method: 'GET' }),

  deleteDocument: (id: string) =>
    apiFetch<{ message: string; document_id: string }>(`documents/${id}`, {
      method: 'DELETE',
    }),
};
