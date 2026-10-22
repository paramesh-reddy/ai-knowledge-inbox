"""Document Pydantic schemas."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.db.models.document import DocumentStatus, FileType


class CreateNoteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: str = Field(..., min_length=1, description="Raw text content of the note")


class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    extracted_text: str
    page_number: Optional[int] = None
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    file_type: FileType
    file_size: int
    processing_status: DocumentStatus
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    raw_content_preview: Optional[str] = None
    chunks: List[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
