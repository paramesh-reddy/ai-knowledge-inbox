"""Document service for upload validation, note creation, retry, and deletion."""
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.core.config import settings
from app.core.logging import logger
from app.db.models.document import Document, DocumentStatus, FileType
from app.db.models.chunk import DocumentChunk
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.job_repo import JobRepository


ALLOWED_EXTENSIONS = {
    ".pdf": FileType.PDF,
    ".txt": FileType.TXT,
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
}


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.job_repo = JobRepository(session)

    async def upload_file(self, file: UploadFile) -> Tuple[Document, str]:
        """
        Validates file type and size, writes file securely to storage,
        creates Document record and enqueues a processing job.
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty.",
            )

        # Path traversal protection: extract pure filename
        original_filename = Path(file.filename).name
        ext = Path(original_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(ALLOWED_EXTENSIONS.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {allowed_list}",
            )

        file_type = ALLOWED_EXTENSIONS[ext]
        max_bytes = settings.max_file_size_mb * 1024 * 1024

        # Read content to validate size and write safely
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.max_file_size_mb} MB.",
            )

        # Generate unique storage filename
        safe_id = str(uuid.uuid4())
        safe_filename = f"{safe_id}_{original_filename}"
        storage_path = settings.absolute_upload_dir / safe_filename

        with open(storage_path, "wb") as f:
            f.write(content)

        # Title defaults to filename without extension
        title = Path(original_filename).stem.replace("_", " ").replace("-", " ").title()

        doc = await self.doc_repo.create(
            title=title,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            file_path=str(storage_path),
        )

        job = await self.job_repo.create_job(
            document_id=doc.id,
            job_type="ingestion",
            max_attempts=settings.job_max_retries,
        )

        logger.info(f"Document '{doc.title}' ({doc.id}) uploaded and job '{job.id}' enqueued.")
        return doc, job.id

    async def create_note(self, title: str, content: str) -> Tuple[Document, str]:
        """Creates a text note document and enqueues processing job."""
        clean_content = content.strip()
        if not clean_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note content cannot be empty.",
            )

        clean_title = title.strip() or "Untitled Note"
        file_size = len(clean_content.encode("utf-8"))

        doc = await self.doc_repo.create(
            title=clean_title,
            original_filename=f"{clean_title}.txt",
            file_type=FileType.NOTE,
            file_size=file_size,
            raw_content=clean_content,
        )

        job = await self.job_repo.create_job(
            document_id=doc.id,
            job_type="ingestion",
            max_attempts=settings.job_max_retries,
        )

        logger.info(f"Note '{doc.title}' ({doc.id}) created and job '{job.id}' enqueued.")
        return doc, job.id

    async def retry_document(self, doc_id: str) -> Tuple[Document, str]:
        """Resets document state, removes existing chunks, and enqueues a new job."""
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        # Delete existing chunks to prevent duplicates
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
        )

        doc.processing_status = DocumentStatus.PENDING
        doc.error_message = None
        doc.chunk_count = 0
        await self.session.commit()

        job = await self.job_repo.create_job(
            document_id=doc.id,
            job_type="ingestion",
            max_attempts=settings.job_max_retries,
        )

        logger.info(f"Retrying ingestion for document '{doc.title}' ({doc.id}), new job: {job.id}")
        return doc, job.id

    async def delete_document(self, doc_id: str) -> bool:
        """Deletes document record, cleans up physical file, cascades chunks and jobs."""
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        # Clean up physical file if it exists
        if doc.file_path:
            file_p = Path(doc.file_path)
            try:
                if file_p.exists():
                    file_p.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete physical file {doc.file_path}: {e}")

        await self.doc_repo.delete(doc_id)
        logger.info(f"Document {doc_id} deleted successfully.")
        return True
