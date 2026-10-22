"""Dashboard stats and health schemas."""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.db.schemas.document import DocumentResponse
from app.db.schemas.job import JobResponse


class DashboardStatsResponse(BaseModel):
    total_documents: int
    completed_documents: int
    processing_documents: int
    failed_documents: int
    pending_documents: int
    total_chunks: int
    total_jobs: int
    recent_documents: List[DocumentResponse]
    recent_jobs: List[JobResponse]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_env: str
    timestamp: datetime
    database_connected: bool
    database_type: str
    gemini_configured: bool
    configured_model: str
    configured_embedding_model: str
    embedding_dimensions: int
    worker_status: str
