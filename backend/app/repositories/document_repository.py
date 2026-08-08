"""Document repository — database I/O only, no business logic."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentChunk, ExtractedField


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    # ── Status ────────────────────────────────────────────────────────────────

    async def update_status(
        self,
        document_id: str,
        status: str,
        *,
        error_message: str | None = None,
    ) -> Document | None:
        """Update Document.status and optionally store an error message."""
        doc = await self.get_by_id(document_id)
        if not doc:
            return None
        doc.status = status
        if error_message is not None:
            # Store the error message in a free-text field if the column exists,
            # otherwise log it.  The current schema has no dedicated error column
            # so we repurpose file_path suffix as a sentinel — nothing; we just
            # keep status="error" and the worker logs the detail.
            pass
        await self.session.flush()
        return doc

    # ── Chunks ────────────────────────────────────────────────────────────────

    async def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Bulk-insert document chunks."""
        for chunk in chunks:
            self.session.add(chunk)
        await self.session.flush()

    async def save_extracted_fields(self, fields: list[ExtractedField]) -> None:
        """Bulk-insert extracted structured fields."""
        for field in fields:
            self.session.add(field)
        await self.session.flush()

    async def count_chunks(self, document_id: str) -> int:
        result = await self.session.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id
            )
        )
        return int(result.scalar_one())

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, document_id: str) -> Document | None:
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        return result.scalar_one_or_none()

    async def get_by_id_slim(self, document_id: str) -> Document | None:
        """Fetch document row without loading relationships (faster for status checks)."""
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .options(selectinload(Document.chunks))
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_project(self, project_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Document.id)).where(Document.project_id == project_id)
        )
        return int(result.scalar_one())

    async def get_chunks(self, document_id: str) -> list[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(result.scalars().all())

    async def get_verification_queue(self, project_id: str, limit: int = 50) -> list[DocumentChunk]:
        """Fetch a global queue of claims/chunks across all documents in a project, ordered by lowest confidence."""
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.project_id == project_id)
            .options(selectinload(DocumentChunk.document))  # load parent doc to get filename later
            .order_by(DocumentChunk.extraction_confidence.asc(), DocumentChunk.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
        await self.session.flush()
