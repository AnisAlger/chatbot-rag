from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ConversationInDB(BaseModel):
    id: str
    owner_id: str
    title: str = "New Conversation"
    selected_document_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "selected_document_ids": self.selected_document_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
