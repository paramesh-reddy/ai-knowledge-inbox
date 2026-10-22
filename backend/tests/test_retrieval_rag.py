"""Tests for vector retrieval, grounding prompt, citations, and no-evidence fallback."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.document import DocumentStatus, FileType
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository
from app.workers.ingestion_worker import IngestionWorker


@pytest.mark.asyncio
async def test_no_evidence_fallback_when_empty_knowledge_base(client: AsyncClient):
    response = await client.post(
        "/api/chat/ask",
        json={"question": "What is the secret recipe for quantum cold brew?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_evidence"] is False
    assert len(data["citations"]) == 0
    assert "could not find enough relevant evidence" in data["answer"].lower()


@pytest.mark.asyncio
async def test_rag_retrieval_with_grounded_citation(test_env, db_session: AsyncSession, client: AsyncClient):
    # 1. Ingest a document
    doc_repo = DocumentRepository(db_session)
    job_repo = JobRepository(db_session)

    doc = await doc_repo.create(
        title="Project Apollo Guidelines",
        original_filename="apollo.txt",
        file_type=FileType.NOTE,
        file_size=150,
        raw_content="Project Apollo requires a strict 99.99% uptime SLA and all deployments must pass canary checks.",
    )
    job = await job_repo.create_job(document_id=doc.id)

    worker = IngestionWorker(session_factory=test_env["session_maker"])
    await worker._execute_ingestion(job.id, doc.id)

    # 2. Ask question matching document
    response = await client.post(
        "/api/chat/ask",
        json={"question": "What uptime SLA does Project Apollo require?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_evidence"] is True
    assert len(data["citations"]) > 0

    citation = data["citations"][0]
    assert citation["document_title"] == "Project Apollo Guidelines"
    assert citation["document_id"] == doc.id
    assert "99.99%" in citation["excerpt"]
