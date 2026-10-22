"""Chat Pydantic schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CitationItem(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    excerpt: str
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="User question")
    session_id: Optional[str] = Field(None, description="Optional existing chat session ID")
    top_k: Optional[int] = Field(None, ge=1, le=10, description="Override top K retrieval")


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    citations: List[CitationItem] = []
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    message_count: int = 0


class AskQuestionResponse(BaseModel):
    session_id: str
    user_message_id: str
    assistant_message_id: str
    answer: str
    citations: List[CitationItem] = []
    has_evidence: bool = True
