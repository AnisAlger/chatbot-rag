import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    Validates all required parameters at startup.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Intelligent RAG Chatbot API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "default-insecure-secret-key-change-in-prod"
    
    # JWT & Auth
    JWT_SECRET_KEY: str = "default-insecure-jwt-secret-key-min-32-chars-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "chatbot_rag"
    MONGODB_TIMEOUT_MS: int = 4000

    # OpenRouter LLM
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_CHAT_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Embedding Provider ("openrouter", "openai", "local_mock")
    EMBEDDING_PROVIDER: str = "local_mock"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://openrouter.ai/api/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vector Store ("local" or "atlas")
    VECTOR_STORE_TYPE: str = "local"
    LOCAL_VECTOR_STORE_PATH: str = "./data/vector_store"
    MONGODB_VECTOR_INDEX_NAME: str = "rag_vector_index"

    # File uploads & Chunking
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_MB: int = 10
    CHUNK_SIZE: int = 350
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5

    # CORS
    FRONTEND_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


settings = Settings()
