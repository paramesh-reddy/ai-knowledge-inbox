"""Chat session and message database models."""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationship
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    @property
    def citations(self) -> List[Dict[str, Any]]:
        if not self.citations_json:
            return []
        try:
            return json.loads(self.citations_json)
        except Exception:
            return []

    @citations.setter
    def citations(self, items: List[Dict[str, Any]]) -> None:
        self.citations_json = json.dumps(items)
