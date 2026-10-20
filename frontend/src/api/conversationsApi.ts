import { apiFetch } from './client';
import {
  ChatAnswerResponse,
  ConversationDetail,
  ConversationSummary,
} from '../types/conversation';

export const conversationsApi = {
  listConversations: () =>
    apiFetch<ConversationSummary[]>('conversations', { method: 'GET' }),

  getConversation: (id: string) =>
    apiFetch<ConversationDetail>(`conversations/${id}`, { method: 'GET' }),

  createConversation: (payload: { title?: string; selected_document_ids?: string[] }) =>
    apiFetch<ConversationDetail>('conversations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateConversation: (
    id: string,
    payload: { title?: string; selected_document_ids?: string[] }
  ) =>
    apiFetch<ConversationSummary>(`conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deleteConversation: (id: string) =>
    apiFetch<{ message: string; conversation_id: string }>(`conversations/${id}`, {
      method: 'DELETE',
    }),

  sendMessage: (
    conversationId: string,
    payload: { content: string; selected_document_ids?: string[] }
  ) =>
    apiFetch<ChatAnswerResponse>(`conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
