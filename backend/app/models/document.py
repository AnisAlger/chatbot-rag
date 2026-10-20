from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class DocumentInDB(BaseModel):
    id: str
    owner_id: str
    filename: str
    safe_storage_name: str
    file_path: str
    file_size_bytes: int
    file_hash: str
    page_count: int = 0
    status: str = "uploaded"  # uploaded, processing, indexed, failed
    error_message: Optional[str] = None
    chunk_count: int = 0
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "owner_id": self.owner_id,
            "filename": self.filename,
            "safe_storage_name": self.safe_storage_name,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "file_hash": self.file_hash,
            "page_count": self.page_count,
            "status": self.status,
            "error_message": self.error_message,
            "chunk_count": self.chunk_count,
            "uploaded_at": self.uploaded_at.isoformat()
        }
