"""Document database model."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from sqlalchemy import String, Integer, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "md"
    NOTE = "note"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        SAEnum(FileType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0)

    processing_status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, values_callable=lambda x: [e.value for e in x]),
        default=DocumentStatus.PENDING,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )
    jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(ProcessingJob.created_at)",
    )
