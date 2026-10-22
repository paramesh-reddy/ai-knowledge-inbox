"""Job service for queue status queries and statistics."""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.job import ProcessingJob, JobStatus
from app.db.models.document import Document, DocumentStatus
from app.db.models.chunk import DocumentChunk
from app.db.repositories.job_repo import JobRepository
from app.db.schemas.stats import DashboardStatsResponse
from app.db.schemas.job import JobResponse
from app.db.schemas.document import DocumentResponse


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = JobRepository(session)

    async def get_dashboard_stats(self) -> DashboardStatsResponse:
        # Total documents by status
        total_docs = (await self.session.execute(select(func.count(Document.id)))).scalar_one()
        completed_docs = (
            await self.session.execute(
                select(func.count(Document.id)).where(Document.processing_status == DocumentStatus.COMPLETED)
            )
        ).scalar_one()
        processing_docs = (
            await self.session.execute(
                select(func.count(Document.id)).where(Document.processing_status == DocumentStatus.PROCESSING)
            )
        ).scalar_one()
        failed_docs = (
            await self.session.execute(
                select(func.count(Document.id)).where(Document.processing_status == DocumentStatus.FAILED)
            )
        ).scalar_one()
        pending_docs = (
            await self.session.execute(
                select(func.count(Document.id)).where(Document.processing_status == DocumentStatus.PENDING)
            )
        ).scalar_one()

        total_chunks = (await self.session.execute(select(func.count(DocumentChunk.id)))).scalar_one()
        total_jobs = (await self.session.execute(select(func.count(ProcessingJob.id)))).scalar_one()

        # Recent documents
        recent_docs_stmt = (
            select(Document).order_by(Document.created_at.desc()).limit(5)
        )
        recent_docs = (await self.session.execute(recent_docs_stmt)).scalars().all()

        # Recent jobs
        recent_jobs_stmt = (
            select(ProcessingJob).order_by(ProcessingJob.created_at.desc()).limit(5)
        )
        recent_jobs = (await self.session.execute(recent_jobs_stmt)).scalars().all()

        return DashboardStatsResponse(
            total_documents=total_docs,
            completed_documents=completed_docs,
            processing_documents=processing_docs,
            failed_documents=failed_docs,
            pending_documents=pending_docs,
            total_chunks=total_chunks,
            total_jobs=total_jobs,
            recent_documents=[DocumentResponse.model_validate(d) for d in recent_docs],
            recent_jobs=[
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
                for j in recent_jobs
            ],
        )
