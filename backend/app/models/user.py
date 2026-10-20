from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserInDB(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }
