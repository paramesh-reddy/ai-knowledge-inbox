"""Tests for job queue, claiming, and worker ingestion execution."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.document import DocumentStatus, FileType
from app.db.models.job import JobStatus
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository
from app.workers.ingestion_worker import IngestionWorker


@pytest.mark.asyncio
async def test_job_creation_and_atomic_claim(db_session: AsyncSession):
    doc_repo = DocumentRepository(db_session)
    job_repo = JobRepository(db_session)

    # 1. Create document & job
    doc = await doc_repo.create(
        title="Test Doc",
        original_filename="test.txt",
        file_type=FileType.NOTE,
        file_size=100,
        raw_content="Content inside test document.",
    )
    job = await job_repo.create_job(document_id=doc.id)
    assert job.status == JobStatus.PENDING
    assert job.attempt_count == 0

    # 2. Claim next job
    claimed = await job_repo.claim_next_job()
    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.status == JobStatus.PROCESSING
    assert claimed.attempt_count == 1
    assert claimed.started_at is not None

    # 3. Next claim returns None (no pending jobs left)
    second_claim = await job_repo.claim_next_job()
    assert second_claim is None


@pytest.mark.asyncio
async def test_ingestion_worker_processes_note(test_env, db_session: AsyncSession):
    doc_repo = DocumentRepository(db_session)
    job_repo = JobRepository(db_session)

    # Create note
    doc = await doc_repo.create(
        title="Knowledge on Distributed Systems",
        original_filename="note.txt",
        file_type=FileType.NOTE,
        file_size=80,
        raw_content="Raft consensus and Paxos algorithms guarantee consistency in distributed state machines.",
    )
    job = await job_repo.create_job(document_id=doc.id)

    worker = IngestionWorker(session_factory=test_env["session_maker"])
    # Execute single job ingestion
    await worker._execute_ingestion(job.id, doc.id)

    # Verify document and job transitioned to completed using fresh session
    async with test_env["session_maker"]() as verify_session:
        verify_doc_repo = DocumentRepository(verify_session)
        verify_job_repo = JobRepository(verify_session)

        updated_doc = await verify_doc_repo.get_by_id(doc.id, load_chunks=True)
        assert updated_doc.processing_status == DocumentStatus.COMPLETED
        assert updated_doc.chunk_count > 0
        assert len(updated_doc.chunks) > 0
        assert "Raft consensus" in updated_doc.chunks[0].extracted_text

        updated_job = await verify_job_repo.get_by_id(job.id)
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.finished_at is not None
