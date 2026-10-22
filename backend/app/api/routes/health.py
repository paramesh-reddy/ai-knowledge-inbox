"""Health and diagnostic API routes."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.db.schemas.stats import HealthResponse
from app.services.embedding_service import EmbeddingService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health(session: AsyncSession = Depends(get_db)):
    """System health endpoint reporting database connectivity, AI status, and model config."""
    db_connected = False
    try:
        await session.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    embedding_svc = EmbeddingService()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        app_name=settings.app_name,
        app_env=settings.app_env,
        timestamp=datetime.now(timezone.utc),
        database_connected=db_connected,
        database_type="PostgreSQL (pgvector)" if settings.is_postgres else "SQLite (Vector Engine)",
        gemini_configured=embedding_svc.is_configured,
        configured_model=settings.gemini_model,
        configured_embedding_model=settings.gemini_embedding_model,
        embedding_dimensions=settings.embedding_dimensions,
        worker_status="active",
    )
