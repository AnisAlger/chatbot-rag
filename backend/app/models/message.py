from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageInDB(BaseModel):
    id: str
    conversation_id: str
    owner_id: str
    role: str  # "user" or "assistant"
    content: str
    citations: Optional[List[Dict[str, Any]]] = None
    retrieval_meta: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "conversation_id": self.conversation_id,
            "owner_id": self.owner_id,
            "role": self.role,
            "content": self.content,
            "citations": self.citations,
            "retrieval_meta": self.retrieval_meta,
            "created_at": self.created_at.isoformat()
        }
