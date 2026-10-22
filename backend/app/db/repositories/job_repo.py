"""Processing job repository for asynchronous queue management."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models.job import ProcessingJob, JobStatus


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(
        self, document_id: str, job_type: str = "ingestion", max_attempts: int = 3
    ) -> ProcessingJob:
        job = ProcessingJob(
            document_id=document_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            attempt_count=0,
            max_attempts=max_attempts,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        query = (
            select(ProcessingJob)
            .options(selectinload(ProcessingJob.document))
            .where(ProcessingJob.id == job_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[JobStatus] = None,
    ) -> Tuple[List[ProcessingJob], int]:
        query = select(ProcessingJob).options(selectinload(ProcessingJob.document))

        if status:
            query = query.where(ProcessingJob.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        offset = (page - 1) * page_size
        query = query.order_by(desc(ProcessingJob.created_at)).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def claim_next_job(self) -> Optional[ProcessingJob]:
        """
        Atomically claims the next pending job using row locking.
        On PostgreSQL, uses FOR UPDATE SKIP LOCKED.
        On SQLite, performs immediate status transition to prevent race conditions.
        """
        query = (
            select(ProcessingJob)
            .where(
                ProcessingJob.status == JobStatus.PENDING,
                ProcessingJob.attempt_count < ProcessingJob.max_attempts,
            )
            .order_by(ProcessingJob.created_at)
            .limit(1)
        )

        if settings.is_postgres:
            query = query.with_for_update(skip_locked=True)

        result = await self.session.execute(query)
        job = result.scalar_one_or_none()

        if job:
            now = datetime.now(timezone.utc)
            job.status = JobStatus.PROCESSING
            job.started_at = now
            job.heartbeat_at = now
            job.attempt_count += 1
            await self.session.commit()
            await self.session.refresh(job)

        return job

    async def update_heartbeat(self, job_id: str) -> None:
        """Updates job heartbeat to demonstrate worker liveness."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(heartbeat_at=now)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def complete_job(self, job_id: str) -> Optional[ProcessingJob]:
        job = await self.get_by_id(job_id)
        if not job:
            return None
        now = datetime.now(timezone.utc)
        job.status = JobStatus.COMPLETED
        job.finished_at = now
        job.error_message = None
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def fail_job(
        self, job_id: str, error_message: str, can_retry: bool = True
    ) -> Optional[ProcessingJob]:
        job = await self.get_by_id(job_id)
        if not job:
            return None
        now = datetime.now(timezone.utc)
        
        # Determine whether to mark pending for retry or failed permanently
        if can_retry and job.attempt_count < job.max_attempts:
            job.status = JobStatus.PENDING
            job.error_message = f"[Attempt {job.attempt_count}] {error_message}"
        else:
            job.status = JobStatus.FAILED
            job.finished_at = now
            job.error_message = error_message

        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def recover_stale_jobs(self, timeout_seconds: int = 300) -> int:
        """
        Recovers jobs stuck in PROCESSING state without recent heartbeat.
        Resets them to PENDING if attempts remain, or marks them FAILED.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        query = select(ProcessingJob).where(
            ProcessingJob.status == JobStatus.PROCESSING,
            (ProcessingJob.heartbeat_at < cutoff) | (ProcessingJob.heartbeat_at.is_(None)),
        )
        result = await self.session.execute(query)
        stale_jobs = list(result.scalars().all())

        recovered_count = 0
        for job in stale_jobs:
            if job.attempt_count < job.max_attempts:
                job.status = JobStatus.PENDING
                job.error_message = f"Recovered from stalled worker (last heartbeat: {job.heartbeat_at})"
            else:
                job.status = JobStatus.FAILED
                job.finished_at = datetime.now(timezone.utc)
                job.error_message = "Job stalled and reached maximum retry attempts."
            recovered_count += 1

        if recovered_count > 0:
            await self.session.commit()

        return recovered_count
