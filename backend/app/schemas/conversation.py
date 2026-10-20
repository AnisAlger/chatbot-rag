from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int
    chunk_id: str
    excerpt: str


class RetrievalMeta(BaseModel):
    chunks_used: int


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=150)
    selected_document_ids: Optional[List[str]] = Field(default_factory=list)


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    selected_document_ids: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000, description="User question or prompt")
    selected_document_ids: Optional[List[str]] = Field(None, description="Optional override of documents to query")


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    retrieval_meta: Optional[RetrievalMeta] = None
    created_at: datetime


class ConversationSummaryResponse(BaseModel):
    id: str
    title: str
    selected_document_ids: List[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    selected_document_ids: List[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]


class ChatAnswerResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: List[Citation]
    retrieval: RetrievalMeta
