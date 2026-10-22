"""FastAPI dependency injection utilities."""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.chat_repo import ChatRepository
from app.services.document_service import DocumentService
from app.services.job_service import JobService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.rag_service import RAGService


def get_document_repo(session: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(session)


def get_job_repo(session: AsyncSession = Depends(get_db)) -> JobRepository:
    return JobRepository(session)


def get_chat_repo(session: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(session)


def get_document_service(session: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(session)


def get_job_service(session: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(session)


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_retrieval_service(
    session: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    return RetrievalService(session, embedding_service)


def get_rag_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> RAGService:
    return RAGService(retrieval_service)
