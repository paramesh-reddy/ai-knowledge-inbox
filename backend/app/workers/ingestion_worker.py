"""Asynchronous Ingestion Worker process for background document processing."""
import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal, init_db
from app.db.models.document import Document, DocumentStatus, FileType
from app.db.models.chunk import DocumentChunk
from app.db.models.job import ProcessingJob, JobStatus
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.document_repo import DocumentRepository
from app.services.extraction_service import ExtractionService, ExtractionError
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService


class IngestionWorker:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory or AsyncSessionLocal
        self.is_running = True
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self._stale_check_counter = 0

    def stop(self) -> None:
        logger.info("Stopping Ingestion Worker gracefully...")
        self.is_running = False

    async def run(self) -> None:
        """Main worker loop: polls and processes pending jobs."""
        logger.info("Ingestion Worker started. Listening for background jobs...")
        await init_db()

        while self.is_running:
            try:
                # Periodic stale job recovery (every 10 loop iterations)
                self._stale_check_counter += 1
                if self._stale_check_counter >= 10:
                    self._stale_check_counter = 0
                    await self._recover_stale_jobs()

                job_processed = await self._process_next_job()
                if not job_processed:
                    # Sleep before next poll
                    await asyncio.sleep(settings.job_poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(settings.job_poll_interval_seconds)

        logger.info("Ingestion Worker shutdown complete.")

    async def _recover_stale_jobs(self) -> None:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            recovered = await job_repo.recover_stale_jobs(
                timeout_seconds=settings.job_stale_timeout_seconds
            )
            if recovered > 0:
                logger.warning(f"Worker recovered {recovered} stale jobs.")

    async def _process_next_job(self) -> bool:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            doc_repo = DocumentRepository(session)

            job = await job_repo.claim_next_job()
            if not job:
                return False

            logger.info(
                f"Claimed job {job.id} for document {job.document_id} (Attempt {job.attempt_count}/{job.max_attempts})"
            )

            # Update document to PROCESSING
            await doc_repo.update_status(job.document_id, DocumentStatus.PROCESSING)

        # Process the job outside the claim transaction
        await self._execute_ingestion(job.id, job.document_id)
        return True

    async def _execute_ingestion(self, job_id: str, document_id: str) -> None:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            doc_repo = DocumentRepository(session)

            doc = await doc_repo.get_by_id(document_id)
            if not doc:
                logger.error(f"Document {document_id} does not exist for job {job_id}.")
                await job_repo.fail_job(job_id, "Document record not found.", can_retry=False)
                return

            try:
                # 1. Heartbeat
                await job_repo.update_heartbeat(job_id)

                # 2. Extract text
                if doc.file_type == FileType.NOTE:
                    pages = ExtractionService.extract_from_text(doc.raw_content or "")
                else:
                    if not doc.file_path:
                        raise ExtractionError("Missing document file path.")
                    pages = ExtractionService.extract_from_file(Path(doc.file_path), doc.file_type)

                # 3. Heartbeat
                await job_repo.update_heartbeat(job_id)

                # 4. Chunk text
                chunks = self.chunking_service.chunk_extracted_pages(pages)
                if not chunks:
                    raise ExtractionError("Document produced 0 text chunks.")

                logger.info(f"Document '{doc.title}' yielded {len(chunks)} text chunks.")

                # 5. Heartbeat
                await job_repo.update_heartbeat(job_id)

                # 6. Generate embeddings (in batches of 20 to avoid payload limits)
                chunk_texts = [c.text for c in chunks]
                embeddings = []
                batch_size = 20
                for i in range(0, len(chunk_texts), batch_size):
                    batch = chunk_texts[i : i + batch_size]
                    batch_embeddings = self.embedding_service.embed_batch(batch)
                    embeddings.extend(batch_embeddings)
                    await job_repo.update_heartbeat(job_id)

                # 7. Persist chunks in transaction
                # Clear any existing chunks to avoid duplication
                from sqlalchemy import delete
                await session.execute(
                    delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
                )

                for chunk_obj, emb_vec in zip(chunks, embeddings):
                    chunk_entity = DocumentChunk(
                        document_id=document_id,
                        chunk_index=chunk_obj.chunk_index,
                        extracted_text=chunk_obj.text,
                        page_number=chunk_obj.page_number,
                    )
                    chunk_entity.embedding = emb_vec
                    session.add(chunk_entity)

                # 8. Mark document completed
                await doc_repo.update_status(
                    document_id,
                    DocumentStatus.COMPLETED,
                    chunk_count=len(chunks),
                )

                # 9. Mark job completed
                await job_repo.complete_job(job_id)
                logger.info(f"Successfully processed document '{doc.title}' ({document_id}).")

            except ExtractionError as e:
                error_msg = str(e)
                logger.warning(f"Extraction error for document {document_id}: {error_msg}")
                await doc_repo.update_status(document_id, DocumentStatus.FAILED, error_message=error_msg)
                await job_repo.fail_job(job_id, error_msg, can_retry=False)

            except Exception as e:
                error_msg = f"Processing error: {str(e)}"
                logger.error(f"Failed processing document {document_id}: {error_msg}", exc_info=True)
                await doc_repo.update_status(document_id, DocumentStatus.FAILED, error_message=error_msg)
                await job_repo.fail_job(job_id, error_msg, can_retry=True)


async def main():
    worker = IngestionWorker()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            pass  # Signal handlers may not be supported on all platforms (e.g. Windows)

    try:
        await worker.run()
    except Exception as e:
        logger.critical(f"Worker crashed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
