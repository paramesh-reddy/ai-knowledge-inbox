"""Document Chunk database model."""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Serialized vector representation for maximum portability across Postgres and SQLite
    embedding_json: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 1-indexed page number if extracted from a paged document (e.g. PDF)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    @property
    def embedding(self) -> List[float]:
        try:
            return json.loads(self.embedding_json)
        except Exception:
            return []

    @embedding.setter
    def embedding(self, vec: List[float]) -> None:
        self.embedding_json = json.dumps(vec)
