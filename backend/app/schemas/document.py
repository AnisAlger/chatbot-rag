from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    owner_id: str
    filename: str
    file_size_bytes: int
    page_count: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    uploaded_at: datetime


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    page_count: int
    chunk_count: int
    error_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
