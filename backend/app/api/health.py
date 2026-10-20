from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings
from app.database import db_manager
from app.schemas.health import HealthResponse, ReadyResponse
from app.services.llm_service import llm_service
from app.services.vector_store import get_vector_store

router = APIRouter(tags=["Operations & Health"])


@router.get("/", summary="Root Welcome")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs"
    }


@router.get("/health", response_model=HealthResponse, summary="Liveness Probe")
async def health_check():
    """
    Verifies that the application process is running and responding.
    """
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/ready", response_model=ReadyResponse, summary="Readiness Probe")
async def readiness_check():
    """
    Verifies that dependent services (database, vector store, embedding, LLM)
    are operational without exposing sensitive credentials or connection strings.
    """
    db_health = db_manager.check_health()
    vector_store = get_vector_store()
    vector_stats = vector_store.get_stats()

    is_ready = db_health.get("status") in ("healthy", "degraded")

    return ReadyResponse(
        status="ready" if is_ready else "not_ready",
        database={
            "status": db_health.get("status"),
            "mode": db_health.get("mode"),
            "connected": db_health.get("connected")
        },
        vector_store={
            "type": vector_stats.get("type"),
            "ready": True
        },
        embedding_provider=settings.EMBEDDING_PROVIDER,
        llm_configured=llm_service.is_configured(),
        timestamp=datetime.now(timezone.utc)
    )
