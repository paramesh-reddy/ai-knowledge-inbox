"""Vector retrieval service for cosine similarity search over chunks."""
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models.document import Document, DocumentStatus
from app.db.models.chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    chunk_index: int
    page_number: Optional[int]
    text: str
    similarity_score: float


class RetrievalService:
    def __init__(self, session: AsyncSession, embedding_service: Optional[EmbeddingService] = None):
        self.session = session
        self.embedding_service = embedding_service or EmbeddingService()

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """
        Embeds the query string and performs vector similarity search across all completed documents.
        """
        k = top_k or settings.retrieval_top_k
        threshold = min_score if min_score is not None else settings.retrieval_min_score

        query_vec = self.embedding_service.embed_text(query)
        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm == 0:
            return []

        # Query all chunks from completed documents
        stmt = (
            select(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.processing_status == DocumentStatus.COMPLETED)
            .options(selectinload(DocumentChunk.document))
        )
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())

        if not chunks:
            return []

        scored_chunks: List[RetrievedChunk] = []
        for chk in chunks:
            emb = chk.embedding
            if not emb:
                continue

            emb_arr = np.array(emb, dtype=np.float32)
            denom = q_norm * np.linalg.norm(emb_arr)
            score = float(np.dot(q_arr, emb_arr) / denom) if denom > 0 else 0.0

            if score >= threshold:
                doc_title = chk.document.title if chk.document else "Untitled Document"
                scored_chunks.append(
                    RetrievedChunk(
                        chunk_id=chk.id,
                        document_id=chk.document_id,
                        document_title=doc_title,
                        chunk_index=chk.chunk_index,
                        page_number=chk.page_number,
                        text=chk.extracted_text,
                        similarity_score=round(score, 4),
                    )
                )

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_chunks[:k]
