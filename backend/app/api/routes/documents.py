"""Documents API endpoints."""
import math
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_document_repo, get_document_service
from app.db.models.document import DocumentStatus, FileType
from app.db.repositories.document_repo import DocumentRepository
from app.db.schemas.document import (
    CreateNoteRequest,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentChunkResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query in title or filename"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by processing status"),
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    """Lists knowledge documents with pagination, keyword search, and filters."""
    items, total = await doc_repo.list_documents(
        page=page,
        page_size=page_size,
        search=search,
        file_type=file_type,
        status=status,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    doc_service: DocumentService = Depends(get_document_service),
):
    """
    Uploads a PDF, TXT, or Markdown document.
    Saves the file securely, creates a Document entity, and asynchronously enqueues ingestion.
    """
    doc, _ = await doc_service.upload_file(file)
    return DocumentResponse.model_validate(doc)


@router.post("/notes", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_note(
    payload: CreateNoteRequest,
    doc_service: DocumentService = Depends(get_document_service),
):
    """Creates a raw text note and queues it for background chunking and embedding."""
    doc, _ = await doc_service.create_note(title=payload.title, content=payload.content)
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    """Retrieves document metadata along with all generated chunks."""
    doc = await doc_repo.get_by_id(document_id, load_chunks=True)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    # Preview of raw content if available
    preview = None
    if doc.raw_content:
        preview = doc.raw_content[:2000]
    elif doc.file_path and Path(doc.file_path).exists() and doc.file_type in (FileType.TXT, FileType.MARKDOWN):
        try:
            with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
                preview = f.read(2000)
        except Exception:
            pass

    return DocumentDetailResponse(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        processing_status=doc.processing_status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        raw_content_preview=preview,
        chunks=[
            DocumentChunkResponse(
                id=c.id,
                chunk_index=c.chunk_index,
                extracted_text=c.extracted_text,
                page_number=c.page_number,
                created_at=c.created_at,
            )
            for c in doc.chunks
        ],
    )


@router.get("/{document_id}/content", response_class=PlainTextResponse)
async def get_document_raw_content(
    document_id: str,
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    """Returns the full plain text or extracted content of a document."""
    doc = await doc_repo.get_by_id(document_id, load_chunks=True)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.raw_content:
        return doc.raw_content

    if doc.chunks:
        return "\n\n--- Chunk ---\n\n".join(c.extracted_text for c in doc.chunks)

    if doc.file_path and Path(doc.file_path).exists():
        try:
            with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            pass

    return "No content available."


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_document_service),
):
    """Deletes a document, associated physical file, chunks, and job records."""
    await doc_service.delete_document(document_id)
    return {"message": "Document deleted successfully.", "document_id": document_id}


@router.post("/{document_id}/retry", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_document_service),
):
    """Re-enqueues a document for processing after failure."""
    doc, _ = await doc_service.retry_document(document_id)
    return DocumentResponse.model_validate(doc)
