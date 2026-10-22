"""Processing Jobs API endpoints."""
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.dependencies import get_job_repo
from app.db.models.job import JobStatus
from app.db.repositories.job_repo import JobRepository
from app.db.schemas.job import JobResponse, JobListResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    job_repo: JobRepository = Depends(get_job_repo),
):
    """Lists background processing jobs with pagination and status filters."""
    items, total = await job_repo.list_jobs(page=page, page_size=page_size, status=status)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return JobListResponse(
        items=[
            JobResponse(
                id=j.id,
                document_id=j.document_id,
                document_title=j.document.title if j.document else None,
                job_type=j.job_type,
                status=j.status,
                attempt_count=j.attempt_count,
                max_attempts=j.max_attempts,
                error_message=j.error_message,
                created_at=j.created_at,
                started_at=j.started_at,
                finished_at=j.finished_at,
                heartbeat_at=j.heartbeat_at,
            )
            for j in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    job_repo: JobRepository = Depends(get_job_repo),
):
    """Retrieves specific background job details."""
    j = await job_repo.get_by_id(job_id)
    if not j:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    return JobResponse(
        id=j.id,
        document_id=j.document_id,
        document_title=j.document.title if j.document else None,
        job_type=j.job_type,
        status=j.status,
        attempt_count=j.attempt_count,
        max_attempts=j.max_attempts,
        error_message=j.error_message,
        created_at=j.created_at,
        started_at=j.started_at,
        finished_at=j.finished_at,
        heartbeat_at=j.heartbeat_at,
    )
