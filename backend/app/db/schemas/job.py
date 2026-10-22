"""Job Pydantic schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.db.models.job import JobStatus


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    document_title: Optional[str] = None
    job_type: str
    status: JobStatus
    attempt_count: int
    max_attempts: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    heartbeat_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
