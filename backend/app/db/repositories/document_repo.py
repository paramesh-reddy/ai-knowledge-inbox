"""Document repository for database operations."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import Document, DocumentStatus, FileType
from app.db.models.chunk import DocumentChunk


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        title: str,
        original_filename: str,
        file_type: FileType,
        file_size: int,
        file_path: Optional[str] = None,
        raw_content: Optional[str] = None,
    ) -> Document:
        doc = Document(
            title=title,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            raw_content=raw_content,
            processing_status=DocumentStatus.PENDING,
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: str, load_chunks: bool = False) -> Optional[Document]:
        query = select(Document).where(Document.id == doc_id)
        if load_chunks:
            query = query.options(selectinload(Document.chunks))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        file_type: Optional[FileType] = None,
        status: Optional[DocumentStatus] = None,
    ) -> Tuple[List[Document], int]:
        query = select(Document)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(Document.title.ilike(term), Document.original_filename.ilike(term))
            )

        if file_type:
            query = query.where(Document.file_type == file_type)

        if status:
            query = query.where(Document.processing_status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(desc(Document.created_at)).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        doc = await self.get_by_id(doc_id)
        if not doc:
            return None

        doc.processing_status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message
        elif status == DocumentStatus.COMPLETED:
            doc.error_message = None

        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def delete(self, doc_id: str) -> bool:
        doc = await self.get_by_id(doc_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.commit()
        return True
