from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    vector_store: Dict[str, Any]
    embedding_provider: str
    llm_configured: bool
    timestamp: datetime
