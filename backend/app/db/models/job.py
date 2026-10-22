"""Processing Job database model."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(String(50), default="ingestion")
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.PENDING,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    document: Mapped["Document"] = relationship("Document", back_populates="jobs")
