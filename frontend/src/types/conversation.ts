export interface Citation {
  document_id: string;
  filename: string;
  page: number;
  chunk_id: string;
  excerpt: string;
}

export interface RetrievalMeta {
  chunks_used: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[] | null;
  retrieval_meta?: RetrievalMeta | null;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  selected_document_ids: string[];
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationDetail {
  id: string;
  title: string;
  selected_document_ids: string[];
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatAnswerResponse {
  conversation_id: string;
  answer: string;
  citations: Citation[];
  retrieval: RetrievalMeta;
}
